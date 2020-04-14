#!/usr/bin/env python3

import requests
import json

postcodes = {
"_A": "NR11BD",
"_B": "CV11DD",
"_C": "E16AN",
"_D": "L10AF",
"_E": "ST11DB",
"_F": "YO10AT",
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

if __name__ == "__main__":
	tariffs = {}
	tariffs = get_bulb_tariffs(tariffs)
	with open('tariffs.json', 'w') as f:
		json.dump(tariffs, f)
