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
	address = false;
	$.ajax({
		url: baseurl + "/v1/accounts/" + account_no,
		type: 'GET',
		headers: {
			"Authorization": "Basic " + btoa(apikey+":")
		},
		dataType: 'json',
		async: false,
		success: function(json) {
			address = json["properties"][0]["address_line_1"];
			if (storecreds == true) {
				setCookie("account_no", account_no, 365);
				setCookie("apikey", apikey, 365);
			} else {
				console.log(storecreds);
			}
		},
	})
	return address;
}

function login() {
	var account_no = document.getElementById("account_no").value;
	var apikey = document.getElementById("apikey").value;
	var storecreds = document.getElementById("storecreds").checked;
	var address = do_login(account_no, apikey, storecreds);
	if (address) {
		logged_in(address);
	} else {
		document.getElementById("loginstate").innerHTML = 'Login failed';
	}
}

function checklogin() {
	var account_no = getCookie("account_no");
	var apikey = getCookie("apikey");
	var address = false;
	if (account_no != "" && apikey != "") {
		address = do_login(account_no, apikey, true);
	}
	var to_return = {"account_no": account_no, "apikey": apikey, "address": address}
	return to_return
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

