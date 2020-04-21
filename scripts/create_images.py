#!/usr/bin/env python3

from datetime import datetime, timedelta
import urllib.parse
import requests
import os
from pytz import timezone, utc
import boto3
s3_client = boto3.client('s3')

baseurl = 'https://api.octopus.energy/'
qcurl = 'https://quickchart.io/chart'
agile_code = 'AGILE-18-02-21'
images_dir = '/tmp/images/'
if not os.path.exists(images_dir):
	os.mkdir(images_dir)
end_of_data_file = '/tmp/end_of_data.txt'


def get_end_of_data_file():
	s3_client.download_file('smartathome.co.uk', 'octopus/scripts/end_of_data.txt', end_of_data_file)


def put_end_of_data_file():
	s3_client.upload_file(end_of_data_file, 'smartathome.co.uk', 'octopus/scripts/end_of_data.txt')


def upload_images():
	for i in os.listdir(images_dir):
		s3_client.upload_file(images_dir+'/'+i, 'smartathome.co.uk', 'octopus/images/'+i)


def create_config(dataSets, startdate, enddate):
	startTimeStr = startdate.strftime('%A %-d %B %Y')
	endTimeStr = enddate.strftime('%A %-d %B %Y')
	if startTimeStr != endTimeStr:
		startTimeStr = startdate.strftime('%a %-d') + ' - ' + enddate.strftime('%a %-d %B %Y')
	config = {
		'type': 'bar',
		'data': { 'datasets': dataSets },
		'options': {
			'title': {
				'display': True,
				'text': 'Agile Prices for '+startTimeStr
			},
			'legend': {
				'position': 'bottom',
				'labels': { 'fontSize': 18, 'usePointStyle': True }
			},
			'scales': {
				'xAxes': [{
					'type': 'time',
				}],
				'yAxes': [{
					'scaleLabel': { 'display': True, 'labelString': 'Price (p/kWh)' }
				}]
			}
		}
	}
	return config


def create_datasets(gsp, dataPoints):
	datasets = [{
		'type': 'line',
		'pointStyle':'line',
		'backgroundColor':'#00ff00',
		'borderColor':'#00ff00',
		'label':'Agile Price ('+gsp+')',
		'fill':False,
		'steppedLine':'before',
		'data':dataPoints
	}]
	return datasets


def do_post(config):
	data = {
		"backgroundColor": "white",
		"width": 900,
		"height": 500,
		"format": "png",
		"chart": config,
	}
	r = requests.post(qcurl, json = data)
	return r


def get_account_details(auth, account_no):
	r = requests.get(baseurl+'/v1/accounts/'+account_no, auth=auth)
	return r.json()['properties'][0]


def get_unit_rates(code, gsp, startdate, enddate):
	tariff_code = get_tariff_code(code, gsp)
	results = []
	params = {}
	params['period_from'] = datetime.strftime(startdate,'%Y-%m-%dT%H:%M:%S')
	params['period_to'] = datetime.strftime(enddate,'%Y-%m-%dT%H:%M:%S')
	r = requests.get(baseurl+'/v1/products/'+code+'/electricity-tariffs/'+tariff_code+'/standard-unit-rates/', params=params)
	results += r.json()['results']
	while r.json()['next'] is not None:
		r = requests.get(r.json()['next'], params=params)
		results += r.json()['results']
	sorted_results = sorted(results, key=lambda k: k['valid_from'])
	return sorted_results


def get_tariff_code(code, gsp):
#	r = requests.get(baseurl+'/v1/products/'+code)
#	return r.json()['single_register_electricity_tariffs'][gsp]['direct_debit_monthly']['code']
	return 'E-1R-'+code+'-'+gsp[1]

def get_gsps():
	return ['_P', '_E', '_M', '_G', '_L', '_C', '_K', '_D', '_J', '_A', '_H', '_N', '_B', '_F']


def create_datapoints(sorted_rates, add_extra_point_at_end=True):
	datapoints = []
	for i in sorted_rates:
		valid_from = datetime.strptime(i['valid_from'], '%Y-%m-%dT%H:%M:%SZ')
		utc_from = valid_from.replace(tzinfo=utc)
		london_from = utc_from.astimezone(timezone('Europe/London'))
		london_strf = london_from.strftime('%Y-%m-%dT%H:%M:%S')
		datapoints.append({'x':london_strf, 'y':i['value_inc_vat']})
	if add_extra_point_at_end:
		london_from = london_from + timedelta(minutes=30)
		london_strf = london_from.strftime('%Y-%m-%dT%H:%M:%S')
		datapoints.append({'x':london_strf, 'y':i['value_inc_vat']})
	return datapoints


def lambda_handler(event, context):
	startdate = datetime.now().astimezone(timezone('Europe/London'))
	startdate = startdate.replace(minute=0, second=0, microsecond=0)
	if startdate.hour < 16:
		startdate = startdate.replace(hour=0)
		enddate = datetime.now().astimezone(timezone('Europe/London'))
	else:
		enddate = datetime.now().astimezone(timezone('Europe/London')) + timedelta(days=1)
	enddate = enddate.replace(hour=23, minute=0, second=0, microsecond=0)
	rates = {}
	for gsp in get_gsps():
		rates[gsp[1]] = get_unit_rates(agile_code, gsp, startdate, enddate)
	end_of_data = rates['P'][-1]['valid_to']
	get_end_of_data_file()
	with open(end_of_data_file, 'r',) as f:
		prev_end_of_data = f.read().strip()
	if end_of_data != prev_end_of_data or datetime.now().astimezone(timezone('Europe/London')).strftime('%H%M') == '0000':
		with open(end_of_data_file, 'w') as f:
			f.write(end_of_data)
		put_end_of_data_file()
		for gsp in rates:
			agileDataPoints = create_datapoints(rates[gsp])
			datasets = create_datasets(gsp, agileDataPoints)
			config = create_config(datasets, startdate, enddate)
			r = do_post(config)
			with open(images_dir+gsp+'.png', 'wb') as f:
				f.write(r.content)
		av_rates = []
		for dp in rates['P']:
			all_rates = []
			dpt = dp['valid_from']
			for gsp in rates:
				for i in rates[gsp]:
					if i['valid_from'] == dpt:
						all_rates.append(i['value_inc_vat'])
			av_rate = sum(all_rates) / len(all_rates)
			av_rates.append({'valid_from': dpt, 'value_inc_vat': av_rate})
		agileDataPoints = create_datapoints(av_rates)
		datasets = create_datasets('average', agileDataPoints)
		config = create_config(datasets, startdate, enddate)
		r = do_post(config)
		with open(images_dir+'average.png', 'wb') as f:
			f.write(r.content)
		upload_images()


if __name__ =='__main__':
	lambda_handler(None, None)
