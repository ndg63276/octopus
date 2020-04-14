var baseurl = "https://api.octopus.energy/"
var go_code = "GO-4H-0030";
var agile_code = "AGILE-18-02-21";

function logged_in(address) {
	document.getElementById("loginstate").innerHTML = "You are logged in as "+address+".";
	document.getElementById("mainbody").innerHTML = "Click <a href='octopus.html"+window.location.search+"'>here</a> if you are not redirected automatically.<br />";
	setTimeout(function () {location.href = "octopus.html"+window.location.search}, 3000);
}

function do_login(account_no, apikey, storecreds) {
	to_return = {};
	var url = baseurl + "/v1/accounts/" + account_no;
	var headers = {"Authorization": "Basic " + btoa(apikey+":")};
	var j = ajax_get(url, headers)
	var last_property = last_element(j["properties"])
	to_return["address"] = last_property["address_line_1"];
	to_return["postcode"] = last_property["postcode"];
	var last_meter_point = last_element(last_property["electricity_meter_points"])
	to_return["mpan"] = last_meter_point["mpan"]
	var last_meter = last_element(last_meter_point["meters"])
	to_return["serial"] = last_meter["serial_number"]
	to_return["headers"] = headers;
	if (storecreds == true) {
		setCookie("account_no", account_no, 365*24);
		setCookie("apikey", apikey, 365*24);
	} else if (storecreds == false) {
		setCookie("account_no", account_no, 1);
		setCookie("apikey", apikey, 1);
	}
	return to_return;
}

function login() {
	var account_no = document.getElementById("account_no").value;
	var apikey = document.getElementById("apikey").value;
	var storecreds = document.getElementById("storecreds").checked;
	var user_info = do_login(account_no, apikey, storecreds);
	if ("address" in user_info) {
		logged_in(user_info["address"]);
	} else {
		document.getElementById("loginstate").innerHTML = "Login failed";
	}
}

function check_login() {
	var account_no = getCookie("account_no");
	var apikey = getCookie("apikey");
	var to_return = {};
	if (account_no != "" && apikey != "") {
		to_return = do_login(account_no, apikey);
		to_return["account_no"] = account_no;
		to_return["apikey"] = apikey;
		to_return["gsp"] = get_gsp(to_return)
	}
	return to_return;
}

function get_gsp(user_info) {
	var url = baseurl + "/v1/industry/grid-supply-points/";
	var headers = user_info["headers"];
	var data = {"postcode": user_info["postcode"]};
	var j = ajax_get(url, headers, data);
	return j["results"][0]["group_id"];
}

function get_all_tariff_codes(code) {
	var url = baseurl + "/v1/products/" + code;
	var j = ajax_get(url);
	var tariff_codes = [];
	if ("single_register_electricity_tariffs" in j) {
		for (gsp in j["single_register_electricity_tariffs"]) {
			tariff_codes.push(j["single_register_electricity_tariffs"][gsp]["direct_debit_monthly"]["code"]);
		}
	}
	return tariff_codes;
}

function get_tariff_code(user_info, code) {
	if (code == 'bulb') {
		return 'bulb';
	}
	var gsp = user_info["gsp"];
	if (gsp == "average") {
		return "average"
	}
	var url = baseurl + "/v1/products/" + code;
	var headers = user_info["headers"];
	var j = ajax_get(url, headers);
	if ("single_register_electricity_tariffs" in j) {
		return j["single_register_electricity_tariffs"][gsp]["direct_debit_monthly"]["code"];
	} else {
		return null;
	}
}

function get_costs(user_info, code, startdate, enddate, tariff_code) {
	if (tariff_code == null) {
		tariff_code = get_tariff_code(user_info, code);
	}
	var consumption = get_consumption(user_info, startdate, enddate);
	var standing_charges = get_standing_charges(user_info, code, startdate, enddate, tariff_code);
	var unit_rates = get_30min_unit_rates(user_info, code, startdate, enddate, tariff_code);
	return get_costs_from_data(consumption, unit_rates, standing_charges)
}

function get_costs_from_data(consumption, unit_rates, standing_charges) {
	var unit_cost = 0;
	var charge_cost = 0;
	for (period in consumption) {
		period_start = Date.parse(consumption[period]["interval_start"]);
		period_consumption = consumption[period]["consumption"];
		for (rate in unit_rates) {
			period_rate_start = Date.parse(unit_rates[rate]["date"]);
			if (period_rate_start == period_start) {
				period_rate = unit_rates[rate]["rate"];
				period_cost = period_rate * period_consumption;
				unit_cost += period_cost
			}
		}
		for (charge in standing_charges) {
			charge_start = Date.parse(standing_charges[charge]["valid_from"]);
			charge_end = Date.parse(standing_charges[charge]["valid_to"]);
			if (charge_start <= period_start && (charge_end > period_start || isNaN(charge_end))) {
				// assume each period is 30 mins
				period_cost = standing_charges[charge]["value_inc_vat"] / 48;
				charge_cost += period_cost;
			}
		}
	}
	return {"unit_cost": unit_cost, "charge_cost": charge_cost};
}

function get_consumption(user_info, startdate, enddate) {
	var headers = user_info["headers"];
	var mpan = user_info["mpan"];
	var serial = user_info["serial"];
	var results = [];
	var data = {};
	if (startdate != null) {
		data["period_from"] = startdate.toISOString();
		if (enddate != null) {
			data["period_to"] = enddate.toISOString();
		}
	}
	var j = {};
	j["next"] = baseurl+"/v1/electricity-meter-points/"+mpan+"/meters/"+serial+"/consumption/";
	while (j["next"] != null) {
		var j = ajax_get(j["next"], headers, data);
		for (result in j["results"]) {
			results.push(j["results"][result]);
		}
	}
	return results;
}

function get_standing_charges(user_info, code, startdate, enddate, tariff_code) {
	if (code == 'bulb') {
		return get_bulb_standing_charges(user_info);
	}
	if (tariff_code == null) {
		tariff_code = get_tariff_code(user_info, code);
	}
	var headers = user_info["headers"];
	var data = {};
	if (startdate != null) {
		data["period_from"] = startdate.toISOString();
		if (enddate != null) {
			data["period_to"] = enddate.toISOString();
		}
	}
	var url = baseurl+"/v1/products/"+code+"/electricity-tariffs/"+tariff_code+"/standing-charges/";
	var j = ajax_get(url, headers, data);
	return j["results"];
}

function get_unit_rates(user_info, code, startdate, enddate, tariff_code) {
	if (tariff_code == null) {
		tariff_code = get_tariff_code(user_info, code);
		tariff_codes = [tariff_code];
	} else if (tariff_code == "average") {
		tariff_codes = get_all_tariff_codes(code);
	} else {
		tariff_codes = [tariff_code];
	}
	var headers = user_info["headers"];
	var results = {};
	var data = {};
	if (startdate != null) {
		data["period_from"] = startdate.toISOString();
		if (enddate != null) {
			data["period_to"] = enddate.toISOString();
		}
	}
	for (index in tariff_codes) {
		var this_result = []
		var j = {};
		tariff_code = tariff_codes[index];
		j["next"] = baseurl+"/v1/products/"+code+"/electricity-tariffs/"+tariff_code+"/standard-unit-rates/";
		while (j["next"] != null) {
			var j = ajax_get(j["next"], headers, data);
			for (result in j["results"]) {
				this_result.push(j["results"][result]);
			}
		}
		results[tariff_code] = this_result;
	}
	results["average"] = get_average_rates(results);
	return results;
}

function get_average_rates(results) {
	average = []
	av_results = {};
	for (tariff_code in results) {
		for (index in results[tariff_code]) {
			valid_from = results[tariff_code][index]["valid_from"];
			valid_to = results[tariff_code][index]["valid_to"];
			value_inc_vat = results[tariff_code][index]["value_inc_vat"];
			if ( ! (valid_from in av_results)) {
				av_results[valid_from] = {"valid_to": valid_to, "value_inc_vat": []}
			}
			av_results[valid_from]["value_inc_vat"].push(value_inc_vat);
		}
	}
	for (av in av_results) {
		vals = av_results[av]["value_inc_vat"];
		sum = vals.reduce((previous, current) => current += previous);
		avg = (sum / vals.length).toFixed(3);
		average.push({"valid_from": av, "valid_to": av_results[av]["valid_to"], "value_inc_vat": avg});
	}
	return average;
}


function get_30min_unit_rates(user_info, code, startdate, enddate, tariff_code) {
	if (code == 'bulb') {
		var all_rates = get_bulb_rates(user_info);
	} else {
		var all_rates = get_unit_rates(user_info, code, startdate, enddate, tariff_code);
	}
	var rates = all_rates[tariff_code];
	var to_return = [];
	var d = new Date(startdate.getTime());
	d.setHours(0, 0, 0, 0);
	while (d < enddate) {
		if (d > startdate) {
			this_rate = {};
			this_rate["date"] = d.toISOString();
			for (rate in rates) {
				if (Date.parse(rates[rate]["valid_from"]) <= d && Date.parse(rates[rate]["valid_to"]) > d) {
					this_rate["rate"] = rates[rate]["value_inc_vat"];
					break;
				}
			}
			to_return.push(this_rate);
		} else {
			to_return = [{}];
			to_return[0]["date"] = d.toISOString();
			for (rate in rates) {
				if (Date.parse(rates[rate]["valid_from"]) <= d && Date.parse(rates[rate]["valid_to"]) > d) {
					to_return[0]["rate"] = rates[rate]["value_inc_vat"];
					break;
				}
			}
		}
		d.setMinutes(d.getMinutes() + 30);
	}
	return to_return;
}

function get_tariff_data(user_info, code, logged_in, consumption) {
	var dataPoints = [];
	var costs = "null";
	tariff_code = get_tariff_code(user_info, code)
	if (tariff_code != null) {
		unit_rates = get_30min_unit_rates(user_info, code, startdate, enddate, tariff_code);
		for (i in unit_rates) {
			dataPoints.push({x: unit_rates[i]["date"], y: unit_rates[i]["rate"]});
		}
		if (logged_in) {
			standing_charges = get_standing_charges(user_info, code, startdate, enddate, tariff_code);
			costs = get_costs_from_data(consumption, unit_rates, standing_charges);
		}
	}
	return { 'costs': costs, datapoints: dataPoints }
}

function ajax_get(url, headers, data) {
	var to_return = {};
	$.ajax({
		url: url,
		type: "GET",
		headers: headers,
		data: data,
		dataType: "json",
		async: false,
		success: function(json) {
			to_return = json;
		},
		error: function() {
			to_return = {};
		}
	})
	return to_return;
}

function future_prices() {
	var pagelink = location.origin+location.pathname;
	window.location.href=pagelink+"?start=now&end=future_prices";
}

function get_carbon_intensity(startdate, enddate) {
	var to_return = [];
	var url = 'https://api.carbonintensity.org.uk/intensity/';
	var s = new Date(startdate);
	s.setSeconds(s.getSeconds()+1)
	var e = new Date(enddate)
	e.setSeconds(e.getSeconds()+1)
	url += s.toISOString() + '/' + e.toISOString();
	var j = ajax_get(url);
	for (i in j["data"]) {
		var this_date = new Date(j["data"][i]["from"]);
		if (this_date < startdate) { continue; }
		if ("actual" in j["data"][i]["intensity"] && j["data"][i]["intensity"]["actual"] != null) {
			var this_intensity = j["data"][i]["intensity"]["actual"];
		} else {
			var this_intensity = j["data"][i]["intensity"]["forecast"];
		}
		to_return.push({"date": this_date.toISOString(), "intensity": this_intensity})
	}
	return to_return;
}

function get_carbon_from_data(consumption, carbon_intensity) {
	var carbon = 0;
	for (period in consumption) {
		period_start = Date.parse(consumption[period]["interval_start"]);
		period_consumption = consumption[period]["consumption"];
		for (rate in carbon_intensity) {
			period_rate_start = Date.parse(carbon_intensity[rate]["date"])
			if (period_rate_start == period_start) {
				period_rate = carbon_intensity[rate]["intensity"];
				period_carbon = period_rate * period_consumption;
				carbon += period_carbon;
			}
		}
	}
	return carbon;
}

function changePostcode() {
	var pc = document.getElementById("postcode").value;
	user_info["postcode"] = pc;
	setCookie("postcode", pc, 365*24);
	var gsp = get_gsp(user_info);
	document.getElementById("region").value = gsp;
	changeRegion(gsp);
}

function changeRegion(val) {
	user_info['gsp'] = val;
	setCookie("gsp", val, 365*24);
	go_data = get_tariff_data(user_info, go_code, logged_in, consumption);
	config.data.datasets[0].data = go_data['datapoints'];
	agile_data = get_tariff_data(user_info, agile_code, logged_in, consumption);
	config.data.datasets[1].data = agile_data['datapoints'];
	myChart.update();
}

function get_config() {
	return {
		type: 'bar',
		data: { datasets: dataSets },
		options: {
			title: { display: false },
			tooltips: {
				mode: 'index',
				position: 'nearest',
				callbacks: {
					footer: function(tooltipItems, data) {
						var index = tooltipItems[0].index;
						if (data.datasets[3] != null && data.datasets[3].data[index] != null) {
							var go_cost = 0;
							var agile_cost = 0;
							var footprint = 0;
							tooltipItems.forEach(function(tooltipItem) {
								if (tooltipItem.datasetIndex == 0) {
									go_cost = tooltipItem.value * data.datasets[3].data[index].y;
								} else if (tooltipItem.datasetIndex == 1) {
									agile_cost = tooltipItem.value * data.datasets[3].data[index].y;
								} else if (tooltipItem.datasetIndex == 2) {
									footprint = tooltipItem.value * data.datasets[3].data[index].y;
								}
							});
							to_return = '';
							if (go_cost != 0) { to_return += 'Go cost: ' + go_cost.toFixed(2) + 'p\n'; }
							if (agile_cost != 0) { to_return += 'Agile cost: ' + agile_cost.toFixed(2) + 'p\n'; }
							if (footprint != 0) { to_return += 'Carbon footprint: ' + footprint.toFixed(1) + 'g'; }
							return to_return;
						}
					},
				},
				footerFontStyle: 'normal'
			},
			legend: {
				display: true,
				position: 'bottom',
				labels: { fontSize: 18, usePointStyle: true }
			},
			scales: {
				xAxes: [{
					type: 'time',
					time: { tooltipFormat: "DD-MM-YY HH:mm:ss" },
					display: true,
					scaleLabel: { display: false },
					offset: true
				}],
				yAxes: [
				{
					id: 'left',
					display: true,
					position: 'left',
					type: 'linear',
					scaleLabel: { display: true, labelString: 'Price (p/kWh)' }
				},
				{
					id: 'right2',
					display: true,
					position: 'right',
					type: 'linear',
					scaleLabel: { display: true, labelString: 'Carbon Intensity (gCO2/kWh)' },
					ticks: { suggestedMin: 0, suggestedMax: 350 }
				},
				{
					id: 'right',
					display: rightAxis,
					position: 'right',
					type: 'linear',
					scaleLabel: { display: true, labelString: 'Consumption (kWh)' }
				}
				]
			}
		}
	};
}

function get_json(jsonfile) {
	var to_return = {};
	$.ajax({
		url: jsonfile,
		async: false,
		dataType: 'json',
		success: function (json) {
			to_return = json;
		}
	});
	return to_return;
}

function get_bulb_rates(user_info) {
	json = get_json('tariffs.json');
	data = json['bulb'];
	region_data = data[user_info["gsp"]];
	to_return = {'bulb': [{'valid_from': '2000-01-01T00:00:00Z', 'valid_to': '2100-01-01T00:00:00Z', 'value_inc_vat': region_data['unit_cost']}]};
	return to_return;
}

function get_bulb_standing_charges(user_info) {
	json = get_json('tariffs.json');
	data = json['bulb'];
	region_data = data[user_info["gsp"]];
	to_return = [{'valid_from': '2000-01-01T00:00:00Z', 'valid_to': '2100-01-01T00:00:00Z', 'value_inc_vat': region_data['charge_cost']}];
	return to_return;
}

function update_tariff_date() {
	json = get_json('tariffs.json');
	date_str = json['meta']['updated'];
	document.getElementById('tariffdate').innerHTML = date_str;
}
