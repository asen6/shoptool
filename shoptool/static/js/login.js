// login.js

// Constants
var base_url = '/';

// Page state
var login_dropdown_state = 'off';


// Page ready handler
function init() {

	// Set up event handlers
	$("#login_toggle").click(login_toggle_clicked);
	$("#login_or_register_btn").click(login_or_register_clicked);
	$("#logout_link").click(logout_clicked);

	check_if_logged_in();
}
$(document).ready(init);




// --------------------------------------------
// --------------------------------------------
// 		EVENT HANDLERS
// --------------------------------------------
// --------------------------------------------

function check_if_logged_in() {
	var user_id = get_cookie('user_id');
	if (user_id == null) {
		show_login();
		hide_logout();
	} else {
		show_logout();
		hide_login();
	}

	update_admin_link();
}


function login_toggle_clicked() {
	if (login_dropdown_state == 'off') {
		show_login_dropdown();
	} else {
		hide_login_dropdown();
	}
}


function login_or_register_clicked() {
	var raw_email = $("#input_email")[0].value;
	var raw_password = $("#input_password")[0].value
	var email = escape(raw_email);
	var password = escape(raw_password);

	login_request = $.getJSON(base_url + 'login_or_register/', 'email=' + email + '&password=' + password,
		function(data, status, xhr) {
			try {
				console.log(data['return_data']['message']);
			} catch (err) {
				console.log('login successful');
				show_logout();
				hide_login();
				$("#input_email")[0].value = '';
				$("#input_password")[0].value = '';
			}
		})
	.success(function() {})
	.error(function() {console.log('Error - login_request');})
	.complete(function() {
		console.log('about to ask to update admin');
		update_admin_link();
	});


}


function logout_clicked() {
	logout_request = $.getJSON(base_url + 'logout/',
		function(data, status, xhr) {
			console.log('logged out');
		})
	.success(function() {})
	.error(function() {console.log('Error - logout_request');})
	.complete(function() {
		show_login();
		hide_logout();
		$("#input_email")[0].value = '';
		$("#input_password")[0].value = '';
		console.log('about to ask to update admin');
		update_admin_link();
	});
}


// --------------------------------------------
// --------------------------------------------
// 		OTHER FUNCTIONS
// --------------------------------------------
// --------------------------------------------

function get_cookie(c_name) {
	var i,x,y,ARRcookies=document.cookie.split(";");
	for (i=0;i<ARRcookies.length;i++) {
		x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
		y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
		x=x.replace(/^\s+|\s+$/g,"");
		if (x==c_name) {
			return unescape(y);
		}
	}
}

function update_admin_link() {
	console.log('checking admin status...')
	var admin = get_cookie('admin');
	if (admin == 'True') {
		show_admin();
	} else {
		hide_admin();
	}
}


function show_login(){
	console.log('showing login...');
	$('#login_link_area').show();
}

function hide_login(){
	console.log('hiding login...');
	hide_login_dropdown();
	$('#login_link_area').hide();
}

function show_login_dropdown() {
	console.log('showing login dropdown...');
	$('#login_dropdown_menu').show();
	login_dropdown_state = 'on';
}

function hide_login_dropdown() {
	console.log('hiding login dropdown...');
	$('#login_dropdown_menu').hide();
	login_dropdown_state = 'off';
}

function show_logout(){
	console.log('showing logout...');
	$('#logout_link_area').show();
}

function hide_logout(){
	console.log('hiding logout...');
	$('#logout_link_area').hide();
}

function show_admin() {
	console.log('showing admin...');
	$('#admin_link_area').show();
}

function hide_admin() {
	console.log('hiding admin...');
	$('#admin_link_area').hide();
}




















