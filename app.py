import json
from datetime import datetime
from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(64), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    storage = db.relationship("Storage", back_populates="product")


class Storage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id", ondelete="SET NULL"))
    location = db.Column(db.String(64), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product", back_populates="storage")


@app.route("/products/add/", methods=["POST"])
def add_product():
    if request.method != "POST":
        abort(405, "POST method required")
    # This branch happens when user submits the form
    try:
        handle = str(request.json["handle"])
        weight = float(request.json["weight"])
        price = float(request.json["price"])
        prod1 = Product(
            handle=handle,
            weight=weight,
            price=price
        )
        db.session.add(prod1)
        db.session.commit()
        return "", 201
    except IntegrityError:
        return "Handle already exists", 409
    except TypeError:
        return "Request content type must be JSON", 415
    except (KeyError, ValueError):
        abort(400)


@app.route("/storage/<product>/add/", methods=["POST"])
def add_to_storage(product):
    if request.method != "POST":
        abort(405, "POST method required")
    try:
        prodhandle = Product.query.filter_by(handle=product).first()
        if prodhandle:
            location = str(request.json["location"])
            qty = int(request.json["qty"])
            storage1 = Storage(
                location=location,
                qty=qty,
                product=prodhandle
            )
            db.session.add(storage1)
            db.session.commit()
            return "", 201
        else:
            return "Product not found", 404

    except (KeyError, ValueError, IntegrityError):
        abort(400)


@app.route("/storage/")
def get_inventory():
    response_data = []
    products = Product.query.all()
    for product in products:
        location_array = []
        for storage in product.storage:
            location_array.append([storage.location, storage.qty])
        data = {
            "handle": product.handle,
            "weight": product.weight,
            "price": product.price,
            "inventory": location_array
        }
        response_data.append(data)
        """response_data = [{"handle": product.handle, "weight": product.weight, "price": product.price, "inventory": [["shop", 2], ["warehouse", 42]]}]"""
        """response_data.append([product.handle, product.weight, product.price])"""
    return json.dumps(response_data)





