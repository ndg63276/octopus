#!/usr/bin/env python3

from datetime import datetime, timedelta
import urllib.parse
import requests

baseurl = 'https://api.octopus.energy/'
qcurl = 'https://quickchart.io/chart'
agile_code = 'AGILE-18-02-21'

def create_config(dataSets):
	config = {
		'type': 'bar',
		'data': { 'datasets': dataSets },
		'options': {
			'title': { 'display': False },
			'legend': {
				'display': True,
				'position': 'bottom',
				'labels': { 'fontSize': 18, 'usePointStyle': True }
			},
			'scales': {
				'xAxes': [{
					'type': 'time',
					'display': True,
					'scaleLabel': { 'display': False }
				}],
				'yAxes': [{
					'id': 'left',
					'display': True,
					'position': 'left',
					'type': 'linear',
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
		'steppedLine':True,
		'yAxisID':'left',
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


def get_unit_rates(code, gsp, startdate=None, enddate=None):
	tariff_code = get_tariff_code(code, gsp)
	results = []
	params = {}
	if startdate is not None:
		params['period_from'] = datetime.strftime(startdate,'%Y-%m-%dT%H:%M:%S')
		if enddate is not None:
			params['period_to'] = datetime.strftime(enddate,'%Y-%m-%dT%H:%M:%S')
	r = requests.get(baseurl+'/v1/products/'+code+'/electricity-tariffs/'+tariff_code+'/standard-unit-rates/', params=params)
	results += r.json()['results']
	while r.json()['next'] is not None:
		r = requests.get(r.json()['next'], params=params)
		results += r.json()['results']
	return results


def get_tariff_code(code, gsp):
	r = requests.get(baseurl+'/v1/products/'+code)
	return r.json()['single_register_electricity_tariffs'][gsp]['direct_debit_monthly']['code']


def get_gsps():
	return ['_P', '_E', '_M', '_G', '_L', '_C', '_K', '_D', '_J', '_A', '_H', '_N', '_B', '_F']


if __name__ == '__main__':
	startdate = datetime.now()
	enddate = startdate + timedelta(days=1)
	rates = {}
	for gsp in get_gsps():
		rates[gsp[1]] = get_unit_rates(agile_code, gsp, startdate, enddate)
	for gsp in rates:
		agileDataPoints = []
		print(gsp)
		for i in rates[gsp]:
			agileDataPoints.append({'x':i['valid_from'], 'y':i['value_inc_vat']});
		datasets = create_datasets(gsp, agileDataPoints)
		config = create_config(datasets)
		r = do_post(config)
		with open('images/'+gsp+'.png', 'wb') as f:
			f.write(r.content)
	agileDataPoints = []
	for dp in rates['P']:
		all_rates = []
		dpt = dp['valid_from']
		for gsp in rates:
			for i in rates[gsp]:
				if i['valid_from'] == dpt:
					all_rates.append(i['value_inc_vat'])
		av_rate = sum(all_rates) / len(all_rates)
		agileDataPoints.append({'x':dp['valid_from'], 'y':av_rate});
	datasets = create_datasets('all', agileDataPoints)
	config = create_config(datasets)
	r = do_post(config)
	with open('images/all.png', 'wb') as f:
		f.write(r.content)
	
