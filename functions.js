const baseurl = 'https://api.octopus.energy/'

function getCookie(cname) {
	var name = cname + "=";
	var ca = document.cookie.split(';');
	for(var i = 0; i < ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0) == ' ') {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return "";
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
	$.ajax({
		url: baseurl + "/v1/accounts/" + account_no,
		type: 'GET',
		headers: {"Authorization": "Basic " + btoa(apikey+":")},
		dataType: 'json',
		async: false,
		success: function(json) {
			to_return["address"] = json["properties"][0]["address_line_1"];
			to_return["postcode"] = json["properties"][0]["postcode"];
			if (storecreds == true) {
				setCookie("account_no", account_no, 365);
				setCookie("apikey", apikey, 365);
			}
		},
	})
	return to_return;
}

function login() {
	var account_no = document.getElementById("account_no").value;
	var apikey = document.getElementById("apikey").value;
	var storecreds = document.getElementById("storecreds").checked;
	var user_info = do_login(account_no, apikey, storecreds);
	if ("address" in user_info) {
		logged_in(address);
	} else {
		document.getElementById("loginstate").innerHTML = 'Login failed';
	}
}

function check_login() {
	var account_no = getCookie("account_no");
	var apikey = getCookie("apikey");
	var to_return = {};
	if (account_no != "" && apikey != "") {
		to_return = do_login(account_no, apikey, true);
	}
	to_return["account_no"] = account_no;
	to_return["apikey"] = apikey;
	return to_return;
}

function get_gsp(apikey, postcode) {
	to_return = "";
	$.ajax({
		url: baseurl + "/v1/industry/grid-supply-points/",
		type: "GET",
		headers: {"Authorization": "Basic " + btoa(apikey+":")},
		data: {"postcode": postcode},
		dataType: 'json',
		async: false,
		success: function(json) {
			to_return = json["results"][0]["group_id"];
		}
	})
	return to_return;
}

function get_tariff_code(apikey, code, gsp) {
	to_return = "";
	$.ajax({
		url: baseurl + "/v1/products/" + code,
		type: "GET",
		headers: {"Authorization": "Basic " + btoa(apikey+":")},
		dataType: 'json',
		async: false,
		success: function(json) {
			to_return = json["single_register_electricity_tariffs"][gsp]["direct_debit_monthly"]["code"]
		}
	})
	return to_return;
}

function get_unit_rates(apikey, code, gsp, startdate=null, enddate=null) {
	var tariff_code = get_tariff_code(apikey, code, gsp);
	var results = [];
	var data = {};
	if (startdate != null) {
		data["period_from"] = startdate.toISOString();
		if (enddate != null) {
			data["period_to"] = enddate.toISOString();
		}
	}
	var url = baseurl+"/v1/products/"+code+"/electricity-tariffs/"+tariff_code+"/standard-unit-rates/";
	var headers = {"Authorization": "Basic " + btoa(apikey+":")};
	var j = ajax_get(url, headers, data);
	for (result in j["results"]) {
		results.push(j["results"][result]);
	}
	while (j["next"] != null) {
		var j = ajax_get(j["next"], headers, data);
		for (result in j["results"]) {
			results.push(j["results"][result]);
		}
	}
	return results;
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
	if (param.startsWith('20')) {
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
			if (match[2].includes('year')) {
				to_return.setFullYear(to_return.getFullYear() - match[1]);
			}
			if (match[2].includes('month')) {
				to_return.setMonth(to_return.getMonth() - match[1]);
			}
			if (match[2].includes('week')) {
				to_return.setDate(to_return.getDate() - match[1] * 7);
			}
			if (match[2].includes('day')) {
				to_return.setDate(to_return.getDate() - match[1]);
			}
			if (match[2].includes('hour')) {
				to_return.setHours(to_return.getHours() - match[1]);
			}
			if (match[2].includes('min')) {
				to_return.setMinutes(to_return.getMinutes() - match[1]);
			}
			if (match[2].includes('sec')) {
				to_return.setSeconds(to_return.getSeconds() - match[1]);
			}
		}
	}
	return to_return;
}

