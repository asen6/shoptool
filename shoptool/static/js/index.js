// index.js

// Constants
var base_url = '/';
var products_per_row = 3;
var empty_product_list_text = 'No products found';

// Page state
var products = {};
var product_ids = [];
var login_dropdown_state = 'off';


// Page ready handler
function init() {

	// Set up event handlers
	$("#get_products_btn").click(get_products_clicked);
	$("#login_toggle").click(login_toggle_clicked);
	$("#login_or_register_btn").click(login_or_register_clicked);
	$("#logout_link").click(logout_clicked);

	$("#input_category")[0].value = 'Jackets';
	$("#input_min_price")[0].value = 0;
	$("#input_max_price")[0].value = 1000;

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
}

function get_products_clicked(){
	var input_category = escape($("#input_category")[0].value);
	var input_min_price = escape($("#input_min_price")[0].value);
	var input_max_price = escape($("#input_max_price")[0].value);

	// Get products
	get_products_request = $.getJSON(base_url + 'get_products/', 'category=' + input_category + '&min_price=' + input_min_price + '&max_price=' + input_max_price,
		function(data, status, xhr) {
			var latest_products_list = data['products'];
			products = {};
			product_ids = [];
			console.log('latest_products_list length = ' + latest_products_list.length);
			for (var i = 0; i < latest_products_list.length; ++i) {
				curr_product_from_server = latest_products_list[i];
				curr_product_id = curr_product_from_server['id'];
				var product = new Product(curr_product_id
											, curr_product_from_server['name']
											, curr_product_from_server['url']
											, curr_product_from_server['brand']
											, curr_product_from_server['description']
											, curr_product_from_server['msrp_price']
											, curr_product_from_server['sale_price']
											, curr_product_from_server['image_url']
											, curr_product_from_server['image_width']
											, curr_product_from_server['image_height']
											, curr_product_from_server['retailer']);
				if (!products[curr_product_id]) {
					products[curr_product_id] = product;
					product_ids.push(curr_product_id);
				}
			}
		})
	.success(function() {rebuild_products_list();})
	.error(function() {console.log('Error - get_products_request');})
	.complete(function() {});

	
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
	.complete(function() {});
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
	});
}


// --------------------------------------------
// --------------------------------------------
// 		OTHER FUNCTIONS
// --------------------------------------------
// --------------------------------------------

function rebuild_products_list(){
	$('#products').empty();
	var container = $('#products')[0];
	var row_container;

	update_empty_product_list_text(product_ids.length);

	// Build the products list
	console.log('Starting product list build.  Should have ' + product_ids.length + ' products.');
	var curr_product_row = -1;
	for (var i = 0; i < product_ids.length; ++i) {
		var curr_product_id = product_ids[i];
		var curr_product = products[curr_product_id];
		if (curr_product) {
			// Add new row if necessary
			var position_in_row = i % products_per_row;
			if (position_in_row == 0) {
				++curr_product_row;
				var new_product_row_element = get_new_product_row_element(curr_product_row);
				container.appendChild(new_product_row_element);
				row_container = $('#product_row_' + curr_product_row)[0];
			}
			
			// Add product to row
			curr_product.div = product_to_dom(curr_product);
			row_container.appendChild(curr_product.div)
		}
	}
}

function update_empty_product_list_text(num_products_found){
	if (num_products_found==0){
		$("#empty_product_list_text").html(empty_product_list_text);
		console.log('no products found');
	} else {
		$('#empty_product_list_text').empty();
		console.log('some products found');
	}
	return;
}

// Creates a new product row
function get_new_product_row_element(row_num){
	new_product_row_element = document.createElement('div');
	new_product_row_element.id = 'product_row_' + row_num;
	$(new_product_row_element).addClass('row');
	$(new_product_row_element).addClass('product_row');
	return new_product_row_element;
}

// Takes a product and builds a div that represents it in the products list
function product_to_dom(product){
	var this_product = document.createElement('div');
	this_product.id = 'product_' + product.id;
	$(this_product).addClass('product');
	span_num = Math.floor(12/products_per_row);
	$(this_product).addClass('span' + toString(span_num));

	var picture = document.createElement('a');
	$(picture).attr('href', product.url);
	var picture_img = document.createElement('img');
	$(picture_img).addClass('product_picture');
	$(picture_img).attr('src', product.image_url);
	picture.appendChild(picture_img);

	var brand = document.createElement('div');
	$(brand).addClass('product_brand');
	$(brand).html(product.brand);

	var name = document.createElement('div');
	$(name).addClass('product_name');
	var name_link = document.createElement('a');
	$(name_link).attr('href', product.url);
	$(name_link).html(product.name);
	name.appendChild(name_link);

	var sale_price = document.createElement('div');
	$(sale_price).addClass('product_sale_price');
	$(sale_price).html('$' + product.sale_price + ' from ' + product.retailer);

	var msrp_price = document.createElement('div');
	$(msrp_price).addClass('product_msrp_price');
	$(msrp_price).html('$' + product.msrp_price);

	var retailer = document.createElement('div');
	$(retailer).addClass('product_retailer');
	$(retailer).html(product.retailer);

	this_product.appendChild(picture);
	this_product.appendChild(brand);
	this_product.appendChild(name);
	this_product.appendChild(sale_price);
	this_product.appendChild(msrp_price);
	this_product.appendChild(retailer);

	return this_product;
}

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






















