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
	#api_token = environ['OVO_API_TOKEN']
	#headers = {'x-api-key': api_token}
	url = 'https://api.switch.ovoenergy.com/osp/quote'
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
		r = requests.get(url, params=params)
		#print(r.json()['tariffs'])
		charge_cost = r.json()['tariffs']['Variable']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['Variable']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['Variable']['tils']['Electricity']['unitRate']
		#unit_cost_night = r.json()['tariffs']['Variable']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/tariffs ->
	# https://www.edfenergy.com/sites/default/files/goelectric_new_epg_prices.pdf
	# Sept 24
	tariffs['edf98'] = {
		'_A': {'charge_cost': 38.00, 'unit_cost_day': 46.56, 'unit_cost_night': 11.84}, # Eastern
		'_B': {'charge_cost': 44.84, 'unit_cost_day': 43.57, 'unit_cost_night': 12.07}, # East Midlands
		'_C': {'charge_cost': 32.23, 'unit_cost_day': 47.55, 'unit_cost_night': 12.18}, # London
		'_D': {'charge_cost': 47.66, 'unit_cost_day': 49.04, 'unit_cost_night': 10.50}, # North Wales
		'_E': {'charge_cost': 48.21, 'unit_cost_day': 44.71, 'unit_cost_night': 12.11}, # West Midlands
		'_F': {'charge_cost': 49.00, 'unit_cost_day': 42.86, 'unit_cost_night': 11.36}, # North East
		'_G': {'charge_cost': 42.33, 'unit_cost_day': 44.33, 'unit_cost_night': 11.89}, # North West
		'_J': {'charge_cost': 41.75, 'unit_cost_day': 47.07, 'unit_cost_night': 11.63}, # South East
		'_H': {'charge_cost': 43.49, 'unit_cost_day': 45.57, 'unit_cost_night': 11.80}, # Southern
		'_K': {'charge_cost': 48.23, 'unit_cost_day': 45.12, 'unit_cost_night': 12.02}, # South Wales
		'_L': {'charge_cost': 51.71, 'unit_cost_day': 45.25, 'unit_cost_night': 11.38}, # South West
		'_M': {'charge_cost': 48.61, 'unit_cost_day': 43.59, 'unit_cost_night': 12.09}, # Yorkshire
		'_P': {'charge_cost': 50.14, 'unit_cost_day': 43.72, 'unit_cost_night': 12.22}, # North Scotland
		'_N': {'charge_cost': 49.73, 'unit_cost_day': 45.18, 'unit_cost_night': 11.31}, # South Scotland
	}
	tariffs['edf35'] = {
		'_A': {'charge_cost': 38.00, 'unit_cost_day': 51.87, 'unit_cost_night': 4.50}, # Eastern
		'_B': {'charge_cost': 44.84, 'unit_cost_day': 49.05, 'unit_cost_night': 4.50}, # East Midlands
		'_C': {'charge_cost': 32.23, 'unit_cost_day': 53.11, 'unit_cost_night': 4.50}, # London
		'_D': {'charge_cost': 47.66, 'unit_cost_day': 53.39, 'unit_cost_night': 4.50}, # North Wales
		'_E': {'charge_cost': 48.21, 'unit_cost_day': 50.23, 'unit_cost_night': 4.50}, # West Midlands
		'_F': {'charge_cost': 49.00, 'unit_cost_day': 47.82, 'unit_cost_night': 4.50}, # North East
		'_G': {'charge_cost': 42.33, 'unit_cost_day': 49.68, 'unit_cost_night': 4.50}, # North West
		'_J': {'charge_cost': 41.75, 'unit_cost_day': 52.22, 'unit_cost_night': 4.50}, # South East
		'_H': {'charge_cost': 43.49, 'unit_cost_day': 50.86, 'unit_cost_night': 4.50}, # Southern
		'_K': {'charge_cost': 48.23, 'unit_cost_day': 50.56, 'unit_cost_night': 4.50}, # South Wales
		'_L': {'charge_cost': 51.71, 'unit_cost_day': 50.23, 'unit_cost_night': 4.50}, # South West
		'_M': {'charge_cost': 48.61, 'unit_cost_day': 49.08, 'unit_cost_night': 4.50}, # Yorkshire
		'_P': {'charge_cost': 50.14, 'unit_cost_day': 49.31, 'unit_cost_night': 4.50}, # North Scotland
		'_N': {'charge_cost': 49.73, 'unit_cost_day': 50.11, 'unit_cost_night': 4.50}, # South Scotland
	}
	tariffs['edf_overnight'] = {
		'_A': {'charge_cost': 43.76, 'unit_cost_day': 46.38, 'unit_cost_night': 8.00}, # Eastern
		'_B': {'charge_cost': 50.40, 'unit_cost_day': 44.68, 'unit_cost_night': 8.00}, # East Midlands
		'_C': {'charge_cost': 38.28, 'unit_cost_day': 45.84, 'unit_cost_night': 8.00}, # London
		'_D': {'charge_cost': 61.91, 'unit_cost_day': 47.18, 'unit_cost_night': 8.00}, # North Wales
		'_E': {'charge_cost': 54.06, 'unit_cost_day': 45.12, 'unit_cost_night': 8.00}, # West Midlands
		'_F': {'charge_cost': 57.12, 'unit_cost_day': 44.31, 'unit_cost_night': 8.00}, # North East
		'_G': {'charge_cost': 51.51, 'unit_cost_day': 44.79, 'unit_cost_night': 8.00}, # North West
		'_H': {'charge_cost': 49.69, 'unit_cost_day': 45.71, 'unit_cost_night': 8.00}, # Southern
		'_J': {'charge_cost': 47.31, 'unit_cost_day': 46.20, 'unit_cost_night': 8.00}, # South East
		'_K': {'charge_cost': 53.92, 'unit_cost_day': 45.68, 'unit_cost_night': 8.00}, # South Wales
		'_L': {'charge_cost': 58.37, 'unit_cost_day': 44.79, 'unit_cost_night': 8.00}, # South West
		'_M': {'charge_cost': 55.70, 'unit_cost_day': 44.76, 'unit_cost_night': 8.00}, # Yorkshire
		'_N': {'charge_cost': 61.77, 'unit_cost_day': 45.15, 'unit_cost_night': 8.00}, # South Scotland
		'_P': {'charge_cost': 59.08, 'unit_cost_day': 45.32, 'unit_cost_night': 8.00}, # North Scotland
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
