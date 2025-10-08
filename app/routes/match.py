from flask import request, jsonify, Blueprint
from ..common.wrapper import valida_json, require_auth
from ..service import match_service

bp =  Blueprint('match', __name__)

@bp.route(f"/suggest", methods=["POST"])
@require_auth
@valida_json(["category_id", "quantity", "measure_unit", "industry_id"])
def suggest(): 
    data = request.get_json()
    try:
        data["quantity"] = int(data["quantity"])
        data["industry_id"] = int(data["industry_id"])
        data["category_id"] = int(data["category_id"])
        data["measure_unit"] = str(data["measure_unit"])
    except ValueError:
        return jsonify({"msg": "error", "error": "Os campos estão com tipo incorreto"}), 400

    try:
        ret = match_service.return_suggestion(data)
        return jsonify({"msg": "ok", "data": ret}), 200
    except Exception as e:
        return jsonify({"msg": "error", "error": str(e)}), 500
