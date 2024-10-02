#!/usr/bin/env python3

import requests
import json
from datetime import datetime
from os import environ

postcodes = {
"_A": "NR11BD",
"_B": "CV11DD",
"_C": "E16AN",
"_D": "L10AF",
"_E": "ST11DB",
"_F": "YO17JA",
"_G": "OL114LT",
"_H": "OX43TA",
"_J": "CT11AF",
"_K": "CF242AJ",
"_L": "BS11DB",
"_M": "S11DA",
"_N": "G21NF",
"_P": "AB166NS",
}

regions = {
"_A": "EastEngland",
"_B": "EastMidlands",
"_C": "London",
"_D": "MerseysideAndNorthWales",
"_E": "WestMidlands",
"_F": "NorthEastEngland",
"_G": "NorthWestEngland",
"_H": "SouthernEngland",
"_J": "SouthEastEngland",
"_K": "SouthWales",
"_L": "SouthWestEngland",
"_M": "Yorkshire",
"_N": "SouthScotland",
"_P": "NorthScotland",
}


def get_ovo_tariffs(tariffs):
	tariffs['ovo'] = {}
	#config_url = 'https://switch.ovoenergy.com/ev/config.json'
	#r = requests.get(config_url)
	#if 'API_TOKEN' not in r.json():
	#	print("Ovo tariffs not found")
	#	return tariffs
	#api_token = r.json()['API_TOKEN']
	#api_token = environ['OVO_API_TOKEN']
	#headers = {'x-api-key': api_token}
	url = 'https://journey.products.ovoenergy.com/quote'
	params = {
		'fuel': 'Electricity',
		'paymentMethod': 'Paym',
		'usage': 'High',
		'propertyOwner': 'Yes',
		'propertySearchId': ''
	}
	for gsp in postcodes:
		params['postcode'] = postcodes[gsp]
		params['region'] = regions[gsp]
		r = requests.get(url, params=params)
		#print(r.json()['tariffs'])
		charge_cost = r.json()['tariffs']['Variable']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['Variable']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['Variable']['tils']['Electricity']['unitRate']
		#unit_cost_night = r.json()['tariffs']['Variable']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/ev-tariffs ->
	# Request a quote
	tariffs['edf_overnight'] = {
		'_A': {'charge_cost': 51.26, 'unit_cost_day': 25.23, 'unit_cost_night': 8.99}, # Eastern
		'_B': {'charge_cost': 56.62, 'unit_cost_day': 23.84, 'unit_cost_night': 8.99}, # East Midlands
		'_C': {'charge_cost': 41.50, 'unit_cost_day': 25.58, 'unit_cost_night': 8.99}, # London
		'_D': {'charge_cost': 67.70, 'unit_cost_day': 26.72, 'unit_cost_night': 8.99}, # North Wales
		'_E': {'charge_cost': 63.61, 'unit_cost_day': 23.67, 'unit_cost_night': 8.99}, # West Midlands
		'_F': {'charge_cost': 71.77, 'unit_cost_day': 22.82, 'unit_cost_night': 8.99}, # North East
		'_G': {'charge_cost': 51.81, 'unit_cost_day': 25.87, 'unit_cost_night': 8.99}, # North West
		'_H': {'charge_cost': 64.54, 'unit_cost_day': 23.27, 'unit_cost_night': 8.99}, # Southern
		'_J': {'charge_cost': 58.22, 'unit_cost_day': 25.32, 'unit_cost_night': 8.99}, # South East
		'_K': {'charge_cost': 63.62, 'unit_cost_day': 24.63, 'unit_cost_night': 8.99}, # South Wales
		'_L': {'charge_cost': 68.69, 'unit_cost_day': 24.43, 'unit_cost_night': 8.99}, # South West
		'_M': {'charge_cost': 68.18, 'unit_cost_day': 23.31, 'unit_cost_night': 8.99}, # Yorkshire
		'_N': {'charge_cost': 65.16, 'unit_cost_day': 23.80, 'unit_cost_night': 8.99}, # South Scotland
		'_P': {'charge_cost': 62.93, 'unit_cost_day': 25.64, 'unit_cost_night': 8.99}, # North Scotland
	}
	return tariffs


def get_meta_data(tariffs):
	tariffs['meta'] = {'updated': datetime.strftime(datetime.now(), '%Y-%m-%d')}
	return tariffs


def lambda_handler(event, context):
	tariffs = {}
	#tariffs = get_ovo_tariffs(tariffs)
	tariffs = get_edf_tariffs(tariffs)
	tariffs = get_meta_data(tariffs)
	with open('/tmp/tariffs.json', 'w') as f:
		json.dump(tariffs, f)
	if event is not None:
		import boto3
		s3_client = boto3.client('s3')
		s3_client.upload_file('/tmp/tariffs.json', 'smartathome.co.uk', 'octopus/tariffs.json', ExtraArgs={'ContentType': 'text/json'})


if __name__ == '__main__':
	lambda_handler(None, None)
