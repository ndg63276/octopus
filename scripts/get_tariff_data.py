#!/usr/bin/env python3

import requests
import json
from datetime import datetime


postcodes = {
"_A": "NR11BD",
"_B": "CV11DD",
"_C": "E16AN",
"_D": "L10AF",
"_E": "ST11DB",
"_F": "YO17JA",
"_G": "M11AG",
"_P": "AB101AG",
"_N": "G11BX",
"_J": "CT11AF",
"_H": "OX11AE",
"_K": "CF101AE",
"_L": "BS11DB",
"_M": "S11DA",
}


bulb_query="""query Tariffs($postcode: String!) {
  tariffs(postcode: $postcode) {
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
	url='https://gr.bulb.co.uk/graphql'
	for gsp in postcodes:
		data={'operationName':'Tariffs','variables':{'postcode':postcodes[gsp]}, 'query': bulb_query}
		r = requests.post(url, json=data)
		charge_cost = r.json()['data']['tariffs']['residential']['electricity']['credit']['standard'][0]['standingCharge']
		unit_cost = r.json()['data']['tariffs']['residential']['electricity']['credit']['standard'][0]['unitRates']['standard']
		tariffs['bulb'][gsp] = {'charge_cost': charge_cost, 'unit_cost': unit_cost}
	return tariffs


def get_tonik_tariffs(tariffs):
	tariffs['tonik'] = {}
	for gsp in postcodes:
		charge_cost = 0
		unit_cost_day = 10
		unit_cost_night = 4.17
		tariffs['tonik'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_ovo_tariffs(tariffs):
	tariffs['ovo'] = {}
	config_url = 'https://switch.ovoenergy.com/ev/config.json'
	r = requests.get(config_url)
	if 'API_TOKEN' not in r.json():
		return tariffs
	api_token = r.json()['API_TOKEN']
	headers = {'x-ovo-api-key': api_token}
	url = 'https://quote.ovoenergy.com/v3/quick-quote'
	params = {
		'economy7': True,
		'forceFullService': False,
		'fuel': 'Electricity',
		'includeSSR': True,
		'paymentMethod': 'Paym',
		'retailer': 'OVO',
		'serviceType': 'FullService',
		'usage': 'High'
	}
	for gsp in postcodes:
		params['postcode'] = postcodes[gsp]
		r = requests.get(url, headers=headers, params=params)
		charge_cost = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_edf_tariffs(tariffs):
	# https://www.edfenergy.com/electric-cars/tariffs ->
	# edfenergy.com/sites/default/files/ev_rate_card_go_electric_nov_21.pdf
	tariffs['edf'] = {
		'_A': {'charge_cost': 28.70, 'unit_cost_day': 19.52, 'unit_cost_night': 8.00},
		'_B': {'charge_cost': 27.09, 'unit_cost_day': 20.77, 'unit_cost_night': 8.00},
		'_C': {'charge_cost': 27.91, 'unit_cost_day': 17.94, 'unit_cost_night': 8.00},
		'_D': {'charge_cost': 26.84, 'unit_cost_day': 21.55, 'unit_cost_night': 8.00},
		'_E': {'charge_cost': 28.55, 'unit_cost_day': 19.65, 'unit_cost_night': 8.00},
		'_F': {'charge_cost': 30.70, 'unit_cost_day': 19.59, 'unit_cost_night': 8.00},
		'_G': {'charge_cost': 27.71, 'unit_cost_day': 19.07, 'unit_cost_night': 8.00},
		'_J': {'charge_cost': 28.70, 'unit_cost_day': 20.62, 'unit_cost_night': 8.00},
		'_H': {'charge_cost': 27.27, 'unit_cost_day': 19.25, 'unit_cost_night': 8.00},
		'_K': {'charge_cost': 28.22, 'unit_cost_day': 21.48, 'unit_cost_night': 8.00},
		'_L': {'charge_cost': 28.79, 'unit_cost_day': 21.53, 'unit_cost_night': 8.00},
		'_M': {'charge_cost': 30.82, 'unit_cost_day': 19.14, 'unit_cost_night': 8.00},
		'_P': {'charge_cost': 30.73, 'unit_cost_day': 19.14, 'unit_cost_night': 8.00},
		'_N': {'charge_cost': 28.14, 'unit_cost_day': 19.42, 'unit_cost_night': 8.00},
	}
	return tariffs


def get_meta_data(tariffs):
	tariffs['meta'] = {'updated': datetime.strftime(datetime.now(), '%Y-%m-%d')}
	return tariffs


def lambda_handler(event, context):
	tariffs = {}
	tariffs = get_bulb_tariffs(tariffs)
	tariffs = get_tonik_tariffs(tariffs)
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
