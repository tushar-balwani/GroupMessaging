'''
User APIs

1. list users
2. get user
3. create user
4. update user
5. delete user
6. login
7. logout
'''
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, unset_jwt_cookies, jwt_required

from src.main.db import db
from src.main.helper import role_required
from src.main.model.user import User, UserSchema

admin_bp = Blueprint('admin', __name__,)


@admin_bp.route('/users', methods=['GET'])
@role_required(['admin'])
@jwt_required()
def list_users():
    """
    List all users

    Returns
    -------
    Dict - all users
    """
    users = User.query.all()
    schema = UserSchema()
    return jsonify({'users': schema.dump(users, many=True)}), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required(['admin'])
@jwt_required()
def get_user(user_id):
    """
    Get user details

    Parameters
    ----------
    user_id: int - user identifier

    Returns
    -------
    Dict - user detail
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    schema = UserSchema()
    return jsonify({'user': schema.dump(user)}), 200


@admin_bp.route('/users', methods=['POST'])
@role_required(['admin'])
@jwt_required()
def create_user():
    """
    Create new user (only admin can create new user)

    Returns
    -------
    Dict - details of newly created user
    """
    user_data = request.json
    user = User(**user_data)

    db.session.add(user)
    db.session.commit()

    schema = UserSchema()
    return jsonify({'user': schema.dump(user)}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(['admin'])
@jwt_required()
def update_user(user_id):
    """
    Update existing user (only admin can update new user)

    Parameters
    ----------
    user_id: int - user identifier

    Returns
    -------
    Dict - updated user details
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    schema = UserSchema()
    data = schema.load(request.json, partial=True)

    # Update user attributes
    if 'username' in data:
        user.username = data['username']
    if 'password' in data:
        user.password = data['password']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    user.updated_at = datetime.utcnow()

    db.session.commit()

    user_data = schema.dump(user)

    return jsonify({'user': user_data}), 201


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(['admin'])
@jwt_required()
def delete_user(user_id):
    """
    Delete existing user (only admin can delete new user)

    Parameters
    ----------
    user_id: int - user identifier

    Returns
    -------
    Dict - confirmation message
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@admin_bp.route('/login', methods=['POST'])
def login():
    """
    Login user

    Returns
    -------
    Dict - Access token and user details
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.verify_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # create JWT token
    identity = {
        "id": user.id,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "username": user.username
    }
    access_token = create_access_token(identity=identity)

    # serialize user data
    user_schema = UserSchema()
    user_data = user_schema.dump(user)

    # return access token and user data
    response = jsonify({'access_token': access_token, 'user': user_data})
    response.status_code = 200

    return response


@admin_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user

    Returns
    -------
    Dict - confirmation message
    """
    # remove JWT token from client
    response = jsonify({'message': 'Successfully logged out'})
    unset_jwt_cookies(response)
    response.status_code = 200

    return response
