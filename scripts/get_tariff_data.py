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

bulb_query="""query Tariffs($postcode: String!, $pricingAtDate: String!) {
  tariffs(postcode: $postcode
  pricingAtDate: $pricingAtDate) {
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
	if datetime.now() > datetime(2021, 10, 2):
		pricingAtDate = datetime.strftime(datetime.now(), "%Y-%m-%d")
	else:
		pricingAtDate = "2021-10-17"
	for gsp in postcodes:
		data = {'operationName':'Tariffs','variables':{'postcode':postcodes[gsp], 'pricingAtDate':pricingAtDate}, 'query': bulb_query}
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
	headers = {'x-ovo-api-key': api_token}
	url = 'https://quote.ovoenergy.com/v3/quick-quote'
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
		charge_cost = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/tariffs ->
	# https://www.edfenergy.com/sites/default/files/goelectric_ratecard_aug23.pdf
	tariffs['edf98'] = {
		'_A': {'charge_cost': 32.90, 'unit_cost_day': 22.67, 'unit_cost_night': 10.05},
		'_B': {'charge_cost': 31.29, 'unit_cost_day': 23.92, 'unit_cost_night': 10.05},
		'_C': {'charge_cost': 32.11, 'unit_cost_day': 21.21, 'unit_cost_night': 10.05},
		'_D': {'charge_cost': 31.04, 'unit_cost_day': 24.70, 'unit_cost_night': 10.05},
		'_E': {'charge_cost': 32.75, 'unit_cost_day': 22.80, 'unit_cost_night': 10.05},
		'_F': {'charge_cost': 34.90, 'unit_cost_day': 22.74, 'unit_cost_night': 10.05},
		'_G': {'charge_cost': 31.91, 'unit_cost_day': 22.22, 'unit_cost_night': 10.05},
		'_J': {'charge_cost': 32.90, 'unit_cost_day': 23.77, 'unit_cost_night': 10.05},
		'_H': {'charge_cost': 31.47, 'unit_cost_day': 22.40, 'unit_cost_night': 10.05},
		'_K': {'charge_cost': 32.42, 'unit_cost_day': 24.63, 'unit_cost_night': 10.05},
		'_L': {'charge_cost': 32.99, 'unit_cost_day': 24.68, 'unit_cost_night': 10.05},
		'_M': {'charge_cost': 35.02, 'unit_cost_day': 22.29, 'unit_cost_night': 10.05},
		'_P': {'charge_cost': 34.93, 'unit_cost_day': 22.29, 'unit_cost_night': 10.05},
		'_N': {'charge_cost': 32.34, 'unit_cost_day': 22.57, 'unit_cost_night': 10.05},
	}
	tariffs['edf35'] = {
		'_A': {'charge_cost': 36.05, 'unit_cost_day': 20.57, 'unit_cost_night': 4.50},
		'_B': {'charge_cost': 34.44, 'unit_cost_day': 21.82, 'unit_cost_night': 4.50},
		'_C': {'charge_cost': 35.26, 'unit_cost_day': 19.11, 'unit_cost_night': 4.50},
		'_D': {'charge_cost': 34.19, 'unit_cost_day': 22.60, 'unit_cost_night': 4.50},
		'_E': {'charge_cost': 35.90, 'unit_cost_day': 20.70, 'unit_cost_night': 4.50},
		'_F': {'charge_cost': 38.05, 'unit_cost_day': 20.64, 'unit_cost_night': 4.50},
		'_G': {'charge_cost': 35.06, 'unit_cost_day': 20.12, 'unit_cost_night': 4.50},
		'_J': {'charge_cost': 36.05, 'unit_cost_day': 21.67, 'unit_cost_night': 4.50},
		'_H': {'charge_cost': 34.62, 'unit_cost_day': 20.30, 'unit_cost_night': 4.50},
		'_K': {'charge_cost': 35.57, 'unit_cost_day': 22.53, 'unit_cost_night': 4.50},
		'_L': {'charge_cost': 36.14, 'unit_cost_day': 22.58, 'unit_cost_night': 4.50},
		'_M': {'charge_cost': 38.17, 'unit_cost_day': 20.19, 'unit_cost_night': 4.50},
		'_P': {'charge_cost': 38.08, 'unit_cost_day': 20.19, 'unit_cost_night': 4.50},
		'_N': {'charge_cost': 35.49, 'unit_cost_day': 20.47, 'unit_cost_night': 4.50},
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
