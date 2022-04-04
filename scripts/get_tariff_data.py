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
"_P": "AB166NS",
"_N": "G21NF",
"_J": "CT11AF",
"_H": "OX43TA",
"_K": "CF242AJ",
"_L": "BS11DB",
"_M": "S11DA",
}

regions = {
"_A": "EastEngland",
"_B": "EastMidlands",
"_C": "London",
"_D": "MerseysideAndNorthWales",
"_E": "WestMidlands",
"_F": "NorthEastEngland",
"_G": "NorthWestEngland",
"_J": "SouthEastEngland",
"_H": "SouthernEngland",
"_K": "SouthWales",
"_L": "SouthWestEngland",
"_M": "Yorkshire",
"_P": "NorthScotland",
"_N": "SouthScotland",
}

bulb_query="""query Tariffs($postcode: String!, $pricingAtDate: String!, $availableAtDate: String!) {
  tariffs(
    postcode: $postcode
    pricingAtDate: $pricingAtDate
    availableAtDate: $availableAtDate
  ) {
    residential {
      electricity {
        credit {
          standard {
            standingCharge
            unitRates {
              standard
            }
          }
        }
      }
    }
  }
}
"""


def get_bulb_tariffs(tariffs):
	tariffs['bulb'] = {}
	url = 'https://join-gateway.bulb.co.uk/graphql'
	if datetime.now() > datetime(2022, 5, 11):
		pricingAtDate = datetime.strftime(datetime.now(), "%Y-%m-%d")
	else:
		pricingAtDate = "2022-05-11"
	for gsp in postcodes:
		data = {
			'operationName':'Tariffs',
			'variables':{
				'postcode':postcodes[gsp],
				'pricingAtDate':pricingAtDate,
				'availableAtDate':datetime.strftime(datetime.now(), "%Y-%m-%d")
			},
			'query': bulb_query}
		r = requests.post(url, json=data)
		charge_cost = r.json()['data']['tariffs']['residential']['electricity']['credit']['standard'][0]['standingCharge']
		unit_cost = r.json()['data']['tariffs']['residential']['electricity']['credit']['standard'][0]['unitRates']['standard']
		tariffs['bulb'][gsp] = {'charge_cost': charge_cost, 'unit_cost': unit_cost}
	return tariffs


def get_ovo_tariffs(tariffs):
	tariffs['ovo'] = {}
	#config_url = 'https://switch.ovoenergy.com/ev/config.json'
	#r = requests.get(config_url)
	#if 'API_TOKEN' not in r.json():
	#	print("Ovo tariffs not found")
	#	return tariffs
	#api_token = r.json()['API_TOKEN']
	api_token = environ['OVO_API_TOKEN']
	headers = {'x-api-key': api_token}
	url = 'https://api.switch.ovoenergy.com/quote/quick-quote'
	params = {
		'economy7': True,
		'forceFullService': False,
		'fuel': 'Electricity',
		'onDemandPaymentMethod': False,
		'includeSSR': True,
		'paymentMethod': 'Paym',
		'retailer': 'OVO',
		'serviceType': 'FullService',
		'usage': 'High'
	}
	for gsp in postcodes:
		params['postcode'] = postcodes[gsp]
		params['region'] = regions[gsp]
		r = requests.get(url, headers=headers, params=params)
		#print(r.json()['tariffs'])
		charge_cost = r.json()['tariffs']['Variable']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['Variable']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['Variable']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/tariffs ->
	# https://www.edfenergy.com/sites/default/files/goelectric_ratecard_apr24v2.pdf
	tariffs['edf98'] = {
		'_A': {'charge_cost': 38.00, 'unit_cost_day': 38.96, 'unit_cost_night': 18.85}, # Eastern
		'_B': {'charge_cost': 44.84, 'unit_cost_day': 40.21, 'unit_cost_night': 18.85}, # East Midlands
		'_C': {'charge_cost': 32.23, 'unit_cost_day': 37.75, 'unit_cost_night': 18.85}, # London
		'_D': {'charge_cost': 47.66, 'unit_cost_day': 40.99, 'unit_cost_night': 18.85}, # North Wales
		'_E': {'charge_cost': 48.21, 'unit_cost_day': 39.09, 'unit_cost_night': 18.85}, # West Midlands
		'_F': {'charge_cost': 49.00, 'unit_cost_day': 39.02, 'unit_cost_night': 18.85}, # North East
		'_G': {'charge_cost': 42.33, 'unit_cost_day': 38.51, 'unit_cost_night': 18.85}, # North West
		'_J': {'charge_cost': 41.75, 'unit_cost_day': 40.05, 'unit_cost_night': 18.85}, # South East
		'_H': {'charge_cost': 43.49, 'unit_cost_day': 38.69, 'unit_cost_night': 18.85}, # Southern
		'_K': {'charge_cost': 48.23, 'unit_cost_day': 40.91, 'unit_cost_night': 18.85}, # South Wales
		'_L': {'charge_cost': 51.71, 'unit_cost_day': 40.97, 'unit_cost_night': 18.85}, # South West
		'_M': {'charge_cost': 48.61, 'unit_cost_day': 38.57, 'unit_cost_night': 18.85}, # Yorkshire
		'_P': {'charge_cost': 50.14, 'unit_cost_day': 38.57, 'unit_cost_night': 18.85}, # North Scotland
		'_N': {'charge_cost': 49.73, 'unit_cost_day': 38.85, 'unit_cost_night': 18.85}, # South Scotland
	}
	tariffs['edf35'] = {
		'_A': {'charge_cost': 38.00, 'unit_cost_day': 37.91, 'unit_cost_night': 4.50}, # Eastern
		'_B': {'charge_cost': 44.84, 'unit_cost_day': 39.16, 'unit_cost_night': 4.50}, # East Midlands
		'_C': {'charge_cost': 32.23, 'unit_cost_day': 36.45, 'unit_cost_night': 4.50}, # London
		'_D': {'charge_cost': 47.66, 'unit_cost_day': 39.94, 'unit_cost_night': 4.50}, # North Wales
		'_E': {'charge_cost': 48.21, 'unit_cost_day': 38.04, 'unit_cost_night': 4.50}, # West Midlands
		'_F': {'charge_cost': 49.00, 'unit_cost_day': 37.97, 'unit_cost_night': 4.50}, # North East
		'_G': {'charge_cost': 42.33, 'unit_cost_day': 37.46, 'unit_cost_night': 4.50}, # North West
		'_J': {'charge_cost': 41.75, 'unit_cost_day': 39.00, 'unit_cost_night': 4.50}, # South East
		'_H': {'charge_cost': 43.49, 'unit_cost_day': 37.64, 'unit_cost_night': 4.50}, # Southern
		'_K': {'charge_cost': 48.23, 'unit_cost_day': 39.86, 'unit_cost_night': 4.50}, # South Walkes
		'_L': {'charge_cost': 51.71, 'unit_cost_day': 39.92, 'unit_cost_night': 4.50}, # South West
		'_M': {'charge_cost': 48.61, 'unit_cost_day': 37.52, 'unit_cost_night': 4.50}, # Yorkshire
		'_P': {'charge_cost': 50.14, 'unit_cost_day': 37.52, 'unit_cost_night': 4.50}, # North Scotland
		'_N': {'charge_cost': 49.73, 'unit_cost_day': 37.80, 'unit_cost_night': 4.50}, # South Scotland
	}
	return tariffs


def get_meta_data(tariffs):
	tariffs['meta'] = {'updated': datetime.strftime(datetime.now(), '%Y-%m-%d')}
	return tariffs


def lambda_handler(event, context):
	tariffs = {}
	tariffs = get_bulb_tariffs(tariffs)
	tariffs = get_ovo_tariffs(tariffs)
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
