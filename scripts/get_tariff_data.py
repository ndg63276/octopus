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
    tariffs['edf_goelectric'] = {}
    url = "https://api.edfgb-kraken.energy/v1/graphql/"
    body = {
        "operationName": "GetEvEnergyProducts",
        "variables": { "postcode": "" },
        "query": "query GetEvEnergyProducts($postcode: String!, $cursor: String) { energyProducts( postcode: $postcode brands: [\"EDF\"] tags: [\"ev\"] first: 50 after: $cursor filterBy: [SMART] availability: AVAILABLE ) { pageInfo { endCursor hasNextPage __typename } totalCount edges { node { __typename id fullName code displayName description isVariable isFixed isGreen isBusiness isDomestic isPrepay isAvailable isUnavailable isChargedHalfHourly exitFees notes availableTo availableFrom tags tariffs(postcode: $postcode, paymentMethod: DIRECT_DEBIT, first: 10) { edges { node { __typename ... on DayNightTariff { id displayName fullName description standingCharge dayRate nightRate __typename } ... on StandardTariff { id displayName fullName description standingCharge unitRate __typename } } __typename } __typename } } __typename } __typename }}"
    }
    for gsp in postcodes:
        body["variables"]["postcode"] = postcodes[gsp]
        r = requests.post(url, json=body)
        if r.status_code != 200:
            print("error getting data")
            continue
        for i in r.json()['data']['energyProducts']['edges']:
            if i["node"]["code"] != "EDF_EV_FIX_GOELEC_12M_HH":
                continue
            tariffs['edf_goelectric'][gsp] = {
                "charge_cost": i['node']['tariffs']['edges'][0]['node']['standingCharge'],
                "unit_cost_day": i['node']['tariffs']['edges'][0]['node']['dayRate'],
                "unit_cost_night": i['node']['tariffs']['edges'][0]['node']['nightRate'],
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
	if event is not None or False:
		import boto3
		s3_client = boto3.client('s3')
		s3_client.upload_file('/tmp/tariffs.json', 'smartathome.co.uk', 'octopus/tariffs.json', ExtraArgs={'ContentType': 'text/json'})


if __name__ == '__main__':
	lambda_handler(None, None)
