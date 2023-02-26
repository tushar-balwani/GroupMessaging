from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from src.main.model.user import User


def role_required(roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.filter_by(id=current_user_id['id']).first()
            # TODO: update for multiple roles
            role = 'admin' if user.is_admin else 'user'
            if role not in roles:
                return jsonify({'error': 'You do not have the required role'}), 403
            if not user.is_active:
                return jsonify({'error': 'User is disabled'}), 401
            return fn(*args, **kwargs)

        return wrapper

    return decorator
