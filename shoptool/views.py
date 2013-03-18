from shoptool import app, db, User, AvailableProductCategory, gilt_sale, gilt_product, gilt_category, gilt_image_url, gilt_sku
from flask import Flask, request, session, g, redirect, url_for, abort, \
	render_template, flash, _app_ctx_stack, jsonify, json, make_response, \
	send_from_directory
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, contains_eager
import time, requests, json, dateutil.parser, re, os




# -----------------------------------
# 		FRONT END
# -----------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
	available_categories = get_available_categories()
	return render_template('index.html', available_categories=available_categories)

def get_available_categories():
	available_categories = db.session.query(gilt_category).\
										group_by(gilt_category.gilt_category).\
										order_by(gilt_category.gilt_category).\
										all()
	return available_categories

@app.route('/test_json/', methods=['GET'])
def test_json():
	random_something = 'something'
	return jsonify(username=random_something)

@app.route('/get_products/', methods=['GET'])
def get_items():
	category = request.args.get('category', '')
	min_price = request.args.get('min_price', '')
	max_price = request.args.get('max_price', '')
	current_time = datetime.now()

	products = []

	for apc in db.session.query(AvailableProductCategory).\
							filter(AvailableProductCategory.category==category).\
							filter(AvailableProductCategory.sale_price>=min_price).\
							filter(AvailableProductCategory.sale_price<= max_price).\
							all():

		curr_product_dict = {'id': apc.id
								, 'name': apc.name
								, 'url': apc.url
								, 'brand': apc.brand
								, 'description': apc.description
								, 'msrp_price': apc.msrp_price
								, 'sale_price': apc.sale_price
								, 'image_url': apc.image_url
								, 'image_width': apc.image_width
								, 'image_height': apc.image_height
								, 'retailer': apc.retailer
							}
		products.append(curr_product_dict)
	return jsonify(products=products)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# -----------------------------------
# 		USER
# -----------------------------------

# TODO: Check if email in proper format
@app.route('/login_or_register/', methods=['GET'])
def login_or_register():
	admin_email = 'a.sengupta6@gmail.com'
	
	# Check if already logged in
	try:
		user_id = int(request.cookies.get('user_id'))
	except:
		print 'cookie not found'
		user_id = None
	else:
		print 'cookie found: ' + str(user_id)
		result = 'failed'
		message = 'You are already logged in'
		return_data = {'result': result, 'message': message}
		print message
		return jsonify(return_data=return_data)

	email = request.args.get('email', '')
	password = request.args.get('password', '')

	if is_valid_email(email) == False:
		result = 'failed'
		message = 'Invalid email'
		return_data = {'result': result, 'message': message}
		print message
		return jsonify(return_data=return_data)

	if is_valid_password(password) == False:
		result = 'failed'
		message = 'Invalid password'
		return_data = {'result': result, 'message': message}
		print message
		return jsonify(return_data=return_data)

	if email == admin_email:
		admin = True
		print 'admin true (0)'
	else:
		admin = False
		print 'admin false (0)'


	match_found = 0
	for u in db.session.query(User).filter(User.email==email).all():
		match_found = 1
		if u.password == password:
			user_id = u.id
			admin = u.admin
			print 'admin status of found object is ' + str(admin)
			break

	if match_found == 0:
		new_user = User(None, email, password, admin)
		db.session.add(new_user)
		db.session.commit()
		user_id = new_user.id
		result = 'succeeded'
		message = 'Registered new user'
		print message
		response = make_response()
		response.set_cookie('user_id', user_id)
		if admin == True:
			response.set_cookie('admin', True)
			print 'admin true'
		return response
	elif user_id is None:
		result = 'failed'
		message = 'Login failed: Incorrect password'
		return_data = {'result': result, 'message': message}
		print message
		return jsonify(return_data=return_data)
	else:
		result = 'succeeded'
		message = 'Login succeeded'
		print message
		response = make_response()
		response.set_cookie('user_id', user_id)
		if admin == True:
			response.set_cookie('admin', True)
			print 'admin true'
		return response

@app.route('/logout/', methods=['GET'])
def logout():
	response = make_response()
	response.set_cookie('user_id', '', expires=0)
	response.set_cookie('admin', '', expires=0)
	return response

def is_valid_email(email):
	if re.match(r'[^@]+@[^@]+\.[^@]+', email):
		return True
	else:
		return False

def is_valid_password(password):
	if len(password) < 4:
		return False
	else:
		return True

# -----------------------------------
# 		ADMIN
# -----------------------------------

def is_admin(request):
	try:
		admin = request.cookies.get('admin')
	except:
		print 'admin cookie not found'
		return False
	else:
		if admin == 'True':
			print 'admin cookie is true'
			return True
		print 'admin cookie is false'
		return False

@app.route('/admin/')
def show_admin():
	if is_admin(request) == False:
		return redirect(url_for('index'))

	try:
		available_products_count = request.args['available_products_count']
	except:
		available_products_count = -1

	try:
		changed_inventory_status_count = request.args['changed_inventory_status_count']
	except:
		changed_inventory_status_count = -1

	try:
		new_product_count = request.args['new_product_count']
	except:
		new_product_count = -1

	return render_template('admin.html'
							, available_products_count=available_products_count
							, changed_inventory_status_count=changed_inventory_status_count
							, new_product_count=new_product_count)

# TODO: Figure out how to continue on error
# NOTE: Assuming that sale / product data will not change (except inventory status)
@app.route('/admin/pull_new_data/', methods=['GET', 'POST'])
def pull_new_data():
	if is_admin(request) == False:
		return redirect(url_for('index'))
	if request.method == 'POST':
		apikeystring = '?apikey=ad7a38056f0a95dc24d6dfaa0fe3e0a5'
		r_sales = requests.get('https://api.gilt.com/v1/sales/men/active.json' + apikeystring)
		sales_data = json.loads(r_sales.text)
		sale_count = 0
		product_count = 0
		skipped_products_count = 0
		if sales_data.get('sales') is None:
			return str(product_count)
		for sale in sales_data.get('sales'):
			# add sale if it doesn't exist already
			missing = gilt_sale.query.filter_by(gilt_sale_key=sale.get('sale_key')).first()
			if missing is not None:
				new_sale_id = missing.id
			else:
				begins = None
				ends = None
				if sale.get('begins') is not None:
					begins = dateutil.parser.parse(sale.get('begins'), ignoretz=True)
				if sale.get('ends') is not None:
					ends= dateutil.parser.parse(sale.get('ends'), ignoretz=True)
				new_sale = gilt_sale(sale.get('sale_key')
										, sale.get('name')
										, sale.get('sale_url')
										, sale.get('store')
										, sale.get('description')
										, begins
										, ends)
				db.session.add(new_sale)
				db.session.commit()
				new_sale_id = new_sale.id
				sale_count = sale_count + 1
				print 'added sale.  sale_count = ' + str(sale_count)

			# add products
			if sale.get('products') is None:
				continue
			for product in sale.get('products'):
				missing = gilt_product.query.filter_by(product=product).first()
				r_product = requests.get(product + apikeystring)
				product_data = json.loads(r_product.text)
				if missing is not None:
					skipped_products_count = skipped_products_count + 1
					if skipped_products_count % 10 == 0:
						print 'skipped_products_count = ' + str(skipped_products_count)
					continue
				product_id_value = None
				if product_data.get('id') is not None:
					product_id_value = int(float(product_data.get('id')))
				new_product = gilt_product(product_id_value
											, product_data.get('name')
											, product_data.get('product')
											, product_data.get('brand')
											, product_data.get('url')
											, product_data.get('content').get('description')
											, product_data.get('content').get('fit_notes')
											, product_data.get('content').get('material')
											, product_data.get('content').get('care_instructions')
											, product_data.get('content').get('origin')
											, new_sale_id)
				db.session.add(new_product)
				db.session.commit()
				new_product_id = new_product.id
				product_count = product_count + 1
				print '--> added product.  product_count = ' + str(product_count)

				# add categories
				if product_data.get('categories') is not None:
					for category in product_data.get('categories'):
						missing = gilt_category.query.filter(and_(gilt_category.gilt_product_id==new_product_id
																, gilt_category.gilt_category==category)).first()
						if missing is not None:
							continue
						new_category = gilt_category(category, new_product_id)
						db.session.add(new_category)

				# add image_urls
				if product_data.get('image_urls') is not None:
					for image_resolution in product_data.get('image_urls'):
						image_listing_position = 0
						image_resolution_list = product_data.get('image_urls').get(str(image_resolution))
						if image_resolution_list is not None:
							for image in image_resolution_list:
								curr_url = image.get('url')
								missing = gilt_image_url.query.filter(and_(gilt_image_url.gilt_product_id==new_product_id
																		, gilt_image_url.url==curr_url)).first()
								if missing is not None:
									continue
								width = None
								height = None
								if image.get('width') is not None:
									width = int(float(image.get('width')))
								if image.get('height') is not None:
									height = int(float(image.get('height')))
								new_image_url = gilt_image_url(width
																, height
																, curr_url
																, new_product_id
																, image_listing_position)
								db.session.add(new_image_url)
								image_listing_position = image_listing_position + 1

				# add skus
				if product_data.get('skus') is not None:
					for sku in product_data.get('skus'):
						missing = gilt_sku.query.filter(and_(gilt_sku.gilt_product_id==new_product_id
															, gilt_sku.gilt_sku_id==sku.get('id'))).first()
						if missing is not None:
							continue
						msrp_price = None
						sale_price = None
						shipping_surcharge = None
						if sku.get('msrp_price') is not None:
							msrp_price = float(sku.get('msrp_price'))
						if sku.get('sale_price') is not None:
							sale_price = float(sku.get('sale_price'))
						if sku.get('shipping_surcharge') is not None:
							shipping_surcharge = float(sku.get('shipping_surcharge'))
						# get attributes
						color = None
						size = None
						if sku.get('attributes') is not None:
							for attribute in sku.get('attributes'):
								if attribute.get('name') == 'color':
									color = attribute.get('value')
								if attribute.get('name') == 'size':
									size = attribute.get('value')
						new_sku = gilt_sku(sku.get('id')
											, sku.get('inventory_status')
											, msrp_price
											, sale_price
											, shipping_surcharge
											, color
											, size
											, new_product_id)
						db.session.add(new_sku)
		db.session.commit()
		print '...total stats...'
		print '...sale count: ' + str(sale_count)
		print '...product count: ' + str(product_count)
		print '...skipped_products_count: ' + str(skipped_products_count)
		return redirect(url_for('show_admin', new_product_count=product_count))
	else:
		return redirect(url_for('index'))


@app.route('/admin/update_inventory_status/', methods=['GET', 'POST'])
def update_inventory_status():
	if is_admin(request) == False:
		return redirect(url_for('index'))
	if request.method == 'POST':
		
		apikeystring = '?apikey=ad7a38056f0a95dc24d6dfaa0fe3e0a5'
		r_sales = requests.get('https://api.gilt.com/v1/sales/men/active.json' + apikeystring)
		sales_data = json.loads(r_sales.text)
		sale_count = 0
		product_count = 0
		sku_count = 0
		changed_inventory_status_count = 0

		if sales_data.get('sales') is not None:
			for sale in sales_data.get('sales'):
				sale_count = sale_count + 1
				if sale.get('products') is None:
					continue
				for product in sale.get('products'):
					product_count = product_count + 1
					if product_count % 50 == 0:
						print 'product count = ' + str(product_count)
					r_product = requests.get(product + apikeystring)
					product_data = json.loads(r_product.text)
					if product_data.get('skus') is None:
						continue
					for sku in product_data.get('skus'):
						sku_count = sku_count + 1
						gilt_sku_id = sku.get('id')
						sku_object = db.session.query(gilt_sku).filter(gilt_sku.gilt_sku_id==gilt_sku_id).first()
						if sku_object is None or sku.get('inventory_status') is None:
							continue
						current_inventory_status = sku_object.inventory_status
						new_inventory_status = sku.get('inventory_status')
						if current_inventory_status != new_inventory_status:
							sku_object.inventory_status = new_inventory_status
							changed_inventory_status_count = changed_inventory_status_count + 1
							print 'changed_inventory_status_count = ' + str(changed_inventory_status_count) + ' of sku ' + str(sku_object.id) + ' from ' + current_inventory_status + ' to ' + new_inventory_status
			db.session.commit()
		print 'total stats...'
		print '...sale count: ' + str(sale_count)
		print '...product count: ' + str(product_count)
		print '...sku count: ' + str(sku_count)
		print '...changed_inventory_status_count = ' + str(changed_inventory_status_count)
		return redirect(url_for('show_admin', changed_inventory_status_count=changed_inventory_status_count))
	else:
		return redirect(url_for('index'))


@app.route('/admin/update_available_products_list/', methods=['GET', 'POST'])
def update_available_products_list():
	if is_admin(request) == False:
		return redirect(url_for('index'))
	if request.method == 'POST':
		
		# --------------------------------
		# 1. Delete current rows
		# --------------------------------
		delete_count = 0
		available_product_categories = db.session.query(AvailableProductCategory).all()
		print 'starting delete...'
		for apc in available_product_categories:
			db.session.delete(apc)
			delete_count = delete_count + 1
			if delete_count % 1000 == 0:
				print 'delete_count = ' + str(delete_count)
		db.session.commit()
		print 'number of rows deleted = ' + str(delete_count)
		

		# --------------------------------
		# 2. Add new rows
		# --------------------------------
		print 'starting add new rows...'
		available_products_count = 0
		sold_out_products_count = 0

		current_time = datetime.now()
		for product, sale in db.session.query(gilt_product, gilt_sale).\
									filter(gilt_product.gilt_sale_id==gilt_sale.id).\
									filter(gilt_sale.begins<current_time).\
									filter(gilt_sale.ends>current_time).\
									all():
			# Adding sku information...
			available = 0
			msrp_price = None
			sale_price = None
			for sku in db.session.query(gilt_sku).\
									filter(gilt_sku.gilt_product_id==product.id).\
									filter(gilt_sku.inventory_status!='sold out').\
									all():
				available = 1
				if (msrp_price is None) or (sku.sale_price < sale_price):
					msrp_price = sku.msrp_price
					sale_price = sku.sale_price

			if available == 0:
				sold_out_products_count = sold_out_products_count + 1
				continue

			# Adding image information...
			image_url = None
			image_width = None
			image_height = None
			for image in db.session.query(gilt_image_url).\
										filter(gilt_image_url.gilt_product_id==product.id).\
										filter(gilt_image_url.image_listing_position==0).\
										all():
				if (image_url is None) or (image.width == 300 and image.height == 400):
					image_url = image.url
					image_width = image.width
					image_height = image.height

			# Add a row for each product
			for category in product.categories:
				new_apc = AvailableProductCategory('Gilt'
											, product.id
											, product.name
											, category.gilt_category
											, product.brand
											, product.product_url
											, product.description
											, msrp_price
											, sale_price
											, image_url
											, image_width
											, image_height
											, sale.ends)
				db.session.add(new_apc)
				available_products_count = available_products_count + 1
				if available_products_count % 1000 == 0:
					print 'available_products_count = ' + str(available_products_count)
		
		db.session.commit()
		print 'new row count = ' + str(available_products_count)
		print 'sold_out_products_count = ' + str(sold_out_products_count)

		return redirect(url_for('show_admin', available_products_count=available_products_count))
	else:
		return redirect(url_for('index'))










