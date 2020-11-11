var baseurl = "https://api.octopus.energy"
var go_code = "GO-4H-0030";
var agile_code = "AGILE-18-02-21";

function on_login(address) {
	document.getElementById("loginstate").innerHTML = "You are logged in as "+address+".";
	document.getElementById("loginform").classList.add("hidden");
	document.getElementById("mainbody").innerHTML = "Click <a href='index.html"+window.location.search+"'>here</a> if you are not redirected automatically.<br />";
	setTimeout(function () {location.href = "index.html"+window.location.search}, 3000);
}

function on_consumption_change() {
	if (logged_in) {
		totalConsumption = 0;
		consumptionDataPoints = [];
		consumption = get_consumption(user_info, startdate, enddate);
		if (consumption.length > 0) {
			sortByKey(consumption, "interval_start");
			for (i of consumption) {
				var consumption_start = new Date(i["interval_start"]).toISOString()
				consumptionDataPoints.push({x: consumption_start, y: i["consumption"]});
				totalConsumption += i["consumption"];
			}
		}
		carbon = get_carbon_from_data(consumption, carbon_intensity);
	}

	var go_data = get_tariff_data(user_info, go_code, logged_in, consumption);
	var goDataPoints = go_data["datapoints"];
	go_costs = go_data["costs"];
	var agile_data = get_tariff_data(user_info, agile_code, logged_in, consumption);
	agileDataPoints = agile_data["datapoints"];
	agile_costs = agile_data["costs"];

	var dataSets = [
		{type: "line", pointHitRadius:20, backgroundColor:"#00ff00", borderColor:"#00ff00", label:"Octopus Agile",
			fill:false, steppedLine:false, yAxisID:"left", data:agileDataPoints},
		{type: "line", pointHitRadius:20, backgroundColor:"#ff0000", borderColor:"#ff0000", label:"Octopus Go",
			fill:false, steppedLine:true, yAxisID:"left", data:goDataPoints},
		{type: "line", pointHitRadius:20, backgroundColor:"#800080", borderColor:"#800080", label:"Carbon Intensity",
			fill:false, yAxisID:"right2", data:intensityDataPoints, hidden: consumptionDataPoints.length > 0}
	];

	if (consumptionDataPoints.length > 0) {
		dataSets.push({type: "bar", backgroundColor:"#0000ff", label:"Consumption", fill:true, yAxisID:"right", data:consumptionDataPoints});
		rightAxis = true;
	} else {
		rightAxis = false;
	}

	config = get_config(dataSets)

	var loaderDiv = document.getElementById("loader");
	loaderDiv.classList.add("hidden");
	var chartSpace = document.getElementById("chartSpace");
	chartSpace.classList.remove("hidden");
	chartSpace.innerHTML = '<div class="chart-container"><canvas id="octopus-chart" height=500></canvas></div>';
	var ctx = document.getElementById("octopus-chart").getContext("2d");
	myChart = new Chart(ctx, config);

	if (logged_in) {
		document.getElementById("go_unit_cost").innerHTML = "£"+(go_costs["unit_cost"]/100).toFixed(2);
		document.getElementById("agile_unit_cost").innerHTML = "£"+(agile_costs["unit_cost"]/100).toFixed(2);
		document.getElementById("go_charge").innerHTML = "£"+(go_costs["charge_cost"]/100).toFixed(2);
		document.getElementById("agile_charge").innerHTML = "£"+(agile_costs["charge_cost"]/100).toFixed(2);
		document.getElementById("carbon1").innerHTML = (carbon).toFixed(1)+"g";
		document.getElementById("carbon2").innerHTML = (carbon).toFixed(1)+"g";
		document.getElementById("consumption1").innerHTML = (totalConsumption).toFixed(3)+"kWh";
		document.getElementById("consumption2").innerHTML = (totalConsumption).toFixed(3)+"kWh";
		document.getElementById("cost_table").style.display = ""
	}

}

function do_login(account_no, apikey, storecreds) {
	to_return = {};
	var url = baseurl + "/v1/accounts/" + account_no + "/";
	var headers = {"Authorization": "Basic " + btoa(apikey+":")};
	var j = ajax_get(url, headers)
	if ("properties" in j) {
		var last_property = last_element(j["properties"])
		to_return["address"] = last_property["address_line_1"];
		to_return["postcode"] = last_property["postcode"];
		var last_meter_point = last_element(last_property["electricity_meter_points"])
		to_return["mpan"] = last_meter_point["mpan"]
		to_return["mpans"] = {};
		for (this_meter_point of last_property["electricity_meter_points"]) {
			to_return["mpans"][this_meter_point["mpan"]] = [];
			for (meter of this_meter_point["meters"]) {
				to_return["mpans"][this_meter_point["mpan"]].push(meter["serial_number"]);
			}
		}
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
	}
	return to_return;
}

function login() {
	var account_no = document.getElementById("account_no").value;
	var apikey = document.getElementById("apikey").value;
	var storecreds = document.getElementById("storecreds").checked;
	var user_info = do_login(account_no, apikey, storecreds);
	if ("address" in user_info) {
		on_login(user_info["address"]);
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
	var url = baseurl + "/v1/products/" + code + "/";
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
	if (! code.startsWith("GO") && ! code.startsWith("AGILE")) {
		return code;
	}
	var gsp = user_info["gsp"];
	if (gsp == "average") {
		return "average"
	}
	var url = baseurl + "/v1/products/" + code + "/";
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
	for (period of consumption) {
		period_start = Date.parse(period["interval_start"]);
		period_consumption = period["consumption"];
		for (rate of unit_rates) {
			period_rate_start = Date.parse(rate["date"]);
			if (period_rate_start == period_start) {
				period_rate = rate["rate"];
				period_cost = period_rate * period_consumption;
				unit_cost += period_cost
			}
		}
		for (charge of standing_charges) {
			charge_start = Date.parse(charge["valid_from"]);
			charge_end = Date.parse(charge["valid_to"]);
			if (charge_start <= period_start && (charge_end > period_start || isNaN(charge_end))) {
				// assume each period is 30 mins
				period_cost = charge["value_inc_vat"] / 48;
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
		data = {}; // params not needed after first get
		for (result of j["results"]) {
			con = result["consumption"];
			ints = moment(result["interval_start"])
			inte = moment(result["interval_end"])
			if (ints < enddate) {
				results.push({"consumption":con, "interval_start": ints, "interval_end": inte});
			}
		}
	}
	return results;
}

function get_standing_charges(user_info, code, startdate, enddate, tariff_code) {
	if (! code.startsWith("GO") && ! code.startsWith("AGILE")) {
		return get_other_standing_charges(user_info, code, startdate, enddate);
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
	for (tariff_code of tariff_codes) {
		if (startdate != null) {
			data["period_from"] = startdate.toISOString();
			if (enddate != null) {
				data["period_to"] = enddate.toISOString();
			}
		}
		var this_result = []
		var j = {};
		j["next"] = baseurl+"/v1/products/"+code+"/electricity-tariffs/"+tariff_code+"/standard-unit-rates/";
		while (j["next"] != null) {
			var j = ajax_get(j["next"], headers, data);
			data = {}; // params not needed after first get
			for (result of j["results"]) {
				this_result.push(result);
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
		average.push({"valid_from": av_results[av], "valid_to": av_results[av]["valid_to"], "value_inc_vat": avg});
	}
	return average;
}


function get_30min_unit_rates(user_info, code, startdate, enddate, tariff_code) {
	if (code == "bulb") {
		var all_rates = get_single_rate(user_info, code);
	} else if (code == "ovo" || code == "goodenergy") {
		var all_rates = get_e7_rates(user_info, code, startdate, enddate);
	} else if (code == "edf") {
		var all_rates = get_edf_rates(user_info, code, startdate, enddate);
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
			for (rate of rates) {
				if (Date.parse(rate["valid_from"]) <= d && Date.parse(rate["valid_to"]) > d) {
					this_rate["rate"] = rate["value_inc_vat"];
					break;
				}
			}
			to_return.push(this_rate);
		} else {
			to_return = [{}];
			to_return[0]["date"] = d.toISOString();
			for (rate of rates) {
				if (Date.parse(rate["valid_from"]) <= d && Date.parse(rate["valid_to"]) > d) {
					to_return[0]["rate"] = rate["value_inc_vat"];
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
		for (i of unit_rates) {
			dataPoints.push({x: moment(i["date"]), y: i["rate"]});
		}
		if (logged_in) {
			standing_charges = get_standing_charges(user_info, code, startdate, enddate, tariff_code);
			costs = get_costs_from_data(consumption, unit_rates, standing_charges);
		}
	}
	return { "costs": costs, datapoints: dataPoints }
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
	var url = "https://api.carbonintensity.org.uk/intensity/";
	var s = new Date(startdate);
	s.setSeconds(s.getSeconds()+1)
	var e = new Date(enddate);
	if (e-s > 1000*60*60*24*31) {
		e = new Date(startdate);
		e.setDate(s.getDate()+31);
	}
	url += s.toISOString() + "/" + e.toISOString();
	var j = ajax_get(url);
	for (i of j["data"]) {
		var this_date = new Date(i["from"]);
		if (this_date < startdate) { continue; }
		if ("actual" in i["intensity"] && i["intensity"]["actual"] != null) {
			var this_intensity = i["intensity"]["actual"];
		} else {
			var this_intensity = i["intensity"]["forecast"];
		}
		to_return.push({"date": moment(this_date), "intensity": this_intensity})
	}
	return to_return;
}

function get_carbon_from_data(consumption, carbon_intensity) {
	var carbon = 0;
	for (period of consumption) {
		period_start = Date.parse(period["interval_start"]);
		period_consumption = period["consumption"];
		for (rate of carbon_intensity) {
			period_rate_start = Date.parse(rate["date"])
			if (period_rate_start == period_start) {
				period_rate = rate["intensity"];
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
	$("#region").selectmenu("refresh")
	changeRegion(gsp);
}

function changeRegion(val) {
	user_info["gsp"] = val;
	document.getElementById("postcode").value = "";
	if ("postcode" in user_info) {
		delete user_info["postcode"];
	}
	setCookie("gsp", val, 365*24);
	tariffSelect1 = document.getElementById("changeTariffSelectLoggedOut1")
	changeTariff(tariffSelect1.id, tariffSelect1.value);
	tariffSelect2 = document.getElementById("changeTariffSelectLoggedOut2")
	changeTariff(tariffSelect2.id, tariffSelect2.value);
}

function changeMeter() {
	var loaderDiv = document.getElementById("loader");
	loaderDiv.classList.remove("hidden");
	var chartSpace = document.getElementById("chartSpace");
	chartSpace.classList.add("hidden");
	var val = document.getElementById("changeMeterSelect").value;
	user_info["serial"] = val;
	setTimeout(function(){
		on_consumption_change();
		myChart.update();
	}, 1);
}

function changeMPAN() {
	var loaderDiv = document.getElementById("loader");
	loaderDiv.classList.remove("hidden");
	var chartSpace = document.getElementById("chartSpace");
	chartSpace.classList.add("hidden");
	var val = document.getElementById("changeMPANSelect").value;
	user_info["mpan"] = val;
	updateMeters();
	setTimeout(function(){
		on_consumption_change();
		myChart.update();
	}, 1);
}

function updateMeters() {
	$("#changeMeterSelect").empty();
	var changeMeterSelect = document.getElementById("changeMeterSelect");
	for (this_serial_no of user_info["mpans"][user_info["mpan"]]) {
		var option = document.createElement("option");
		option.text = "Meter: "+this_serial_no;
		option.value = this_serial_no;
		changeMeterSelect.add(option);
		option.selected = true;
		user_info["serial"] = this_serial_no;
	}
	$("#changeMeterSelect").selectmenu("refresh");
}

function get_config(dataSets) {
	return {
		type: "bar",
		data: { datasets: dataSets },
		options: {
			responsive: true,
			maintainAspectRatio: false,
			title: { display: false },
			tooltips: {
				mode: "index",
				position: "nearest",
				callbacks: {
					footer: function(tooltipItems, data) {
						var index = tooltipItems[0].index;
						if (data.datasets[3] != null && data.datasets[3].data[index] != null) {
							var agile_cost = 0;
							var go_cost = 0;
							var footprint = 0;
							tooltipItems.forEach(function(tooltipItem) {
								if (tooltipItem.datasetIndex == 0) {
									agile_cost = tooltipItem.value * data.datasets[3].data[index].y;
								} else if (tooltipItem.datasetIndex == 1) {
									go_cost = tooltipItem.value * data.datasets[3].data[index].y;
								} else if (tooltipItem.datasetIndex == 2) {
									footprint = tooltipItem.value * data.datasets[3].data[index].y;
								}
							});
							to_return = "";
							if (agile_cost != 0) { to_return += "Agile cost: " + agile_cost.toFixed(2) + "p\n"; }
							if (go_cost != 0) { to_return += "Go cost: " + go_cost.toFixed(2) + "p\n"; }
							if (footprint != 0) { to_return += "Carbon footprint: " + footprint.toFixed(1) + "g"; }
							return to_return;
						}
					},
				},
				footerFontStyle: "normal"
			},
			legend: {
				display: true,
				onClick: on_legend_click,
				position: "bottom",
				labels: { fontSize: 18, usePointStyle: true }
			},
			scales: {
				xAxes: [{
					type: "time",
					time: { tooltipFormat: "DD-MM-YY HH:mm:ss" },
					display: true,
					scaleLabel: { display: false },
					offset: true
				}],
				yAxes: [
				{
					id: "left",
					display: true,
					position: "left",
					type: "linear",
					scaleLabel: { display: true, labelString: "Price (p/kWh)" },
					ticks: { suggestedMin: 0 }
				},
				{
					id: "right2",
					display: !rightAxis,
					position: "right",
					type: "linear",
					scaleLabel: { display: true, labelString: "Carbon Intensity (gCO2/kWh)" },
					ticks: { suggestedMin: 0, suggestedMax: 350 }
				},
				{
					id: "right",
					display: rightAxis,
					position: "right",
					type: "linear",
					scaleLabel: { display: true, labelString: "Consumption (kWh)" }
				}
				]
			}
		}
	};
}

function get_single_rate(user_info, code) {
	json = get_json("tariffs.json");
	data = json[code];
	data = get_other_average_rates(data);
	region_data = data[user_info["gsp"]];
	var to_return = {};
	to_return[code] = [];
	to_return[code].push({"valid_from": "2000-01-01T00:00:00Z", "valid_to": "2100-01-01T00:00:00Z", "value_inc_vat": region_data["unit_cost"]});
	return to_return;
}

function get_other_average_rates(data) {
	var day_sum = 0;
	var night_sum = 0;
	var unit_sum = 0;
	var charge_sum = 0;
	var length_sum = 0;
	for (region in data) {
		if ("unit_cost_day" in data[region]) {
			day_sum += data[region]["unit_cost_day"];
			night_sum += data[region]["unit_cost_night"];
		} else {
			unit_sum += data[region]["unit_cost"];
		}
		charge_sum += data[region]["charge_cost"];
		length_sum += 1;
	}
	data["average"] = {};
	data["average"]["unit_cost_day"] = day_sum / length_sum;
	data["average"]["unit_cost_night"] = night_sum / length_sum;
	data["average"]["unit_cost"] = unit_sum / length_sum;
	data["average"]["charge_cost"] = charge_sum / length_sum;
	return data;
}

function get_e7_rates(user_info, code, startdate, enddate) {
	json = get_json("tariffs.json");
	data = json[code];
	data = get_other_average_rates(data);
	region_data = data[user_info["gsp"]];
	var to_return = {};
	to_return[code] = [];
	var d = new Date(startdate);
	var d2 = new Date(startdate);
	while (d < enddate) {
		d.setHours(0, 0, 0, 0);
		d2.setHours(7, 0, 0, 0);
		to_return[code].push({"valid_from": d.toISOString(), "valid_to": d2.toISOString(), "value_inc_vat": region_data["unit_cost_night"]});
		d.setHours(7, 0, 0, 0);
		d2.setDate(d2.getDate()+1);
		d2.setHours(0, 0, 0, 0);
		to_return[code].push({"valid_from": d.toISOString(), "valid_to": d2.toISOString(), "value_inc_vat": region_data["unit_cost_day"]});
		d.setDate(d.getDate()+1);
	}
	return to_return;
}

function get_edf_rates(user_info, code, startdate, enddate) {
	json = get_json("tariffs.json");
	data = json[code];
	data = get_other_average_rates(data);
	region_data = data[user_info["gsp"]];
	var to_return = {};
	to_return[code] = [];
	var d = new Date(startdate);
	d.setHours(0, 0, 0, 0);
	var d2 = new Date(startdate);
	while (d < enddate) {
		while (d2.getDay() == 0 || d2.getDay() == 6) { d2.setDate(d2.getDate()+1) };
		d2.setHours(7, 0, 0, 0);
		to_return[code].push({"valid_from": d.toISOString(), "valid_to": d2.toISOString(), "value_inc_vat": region_data["unit_cost_night"]});
		d = new Date(d2);
		d2.setHours(21, 0, 0, 0);
		to_return[code].push({"valid_from": d.toISOString(), "valid_to": d2.toISOString(), "value_inc_vat": region_data["unit_cost_day"]});
		d = new Date(d2);
		d2.setDate(d2.getDate()+1);
	}
	return to_return;
}

function get_other_standing_charges(user_info, code, startdate, enddate) {
	json = get_json("tariffs.json");
	data = json[code];
	data = get_other_average_rates(data);
	region_data = data[user_info["gsp"]];
	to_return = [{"valid_from": startdate.toISOString(), "valid_to": enddate.toISOString(), "value_inc_vat": region_data["charge_cost"]}];
	return to_return;
}

function update_tariff_date() {
	json = get_json("tariffs.json");
	date_str = json["meta"]["updated"];
	document.getElementById("tariffdate").innerHTML = date_str;
}

function changeTariff(id, val) {
	var code;
	var stepped = true;
	if (val == "Octopus Agile") {
		code = agile_code;
		stepped = false;
	} else if (val == "Octopus Go") {
		code = go_code;
	} else if (val == "Bulb Vari-Fair") {
		code = "bulb";
	} else if (val == "Ovo Energy 2 Year Fixed") {
		code = "ovo";
	} else if (val.includes("EDF GoElectric")) {
		code = "edf";
	} else if (val == "Good Energy EV 3") {
		code = "goodenergy";
	} else if (val.startsWith("Octopus Go Faster")) {
		var split = val.split(" ");
		code = "GO-"+split[3]+"-"+split[4];
	}
	new_data = get_tariff_data(user_info, code, logged_in, consumption);
	new_costs = new_data["costs"];
	var cost_el;
	var charge_el;
	var dataset;
	if (id == "changeTariffSelect1" || id == "changeTariffSelectLoggedOut1") {
		cost_el = document.getElementById("agile_unit_cost");
		charge_el = document.getElementById("agile_charge")
		dataset = config.data.datasets[0];
	} else {
		cost_el = document.getElementById("go_unit_cost")
		charge_el = document.getElementById("go_charge")
		dataset = config.data.datasets[1]
	}
	cost_el.innerHTML = "£"+(new_costs["unit_cost"]/100).toFixed(2);
	charge_el.innerHTML = "£"+(new_costs["charge_cost"]/100).toFixed(2);
	dataset.data = new_data["datapoints"];
	dataset.label = val;
	dataset.steppedLine = stepped;
	myChart.update();
}

function download(consumption) {
	var csv = createCsv();
	var filename = "octopus_consumption_"+moment(startdate).format("YYYYMMDDTHHmmss")+"-"+moment(enddate).format("YYYYMMDDTHHmmss")+".csv";
	var element = document.createElement("a");
	element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(csv));
	element.setAttribute("download", filename);
	element.style.display = "none";
	document.body.appendChild(element);
	element.click();
	document.body.removeChild(element);
}

function createCsv() {
	var tariff1 = document.getElementById("changeTariffSelect1").value;
	var tariff2 = document.getElementById("changeTariffSelect2").value;
	var to_return = "Interval Start,"+tariff1+" Price (p/kWh),";
	to_return += tariff2 + " Price (p/kWh),";
	to_return += "Consumption,"+tariff1+" Cost (p),";
	to_return += tariff2 + " Cost (p),";
	to_return += "Carbon Intensity (gCO2/kWh),Carbon Footprint(gCO2)\n";
	for (j in agileDataPoints) {
		to_return += agileDataPoints[j]["x"].format()+",";
		// add other tariff price
		to_return += config.data.datasets[0].data[j]["y"]+",";
		to_return += config.data.datasets[1].data[j]["y"]+",";
		var consumption_found = false;
		for (i in consumption) {
			if (agileDataPoints[j]["x"].format() == consumption[i]["interval_start"].format()) {
				to_return += consumption[i]["consumption"]+",";
				to_return += config.data.datasets[0].data[j]["y"]*consumption[i]["consumption"]+",";
				to_return += config.data.datasets[1].data[j]["y"]*consumption[i]["consumption"]+",";
				consumption_found = true;
				break;
			}
		}
		if (! consumption_found) {
			to_return += ",,,";
		}
		for (k in carbon_intensity) {
			if (carbon_intensity[k]["date"].format() == agileDataPoints[j]["x"].format()) {
				to_return += carbon_intensity[k]["intensity"]+",";
				if (consumption_found) {
					to_return += carbon_intensity[k]["intensity"]*consumption[i]["consumption"]+",";
				}
				break;
			}
		}
		to_return += "\n";
	}
	return to_return;
}

var on_legend_click = function(e, legendItem) {
	var index = legendItem.datasetIndex;
	var ci = this.chart;
	ci.data.datasets[index].hidden = !ci.data.datasets[index].hidden;
	for (leg of ["Carbon", "Consumption"]) {
		if (legendItem.text.includes(leg)) {
			for (axis of ci.options.scales.yAxes) {
				if (axis.scaleLabel.labelString.includes(leg)) {
					axis.display = !ci.data.datasets[index].hidden;
				}
			}
		}
	}
	ci.update();
}

function logout() {
	setCookie("account_no", "", -1);
	setCookie("apikey", "", -1);
	setCookie("postcode", "", -1);
	setCookie("gsp", "", -1);
	location.reload();
}

