from shoptool import app, db, AvailableProductCategory, gilt_sale, gilt_product, gilt_category, gilt_image_url, gilt_sku
from flask import Flask, request, session, g, redirect, url_for, abort, \
	render_template, flash, _app_ctx_stack, jsonify, json
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, contains_eager
import time
import requests
import json
import dateutil.parser


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




# -----------------------------------
# 		ADMIN
# -----------------------------------

@app.route('/admin/')
def show_admin():
	# TODO: Figure out how to get and show returned statuses
	try:
		available_products_count = request.args['available_products_count']
	except:
		available_products_count = -1

	try:
		new_product_count = request.args['new_product_count']
	except:
		new_product_count = -1

	return render_template('admin.html'
							, available_products_count=available_products_count
							, new_product_count=new_product_count)

# TODO: Figure out how to continue on error
# NOTE: Assuming that sale / product data will not change (except for inventory status of existing skus)
@app.route('/admin/pull_new_data/', methods=['GET', 'POST'])
def pull_new_data():
	if request.method == 'POST':
		apikeystring = '?apikey=ad7a38056f0a95dc24d6dfaa0fe3e0a5'
		r_sales = requests.get('https://api.gilt.com/v1/sales/men/active.json' + apikeystring)
		sales_data = json.loads(r_sales.text)
		sale_count = 0
		product_count = 0
		changed_inventory_status_count = 0
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
					changed_inventory_status_count = update_inventory_status(missing.id
																			, product_data.get('skus')
																			, changed_inventory_status_count)
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
		db.session.commit()
		print 'changed_inventory_status_count = ' + str(changed_inventory_status_count)
		return redirect(url_for('show_admin', new_product_count=product_count))
	else:
		return redirect(url_for('index'))

def update_inventory_status(product_id, product_data_skus, changed_inventory_status_count):
	if product_data_skus is not None:
		for sku in product_data_skus:
			existing_sku = gilt_sku.query.filter(and_(gilt_sku.gilt_product_id==product_id
												, gilt_sku.gilt_sku_id==sku.get('id'))).first()
			if existing_sku is None:
				continue
			new_inventory_status = sku.get('inventory_status')
			if new_inventory_status != existing_sku.inventory_status:
				existing_sku.inventory_status = new_inventory_status
				changed_inventory_status_count = changed_inventory_status_count + 1
				print 'changed_inventory_status_count = ' + str(changed_inventory_status_count) + ' of sku ' + str(existing_sku.id) + ' to ' + new_inventory_status
				db.session.commit()
	return changed_inventory_status_count


@app.route('/admin/update_available_products_list/', methods=['GET', 'POST'])
def update_available_products_list():
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










