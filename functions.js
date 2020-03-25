var baseurl = "https://api.octopus.energy/"
var go_code = "GO-4H-0030";
var agile_code = "AGILE-18-02-21";

function getCookie(cname) {
	var name = cname + "=";
	var ca = document.cookie.split(";");
	for(var i = 0; i < ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0) == " ") {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return "";
}

function last_element(arr) {
	return arr[arr.length-1]
}

function setCookie(cname, cvalue, exdays) {
	var d = new Date();
	d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
	var expires = "expires="+d.toUTCString();
	document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function logged_in(address) {
	document.getElementById("loginstate").innerHTML = "You are logged in as "+address+".";
	document.getElementById("mainbody").innerHTML = "<a href='octopus.html'>Octopus Comparison</a><br />";
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
		setCookie("account_no", account_no, 365);
		setCookie("apikey", apikey, 365);
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
		to_return = do_login(account_no, apikey, true);
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
	var j = ajax_get(url, headers,data);
	return j["results"][0]["group_id"];
}

function get_tariff_code(user_info, code) {
	var url = baseurl + "/v1/products/" + code;
	var headers = user_info["headers"];
	var j = ajax_get(url, headers);
	var gsp = user_info["gsp"];
	return j["single_register_electricity_tariffs"][gsp]["direct_debit_monthly"]["code"];
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
	var rate_cost = 0;
	var charge_cost = 0;
	for (period in consumption) {
		period_start = Date.parse(consumption[period]["interval_start"]);
		period_consumption = consumption[period]["consumption"];
		for (rate in unit_rates) {
			period_rate_start = Date.parse(unit_rates[rate]["date"])
			if (period_rate_start == period_start) {
				period_rate = unit_rates[rate]["rate"];
				period_cost = period_rate * period_consumption;
				rate_cost += period_cost
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
	return rate_cost + charge_cost;
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
	}
	var headers = user_info["headers"];
	var results = [];
	var data = {};
	if (startdate != null) {
		data["period_from"] = startdate.toISOString();
		if (enddate != null) {
			data["period_to"] = enddate.toISOString();
		}
	}
	var j = {};
	j["next"] = baseurl+"/v1/products/"+code+"/electricity-tariffs/"+tariff_code+"/standard-unit-rates/";
	while (j["next"] != null) {
		var j = ajax_get(j["next"], headers, data);
		for (result in j["results"]) {
			results.push(j["results"][result]);
		}
	}
	return results;
}

function get_30min_unit_rates(user_info, code, startdate, enddate, tariff_code) {
	var rates = get_unit_rates(user_info, code, startdate, enddate, tariff_code);
	var to_return = {};
	var i = 1;
	var d = new Date(startdate.getTime());
	d.setHours(0, 0, 0, 0);
	while (d < enddate) {
		if (d > startdate) {
			to_return[i] = {};
			to_return[i]["date"] = d.toISOString();
			for (rate in rates) {
				if (Date.parse(rates[rate]["valid_from"]) <= d && Date.parse(rates[rate]["valid_to"]) > d) {
					to_return[i]["rate"] = rates[rate]["value_inc_vat"];
					break;
				}
			}
			i += 1;
		} else {
			to_return[0] = {};
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
		}
	})
	return to_return;
}


function parseDateParam(param) {
	var to_return = new Date();
	if (param.startsWith("20")) {
		year = param.substring(0, 4);
		month = param.substring(4, 6);
		day = param.substring(6, 8);
		hour = 0;
		min = 0;
		sec = 0;
		if (param.length > 8) { hour = param.substring(8, 10); }
		if (param.length > 10) { min = param.substring(10, 12); }
		if (param.length > 12) { sec = param.substring(12, 14); }
		to_return = new Date(year, month-1, day, hour, min, sec);
	} else {
		var pattern = /-([0-9]+)(year|month|week|day|hour|min|sec).*/i;
		var match = param.match(pattern);
		if (match != null) {
			if (match[2].includes("year")) {
				to_return.setFullYear(to_return.getFullYear() - match[1]);
			}
			if (match[2].includes("month")) {
				to_return.setMonth(to_return.getMonth() - match[1]);
			}
			if (match[2].includes("week")) {
				to_return.setDate(to_return.getDate() - match[1] * 7);
			}
			if (match[2].includes("day")) {
				to_return.setDate(to_return.getDate() - match[1]);
			}
			if (match[2].includes("hour")) {
				to_return.setHours(to_return.getHours() - match[1]);
			}
			if (match[2].includes("min")) {
				to_return.setMinutes(to_return.getMinutes() - match[1]);
			}
			if (match[2].includes("sec")) {
				to_return.setSeconds(to_return.getSeconds() - match[1]);
			}
		}
	}
	return to_return;
}

