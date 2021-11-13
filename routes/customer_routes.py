from app import db
from flask import Blueprint, jsonify,request, make_response, abort
from sqlalchemy import func
from app.models.customer import Customer
from app.models.rental import Rental
from app.models.video import Video
import utils.customer_validations as val
from utils.customer_validations import validate_form_data
from datetime import date, datetime, timezone

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")

def validate_endpoint_id(id, param_id):
    """Validates id for endpoint is an integer."""
    try:
        int(id)
    except:
        abort(make_response({f"details": f"{param_id} must be an int."}, 400))

def timestamp():
    """
    Determines current time and formats to specficiation.
    e.g. "Wed, 16 Apr 2014 21:40:20 -0700"""
    #TODO: fix datetime formatting
    now = datetime.now(timezone.utc).astimezone() #.strftime("%a, %d %b %Y %H:%M:%S %z")
    print(now) # Sat, 06 Nov 2021 21:37:21 -0700 (DOESN'T PRINT THIS WAY IN POSTMAN)
    return now

def query_params():
    query = Customer.query
    # Accepted query params
    sort = request.args.get("sort")
    n = request.args.get("n")
    p = request.args.get("p")

    if sort == "name":
        query = query.order_by(func.lower(Customer.name))
    elif sort == "registered_at":
        query = query.order_by(Customer.registered_at.desc())
    elif sort == "postal_code":
        query = query.order_by(Customer.postal_code)

    try:
        if n and p:
            query = query.paginate(page=int(p), per_page=int(n))          
        elif p:
            query = query.paginate(page=int(p))
        elif n:
            query = query.paginate(per_page=int(n))
        else:
            query = query.all() # Final query, not paginated
            return query, False
    except:
        abort(make_response({"details":"Page not found."},404))

    # Final query, paginated
    return query, True

#WHY DID I HAVE TO DO val.validate_customer_instance(customer_id)... TO IMPORT THIS!?
# DIDN"T WORK AS from ... impor validate_cust...

@customers_bp.route("", methods=["GET"])
def get_all_customer():
    """Retrieves all customers from database."""
    query, paginated = query_params()
    if paginated:
        # If query is Pagination obj, requires .items
        return jsonify([customer.to_dict() for customer in query.items]), 200
    return jsonify([customer.to_dict() for customer in query]), 200


@customers_bp.route("<customer_id>", methods=["GET"])
def get_customer_by_id(customer_id):
    """Retreives customer data by id."""
    validate_endpoint_id(customer_id, "customer_id")
    customer = val.validate_customer_instance(customer_id)
    return jsonify(customer.to_dict())

@customers_bp.route("", methods=["POST"])
def create_customer():
    """Creates a customer from JSON user input."""
    response_body = request.get_json()
    validate_form_data(response_body)

    if not val.validate_postal_code(response_body["postal_code"]):
        return jsonify({"details": "Invalid format for postal_code."}), 400
    if not val.validate_phone_number(response_body["phone"]):
        return jsonify({"details": "Invalid format for phone number."}), 400

    new_customer = Customer(
        name=response_body["name"],
        registered_at=timestamp(),
        postal_code=response_body["postal_code"],
        phone=response_body["phone"]
    )

    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"id": new_customer.id}), 201

@customers_bp.route("<customer_id>", methods=["PUT"])
def update_customer_by_id(customer_id):
    """Updates all customer data by id"""
    customer = val.validate_customer_instance(customer_id)

    response_body = request.get_json()
    val.validate_form_data(response_body)

    customer.update_from_response(response_body)
    db.session.commit()

    return jsonify(customer.to_dict()), 200

@customers_bp.route("<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """Deletes customer account by id."""
    customer = val.validate_customer_instance(customer_id)
    db.session.delete(customer)
    db.session.commit()

    return jsonify({"id": customer.id}), 200


@customers_bp.route("<customer_id>/rentals", methods=["GET"])
def get_rentals_by_customer_id(customer_id):
    validate_endpoint_id(customer_id, "customer_id")
    val.validate_customer_instance(customer_id)

    results = db.session.query(Rental, Customer, Video) \
                        .select_from(Rental).join(Customer).join(Video).all()
    
    response = []
    for rental, customer, video in results:
        response.append({
            "release_date": video.release_date,
            "title": video.title,
            "due_date": rental.due_date,
    })
        
    return jsonify(response), 200