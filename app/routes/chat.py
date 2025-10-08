from flask import request, jsonify, Blueprint
from ..common.wrapper import valida_json, require_auth
from ..service import chat_service

bp =  Blueprint('chat', __name__)

@bp.route(f"/question", methods=["POST"])
@require_auth
@valida_json(['industry_id','message'])
def question(): 
    data = request.get_json()
    print(data)
    try:
        ret = chat_service.get_AI_response(data["message"], data["industry_id"])
        return jsonify({"msg": "ok", "data": ret}), 200
    except Exception as e:
        return jsonify({"msg": "error", "error": str(e)}), 500


    