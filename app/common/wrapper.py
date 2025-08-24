from functools import wraps
from flask import request, jsonify
from ..security.authentication import valida_header


def valida_json(required_fields):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            missing = [f for f in required_fields if f not in data]
            if missing:
                return jsonify({'error': f'Campos obrigatórios: {missing}'}), 400
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization")
        if not valida_header(header):
            return jsonify({'error':'Token inválido'}), 401
        return fn(*args, **kwargs)
    return wrapper