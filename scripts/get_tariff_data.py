#!/usr/bin/env python3

import requests
import json
from datetime import datetime
from os import environ

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

def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/go-electric-tariff-prices
	tariffs['edf_overnight'] = {
		'_A': {'charge_cost': 49.74, 'unit_cost_day': 28.91, 'unit_cost_night': 8.99}, # Eastern
		'_B': {'charge_cost': 55.80, 'unit_cost_day': 26.65, 'unit_cost_night': 8.99}, # East Midlands
		'_C': {'charge_cost': 40.49, 'unit_cost_day': 27.72, 'unit_cost_night': 8.99}, # London
		'_D': {'charge_cost': 66.78, 'unit_cost_day': 27.79, 'unit_cost_night': 8.99}, # North Wales
		'_E': {'charge_cost': 62.51, 'unit_cost_day': 26.11, 'unit_cost_night': 8.99}, # West Midlands
		'_F': {'charge_cost': 71.01, 'unit_cost_day': 24.98, 'unit_cost_night': 8.99}, # North East
		'_G': {'charge_cost': 50.94, 'unit_cost_day': 29.39, 'unit_cost_night': 8.99}, # North West
		'_H': {'charge_cost': 63.18, 'unit_cost_day': 25.96, 'unit_cost_night': 8.99}, # Southern
		'_J': {'charge_cost': 56.74, 'unit_cost_day': 28.26, 'unit_cost_night': 8.99}, # South East
		'_K': {'charge_cost': 63.02, 'unit_cost_day': 27.28, 'unit_cost_night': 8.99}, # South Wales
		'_L': {'charge_cost': 67.02, 'unit_cost_day': 26.87, 'unit_cost_night': 8.99}, # South West
		'_M': {'charge_cost': 71.01, 'unit_cost_day': 24.98, 'unit_cost_night': 8.99}, # Yorkshire
		'_N': {'charge_cost': 63.08, 'unit_cost_day': 25.64, 'unit_cost_night': 8.99}, # South Scotland
		'_P': {'charge_cost': 60.88, 'unit_cost_day': 27.19, 'unit_cost_night': 8.99}, # North Scotland
	}
	return tariffs


def get_ovo_tariffs(tariffs):
	tariffs['ovo'] = {}
	url = 'https://dzt2p7wlleqwbavh3lymhc6z640rzskz.lambda-url.eu-west-1.on.aws/tariffs'
	params = {
		'fuel': 'electricity',
		'for_sale': 'true',
	}
	for gsp in postcodes:
		params['region'] = gsp
		r = requests.get(url, params=params)
		for tariff in r.json()['tariffs']:
			if tariff['name'] == 'Simpler Energy':
				for n in tariff['tariffInformationLabels']:
					if len(n['ratesByTimingCategory']) == 1:
						charge_cost = 100 * n['standingCharge']
						unit_cost_day = 100 * n['ratesByTimingCategory'][0]['unitRate']
						unit_cost_night = 100 * n['ratesByTimingCategory'][0]['unitRate']
						tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
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
