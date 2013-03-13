from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config.from_object('config')

# NEW
db = SQLAlchemy(app)

class gilt_sale(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	gilt_sale_key = db.Column(db.String(40), unique=True)
	sale_name = db.Column(db.String(120))
	sale_url = db.Column(db.Text)
	gilt_store_key = db.Column(db.String(20))
	description = db.Column(db.Text)
	begins = db.Column(db.DateTime)
	ends = db.Column(db.DateTime)
	products = db.relationship('gilt_product', backref='gilt_sale', lazy='select')

	def __init__(self, gilt_sale_key, sale_name, sale_url, gilt_store_key, description, begins, ends):
		self.gilt_sale_key = gilt_sale_key
		self.sale_name = sale_name
		self.sale_url = sale_url
		self.gilt_store_key = gilt_store_key
		self.description = description
		self.begins = begins
		self.ends = ends

	def __repr__(self):
		return '<Sale %r>' % self.sale_name

class gilt_product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	gilt_product_id = db.Column(db.Integer)
	name = db.Column(db.String(120))
	product = db.Column(db.Text)
	brand = db.Column(db.String(120))
	product_url = db.Column(db.Text)
	description = db.Column(db.Text, nullable=True)
	fit_notes = db.Column(db.Text, nullable=True)
	material = db.Column(db.Text, nullable=True)
	care_instructions = db.Column(db.Text, nullable=True)
	origin = db.Column(db.Text, nullable=True)
	gilt_sale_id = db.Column(db.Integer, db.ForeignKey('gilt_sale.id'))
	categories = db.relationship('gilt_category', backref='gilt_product', lazy='select')
	image_urls = db.relationship('gilt_image_url', backref='gilt_product', lazy='select')
	skus = db.relationship('gilt_sku', backref='gilt_product', lazy='select')

	def __init__(self, gilt_product_id, name, product, brand, product_url, description, fit_notes, material, care_instructions, origin, gilt_sale_id):
		self.gilt_product_id = gilt_product_id
		self.name = name
		self.product = product
		self.brand = brand
		self.product_url = product_url
		self.description = description
		self.fit_notes = fit_notes
		self.material = material
		self.care_instructions = care_instructions
		self.origin = origin
		self.gilt_sale_id = gilt_sale_id

	def __repr__(self):
		return '<Product %r>' % self.name

class gilt_category(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	gilt_category = db.Column(db.String(60))
	gilt_product_id = db.Column(db.Integer, db.ForeignKey('gilt_product.id'))

	def __init__(self, gilt_category, gilt_product_id):
		self.gilt_category = gilt_category
		self.gilt_product_id = gilt_product_id

	def __repr__(self):
		return '<Category %r>' % self.gilt_category

class gilt_image_url(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	width = db.Column(db.Integer)
	height = db.Column(db.Integer)
	url = db.Column(db.Text)
	gilt_product_id = db.Column(db.Integer, db.ForeignKey('gilt_product.id'))
	image_listing_position = db.Column(db.Integer)

	def __init__(self, width, height, url, gilt_product_id, image_listing_position):
		self.width = width
		self.height = height
		self.url = url
		self.gilt_product_id = gilt_product_id
		self.image_listing_position = image_listing_position

	def __repr__(self):
		return '<Image_url %r>' % self.url

class gilt_sku(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	gilt_sku_id = db.Column(db.Integer)
	inventory_status = db.Column(db.String(60))
	msrp_price = db.Column(db.Float)
	sale_price = db.Column(db.Float)
	shipping_surcharge = db.Column(db.Float)
	color = db.Column(db.String(40))
	size = db.Column(db.String(20))
	# attributes ?
	gilt_product_id = db.Column(db.Integer, db.ForeignKey('gilt_product.id'))

	def __init__(self, gilt_sku_id, inventory_status, msrp_price, sale_price, shipping_surcharge, color, size, gilt_product_id):
		self.gilt_sku_id = gilt_sku_id
		self.inventory_status = inventory_status
		self.msrp_price = msrp_price
		self.sale_price = sale_price
		self.shipping_surcharge = shipping_surcharge
		self.color = color
		self.size = size
		self.gilt_product_id = gilt_product_id

	def __repr__(self):
		return '<SKU_id %r>' % self.gilt_sku_id

import shoptool.views



