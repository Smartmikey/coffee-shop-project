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
'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} 
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    formattedDrinks = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": formattedDrinks,
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def drinks_detail(jwt):
    drinks = Drink.query.all()
    formattedDrink = [drnk.long() for drink in drinks]

    return jsonify({
        "success": True,
        "drinks": formattedDrink
    })

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


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


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

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


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} 
    where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''

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


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404
'''


'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
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
