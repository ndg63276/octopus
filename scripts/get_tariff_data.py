#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import boto3
s3_client = boto3.client('s3')


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

tonik_data = {
	"estimatedUsage": {
		"homeType": "detached",
		"numberOfBedrooms": 1,
		"numberOfPeople": 1
	},
	"channel": "quoteweb",
	"saleType": "registration",
	"extras": {
		"electricVehicle": True
	},
	"fuels": {
		"electricity": True,
		"gas": False
	},
	"meterPoints": {
		"electricity":{
			"isE7": True
		}
	},
	"paymentType": "directDebit",
	"partner": "evclub"
}


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
	url = 'https://api.tonik.tech/v1/quotes/energy'
	for gsp in postcodes:
		tonik_data['postcode'] = postcodes[gsp]
		r = requests.post(url, json=tonik_data)
		charge_cost = r.json()['data']['products'][0]['details']['standingCharges']['electricity']
		unit_cost_day = r.json()['data']['products'][0]['details']['unitRates']['electricity']['day']
		unit_cost_night = r.json()['data']['products'][0]['details']['unitRates']['electricity']['night']
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
		print(gsp)
		charge_cost = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['standingCharge']
		unit_cost_day = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['unitRate']
		unit_cost_night = r.json()['tariffs']['2YearFixed']['tils']['Electricity']['nightUnitRate']
		tariffs['ovo'][gsp] = {'charge_cost': charge_cost, 'unit_cost_day': unit_cost_day, 'unit_cost_night': unit_cost_night}
	return tariffs


def get_meta_data(tariffs):
	tariffs['meta'] = {'updated': datetime.strftime(datetime.now(), '%Y-%m-%d')}
	return tariffs


def lambda_handler(event, context):
	tariffs = {}
	tariffs = get_bulb_tariffs(tariffs)
	tariffs = get_tonik_tariffs(tariffs)
	tariffs = get_ovo_tariffs(tariffs)
	tariffs = get_meta_data(tariffs)
	with open('/tmp/tariffs.json', 'w') as f:
		json.dump(tariffs, f)
	s3_client.upload_file('/tmp/tariffs.json', 'smartathome.co.uk', 'octopus/tariffs.json')


if __name__ =='__main__':
	lambda_handler(None, None)
