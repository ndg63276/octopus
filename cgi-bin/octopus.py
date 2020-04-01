#!/usr/bin/env python3

from datetime import datetime, timedelta
import urllib.parse
import requests
import os
import pytz
from pytz import timezone

baseurl = 'https://api.octopus.energy/'
qcurl = 'https://quickchart.io/chart'
agile_code = 'AGILE-18-02-21'
dir = os.path.dirname(os.path.realpath(__file__))+'/../images/'
if not os.path.exists(dir):
	os.mkdir(dir)

def create_config(dataSets, startdate):
	timeStr = startdate.strftime('%A %-d %B %Y')
	config = {
		'type': 'bar',
		'data': { 'datasets': dataSets },
		'options': {
			'title': {
				'display': True,
				'text': 'Agile Prices for '+timeStr
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
	return results


def get_tariff_code(code, gsp):
#	r = requests.get(baseurl+'/v1/products/'+code)
#	return r.json()['single_register_electricity_tariffs'][gsp]['direct_debit_monthly']['code']
	return 'E-1R-'+code+'-'+gsp[1]

def get_gsps():
	return ['_P', '_E', '_M', '_G', '_L', '_C', '_K', '_D', '_J', '_A', '_H', '_N', '_B', '_F']


def create_datapoints(unsorted_rates, add_extra_point_at_end=True):
	datapoints = []
	sorted_rates = sorted(unsorted_rates, key=lambda k: k['valid_from'])
	for i in sorted_rates:
		valid_from = datetime.strptime(i['valid_from'], '%Y-%m-%dT%H:%M:%SZ')
		utc_from = valid_from.replace(tzinfo=pytz.utc)
		london_from = utc_from.astimezone(timezone('Europe/London'))
		london_strf = london_from.strftime('%Y-%m-%dT%H:%M:%S')
		datapoints.append({'x':london_strf, 'y':i['value_inc_vat']})
	if add_extra_point_at_end:
		london_from = london_from + timedelta(minutes=30)
		london_strf = london_from.strftime('%Y-%m-%dT%H:%M:%S')
		datapoints.append({'x':london_strf, 'y':i['value_inc_vat']})
	return datapoints


if __name__ == '__main__':
	startdate = datetime.now() + timedelta(days=1)
	startdate = startdate.replace(hour=0, minute=0, second=0, microsecond=0)
	enddate = startdate.replace(hour=23, minute=0, second=0, microsecond=0)
	rates = {}
	for gsp in get_gsps():
		rates[gsp[1]] = get_unit_rates(agile_code, gsp, startdate, enddate)
	for gsp in rates:
		agileDataPoints = create_datapoints(rates[gsp])
		datasets = create_datasets(gsp, agileDataPoints)
		config = create_config(datasets, startdate)
		r = do_post(config)
		with open(dir+gsp+'.png', 'wb') as f:
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
	config = create_config(datasets, startdate)
	r = do_post(config)
	with open(dir+'average.png', 'wb') as f:
		f.write(r.content)
