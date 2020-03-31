#!/usr/bin/env python3

import urllib.parse
import requests

qcurl = 'https://quickchart.io/chart?w=800&h=500&bkg=white&c='


def test():
	config = {'type':'bar','data':{'labels':['January','February','March','April', 'May'], 'datasets':[{'label':'Dogs','data':[50,60,70,180,190]},{'label':'Cats','data':[100,200,300,400,500]}]}}

	u = qcurl + urllib.parse.quote(str(config))

	r = requests.get(u)
	with open('test.png', 'wb') as f:
		f.write(r.content)



agile_code = 'AGILE-18-02-21'

from datetime import datetime, timedelta

baseurl = 'https://api.octopus.energy/'

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
	return ['_P'] #, '_E', '_M', '_G', '_L', '_C', '_K', '_D', '_J', '_A', '_H', '_N', '_B', '_F']


if __name__ == '__main__':
	startdate = datetime.now()
	enddate = startdate + timedelta(days=1)
	rates = {}
	for gsp in get_gsps():
		rates[gsp] = get_unit_rates(agile_code, gsp, startdate, enddate)
	print(rates)
	
