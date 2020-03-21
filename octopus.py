#!/usr/bin/env python

from credentials import apikey, account_no
go_code = 'GO-4H-0030'
agile_code = 'AGILE-18-02-21'

import requests
from datetime import datetime, timedelta

auth = (apikey, None)
baseurl = 'https://api.octopus.energy/'

def get_account_details(auth, account_no):
	r = requests.get(baseurl+'/v1/accounts/'+account_no, auth=auth)
	return r.json()['properties'][0]


def get_standing_charges(auth, code, gsp, startdate=None, enddate=None):
	tariff_code = get_tariff_code(auth, code, gsp)
	params = {}
	if startdate is not None:
		params['period_from'] = datetime.strftime(startdate,'%Y-%m-%dT%H:%M:%S')
		if enddate is not None:
			params['period_to'] = datetime.strftime(enddate,'%Y-%m-%dT%H:%M:%S')
	r = requests.get(baseurl+'/v1/products/'+code+'/electricity-tariffs/'+tariff_code+'/standing-charges/', auth=auth, params=params)
	return r.json()['results']


def get_unit_rates(auth, code, gsp, startdate=None, enddate=None):
	tariff_code = get_tariff_code(auth, code, gsp)
	results = []
	params = {}
	if startdate is not None:
		params['period_from'] = datetime.strftime(startdate,'%Y-%m-%dT%H:%M:%S')
		if enddate is not None:
			params['period_to'] = datetime.strftime(enddate,'%Y-%m-%dT%H:%M:%S')
	r = requests.get(baseurl+'/v1/products/'+code+'/electricity-tariffs/'+tariff_code+'/standard-unit-rates/', auth=auth, params=params)
	results += r.json()['results']
	while r.json()['next'] is not None:
		r = requests.get(r.json()['next'], auth=auth, params=params)
		results += r.json()['results']
	return results


def get_consumption(auth, mpan, serial, startdate=None, enddate=None):
	results = []
	params = {}
	if startdate is not None:
		params['period_from'] = datetime.strftime(startdate,'%Y-%m-%dT%H:%M:%S')
		if enddate is not None:
			params['period_to'] = datetime.strftime(enddate,'%Y-%m-%dT%H:%M:%S')
	r = requests.get(baseurl+'/v1/electricity-meter-points/'+mpan+'/meters/'+serial+'/consumption/', auth=auth, params=params)
	results += r.json()['results']
	while r.json()['next'] is not None:
		r = requests.get(r.json()['next'], auth=auth, params=params)
		results += r.json()['results']
	return results


def get_product(auth, code):
	r = requests.get(baseurl+'/v1/products/'+code, auth=auth)
	return r.json()


def get_tariff_code(auth, code, gsp):
	product = get_product(auth, code)
	return product['single_register_electricity_tariffs'][gsp]['direct_debit_monthly']['code']


def get_gsp(auth, postcode):
	params = {'postcode': postcode}
	r = requests.get(baseurl+'/v1/industry/grid-supply-points/', params=params, auth=auth)
	return r.json()['results'][0]['group_id']


def get_products(auth):
	r = requests.get(baseurl+'/v1/products/', auth=auth)
	return r.json()['results']


def get_brands(auth):
	brands = []
	products = get_products(auth)
	for product in products:
		if product['brand'] not in brands:
			brands.append(product['brand'])
	return brands


def get_brand_products(auth, brand):
	brand_products = []
	products = get_products(auth)
	for product in products:
		if product['brand'] == brand and product not in brand_products:
			brand_products.append(product)
	return brand_products


def get_data(auth, code, startdate, enddate):
	account_details = get_account_details(auth, account_no)
	mpan = account_details['electricity_meter_points'][0]['mpan']
	serial = account_details['electricity_meter_points'][0]['meters'][-1]['serial_number']
	postcode = account_details['postcode']
	gsp = get_gsp(auth, postcode)
	unit_rates = get_unit_rates(auth, code, gsp, startdate, enddate)
	standing_charges = get_standing_charges(auth, code, gsp, startdate, enddate)
	consumption = get_consumption(auth, mpan, serial, startdate, enddate)
	loopdate = startdate
	data = {}
	i = 0
	while loopdate < enddate:
		data[i] = {'start': loopdate}
		for period in consumption:
			if datetime.strptime(period['interval_start'], '%Y-%m-%dT%H:%M:%SZ') == loopdate:
				data[i]['usage'] = period['consumption']
				break
		for charge in standing_charges:
			valid_from = datetime.strptime(charge['valid_from'], '%Y-%m-%dT%H:%M:%SZ')
			if charge['valid_to']:
				valid_to = datetime.strptime(charge['valid_to'], '%Y-%m-%dT%H:%M:%SZ')
			else:
				valid_to = enddate
			if loopdate >= valid_from and loopdate < valid_to:
				data[i]['standing_charge'] = charge['value_inc_vat']/48
				break
		for rate in unit_rates:
			valid_from = datetime.strptime(rate['valid_from'], '%Y-%m-%dT%H:%M:%SZ')
			if rate['valid_to']:
				valid_to = datetime.strptime(rate['valid_to'], '%Y-%m-%dT%H:%M:%SZ')
			else:
				valid_to = enddate
			if loopdate >= valid_from and loopdate < valid_to:
				data[i]['rate'] = rate['value_inc_vat']
				break
		loopdate = loopdate + timedelta(minutes=30)
		i += 1
	return data

def get_cost(start, code):
	startdate = datetime.strptime(start, '%Y%m%d')
	enddate = startdate + timedelta(days=1)
	data = get_data(auth, code, startdate, enddate)
	cost = 0
	for key in data:
		cost += data[key]['standing_charge'] + data[key]['rate'] * data[key]['usage']
	return cost


code = go_code
#code = agile_code

cost = get_cost('20200315', code)

