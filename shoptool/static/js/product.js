// product.js

function Product(id, name, url, brand, description, msrp_price, sale_price, image_url, image_width, image_height, retailer){
	this.id = id;
	this.name = name;
	this.url = url;
	this.brand = brand;
	this.description = description;
	this.msrp_price = msrp_price;
	this.sale_price = sale_price;
	this.image_url = image_url;
	this.image_width = image_width;
	this.image_height = image_height;
	this.retailer = retailer;
	this.div = null;
}