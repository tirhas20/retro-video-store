from app import db
from app.models.customer import Customer
from app.models.rental import Rental
from app.models.video import Video
from flask import Blueprint, jsonify,request, make_response, abort 

customers_bp = Blueprint("customers", __name__,url_prefix="/customers")
rentals_bp = Blueprint("rentals",__name__,url_prefix="/rentals")
videos_bp = Blueprint("videos",__name__,url_prefix="/videos")

# helper function
def valid_int(number,parameter_type):
    try:
        int(number)
    except:
        abort(make_response({"error":f"{parameter_type} must be an int"},400))
def validate_video_existence(video_id):
    video = Video.query.get(video_id)
    if not video:
        abort(make_response({"message":f"Video {video_id} was not found"},404))
    return video
def validate_request_body(request_body):
    video_keys = ["title","total_inventory","release_date"]
    for key in video_keys:
        if key not in request_body:
            abort(make_response({"details":f'Request body must include {key}.'},400))
    

@videos_bp.route("",methods=["GET"])
def handle_videos():
    videos = Video.query.all()
    response_body= [video.video_dict() for video in videos]
    return jsonify(response_body),200

@videos_bp.route("/<video_id>",methods=["GET","DELETE","PUT"])
def handle_video(video_id):
    valid_int(video_id,"video_id")
    video =validate_video_existence(video_id)
    
    if request.method == "GET":
        return jsonify(video.video_dict()),200
    elif request.method == "DELETE":
        db.session.delete(video)
        db.session.commit()
        return jsonify(video.video_dict()),200
    elif request.method == "PUT":
        request_body = request.get_json()
        validate_request_body(request_body)
        video.title = request_body["title"]
        video.total_inventory = request_body["total_inventory"]
        video.release_date = request_body["release_date"]
        db.session.commit() 
        return jsonify(video.video_dict()),200
    
@videos_bp.route("",methods=["POST"])
def create_video():
    request_body = request.get_json()
    validate_request_body(request_body)
    new_video = Video(
        title = request_body["title"],
        total_inventory = request_body["total_inventory"],
        release_date = request_body["release_date"]
        )
    db.session.add(new_video)
    db.session.commit()
    return jsonify(new_video.video_dict()),201      
    
@videos_bp.route("<video_id>/rentals", methods=["GET"])
def get_rentals_by_video_id(video_id):
    """Retrieves all rentals associated with a specific video."""
    valid_int(video_id, "video_id")
    video = validate_video_existence(video_id)
    results = db.session.query(Rental,Video, Customer ) \
                        .select_from(Rental).join(Video).join(Customer).all()
    response = []
    for rental,video, customer,  in results:
        response.append({
            "due_date":rental.calculate_due_date(),
            "name":customer.name,
            "phone":customer.phone,
            "postal_code":customer.postal_code
        })
    return jsonify(response),200
                        

