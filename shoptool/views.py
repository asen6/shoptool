from shoptool import app, db, gilt_sale, gilt_product, gilt_category, gilt_image_url, gilt_sku
from flask import Flask, request, session, g, redirect, url_for, abort, \
	render_template, flash, _app_ctx_stack
from datetime import datetime
from sqlalchemy import and_
import time
import requests
import json


# Home page

@app.route('/')
def find_items():
	return render_template('find_items.html')


@app.route('/refresh_gilt_data/')
def refresh_gilt():
	apikeystring = '?apikey=ad7a38056f0a95dc24d6dfaa0fe3e0a5'
	r_sales = requests.get('https://api.gilt.com/v1/sales/men/active.json' + apikeystring)
	sales_data = json.loads(r_sales.text)
	product_count = 0
	if sales_data.get('sales') is None:
		return str(product_count)
	for sale in sales_data.get('sales'):
		# add sale if it doesn't exist already
		missing = gilt_sale.query.filter_by(gilt_sale_key=sale.get('sale_key')).first()
		if missing is not None:
			new_sale_id = missing.id
			print 'sale not added (already exists): ' + str(new_sale_id)
		else:
			new_sale = gilt_sale(sale.get('sale_key')
									, sale.get('name')
									, sale.get('sale_url')
									, sale.get('store')
									, sale.get('description')
									, sale.get('begins')
									, sale.get('ends'))
			db.session.add(new_sale)
			db.session.commit()
			new_sale_id = new_sale.id
			print 'added sale: ' + str(new_sale_id)

		# add products
		if sale.get('products') is None:
			continue
		for product in sale.get('products'):
			missing = gilt_product.query.filter_by(product=product).first()
			if missing is not None:
				print '--> product not added (already exists): ' + str(missing.id)
				continue
			r_product = requests.get(product + apikeystring)
			product_data = json.loads(r_product.text)
			new_product = gilt_product(product_data.get('id')
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
			print '--> added product: ' + str(new_product_id)

			# add categories
			if product_data.get('categories') is not None:
				for category in product_data.get('categories'):
					missing = gilt_category.query.filter(and_(gilt_category.gilt_product_id==new_product_id
															, gilt_category.gilt_category==category)).first()
					if missing is not None:
						print '----> category not added (already exists):' + str(missing.id)
						continue
					new_category = gilt_category(category, new_product_id)
					db.session.add(new_category)
					db.session.commit()
					new_category_id = new_category.id
					print '----> added category: ' + str(new_category_id)

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
								print '----> image_url not added (already exists): ' + str(missing.id)
								continue
							new_image_url = gilt_image_url(image.get('width')
															, image.get('height')
															, curr_url
															, new_product_id
															, image_listing_position)
							db.session.add(new_image_url)
							db.session.commit()
							new_image_url_id = new_image_url.id
							print '----> added image_url: ' + str(new_image_url_id)
							image_listing_position = image_listing_position + 1

			# add skus
			if product_data.get('skus') is not None:
				for sku in product_data.get('skus'):
					missing = gilt_sku.query.filter(and_(gilt_sku.gilt_product_id==new_product_id
														, gilt_sku.gilt_sku_id==sku.get('id'))).first()
					if missing is not None:
						print '----> sku not added (already exists): ' + str(missing.id)
						continue
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
										, sku.get('msrp_price')
										, sku.get('sale_price')
										, sku.get('shipping_surcharge')
										, color
										, size
										, new_product_id)
					db.session.add(new_sku)
					db.session.commit()
					new_sku_id = new_sku.id
					print '----> added sku: ' + str(new_sku_id)
			
			product_count = product_count + 1
	return '# of products added: ' + str(product_count)


def update_product(product_id, product_object):
	# TODO
	return
