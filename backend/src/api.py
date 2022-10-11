import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    formattedDrinks = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": formattedDrinks,
    })


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def drinks_detail(jwt):
    drinks = Drink.query.all()
    formattedDrink = [drnk.long() for drink in drinks]

    return jsonify({
        "success": True,
        "drinks": formattedDrink
    })

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    body = request.get_json()

    title = body.get("title")
    recipe = json.dumps(body.get("recipe"))

    try:
        new_drink = Drink(title=title, recipe=recipe)
        new_drink.insert()
    except:
        abort(422)

    return jsonify({"success": True, "drinks": [new_drink.long()]})


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(jwt, drink_id):
    body = request.get_json()
    title = body.get("title")
    recipe = body.get("recipe")
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)
        if title:
            drink.title = title
        if recipe:
            drink.recipe = json.dumps(recipe)
        drink.update()

    except:
        abort(422)

    return jsonify({"success": True, "drinks": [drink.long()]})


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(jwt, drink_id):
    drink = Drink.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)
    try:
        drink.delete()
    except:
        abort(422)
    return jsonify({"success": True, "delete": drink_id})


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


app.errorhandler(404)


def resource_not_found(error):
    return jsonify({"success": False, "error": 404, "message": "not found"}), 404


@app.errorhandler(422)
def unprocessable(error):
    return (jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422)


@app.errorhandler(500)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 500,
                "message": "server side error"}),
        500,
    )
    
@app.errorhandler(AuthError)
def unauthorized(error):
    return (
        jsonify(
            {
                "success": False,
                "error": error.status_code,
                "message": error.error.get("description"),
            }
        ),
        error.status_code,
    )
