from flask import request, jsonify, Blueprint
from ..service import match_service
from datetime import datetime

bp =  Blueprint('healthcheck', __name__)

@bp.route("", methods=["GET"])
def healthcheck(): 
    return jsonify({"msg": "ok", "data": f"[{datetime.now()}] Simbia-Artificial-Intelligence is Online :)"}), 200
