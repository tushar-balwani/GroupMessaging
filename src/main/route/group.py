'''
Group APIs

1. list groups
2. get group
3. create group
4. delete group
5. search group
6. add member
7. remove member
8. list members
9. search message in group
10. list messages
11. get message
12. post message
13. delete message
14. edit message
15. like message
16. unlike message
'''
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from src.main.db import db
from src.main.helper import role_required
from src.main.model.group import GroupSchema, Group
from src.main.model.message import MessageSchema, Message, Like
from src.main.model.user import User, UserSchema

group_bp = Blueprint('group', __name__)


@group_bp.route('/groups', methods=['GET'])
@role_required(['admin', 'user'])
@jwt_required()
def list_groups():
    """
    List all available groups

    Returns
    -------
    Dict - List of group details
    """
    groups = Group.query.all()
    result = GroupSchema().dump(groups, many=True)
    return jsonify({'groups': result}), 200


@group_bp.route('/groups/<int:group_id>', methods=['GET'])
@role_required(['admin', 'user'])
@jwt_required()
def get_group(group_id):
    """
    Get group details

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - group details
    """
    message = Group.query.get_or_404(group_id)
    result = GroupSchema().dump(message)
    return jsonify({'group': result}), 200


@group_bp.route('/groups', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def create_group():
    """
    Create a new group

    Returns
    -------
    Dict - newly created group details
    """
    group_schema = GroupSchema()
    name = request.json.get('name')
    group = Group(name=name)
    try:
        db.session.add(group)
        db.session.commit()
        result = group_schema.dump(group)
        return jsonify({'group': result}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Group with this name already exists'}), 400


@group_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@role_required(['admin', 'user'])
@jwt_required()
def delete_group(group_id):
    """
    Delete existing group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - confirmation message
    """
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    db.session.delete(group)
    db.session.commit()

    return jsonify({'message': 'Group deleted successfully'}), 200


@group_bp.route('/groups/search', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def search_group():
    """
    Search group by text

    Returns
    -------
    Dict - list of groups with keyword
    """
    name = request.json.get('name')
    groups = Group.query.filter(Group.name.ilike(f'%{name}%')).all()
    group_schema = GroupSchema(many=True)
    result = group_schema.dump(groups)
    return jsonify({'groups': result}), 200


@group_bp.route('/groups/<int:group_id>/members', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def add_member(group_id):
    """
    Add member to group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - confirmation message
    """
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    user_id = request.json['user_id']
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user in group.members:
        return jsonify({'error': 'User is already a member of this group'}), 409

    group.members.append(user)
    db.session.commit()

    return jsonify({'message': 'User added to group successfully'}), 201


@group_bp.route('/groups/<int:group_id>/members', methods=['GET'])
@role_required(['admin', 'user'])
@jwt_required()
def list_members(group_id):
    """
    List all members in group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - List of member details
    """
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    result = UserSchema().dump(group.members, many=True)

    return jsonify({'members': result}), 200


@group_bp.route('/groups/<int:group_id>/remove_member', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def remove_member(group_id):
    """
    Remove member from group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------

    """
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    user_id = request.json.get('user_id')
    user = User.query.get(user_id)
    if not user or user not in group.members:
        return jsonify({'error': 'User not found'}), 404
    group.members.remove(user)

    db.session.commit()

    group_schema = GroupSchema()
    result = group_schema.dump(group)

    return jsonify({'group': result}), 200


@group_bp.route('/groups/<int:group_id>/messages/search', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def search_messages(group_id):
    """
    Search for text in group.

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - List of messages with search text in group.
    """
    current_user = get_jwt_identity()
    query = request.json.get('query')

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    members = [members.id for members in group.members]
    if current_user['id'] not in members:
        return jsonify({'error': 'You must be a member of the group to post messages'}), 401

    messages = Message.query.filter(
        Message.group_id == group_id, Message.text.ilike(f"%{query}%")
    ).order_by(Message.timestamp.desc()).all()
    message_schema = MessageSchema(many=True)
    result = message_schema.dump(messages)

    return jsonify({'messages': result, 'total': len(result)}), 200


@group_bp.route('/groups/<int:group_id>/messages', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def post_message(group_id):
    """
    Post message in group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------
    Dict - message details
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    members = [members.id for members in group.members]

    if current_user['id'] not in members:
        return jsonify({'error': 'You must be a member of the group to post messages'}), 401
    text = request.json.get('text')

    message = Message(text=text, user_id=current_user['id'], group_id=group_id)

    db.session.add(message)
    db.session.commit()

    message_schema = MessageSchema()
    result = message_schema.dump(message)
    return jsonify({'message': result}), 201


@group_bp.route('/groups/<int:group_id>/messages', methods=['GET'])
@role_required(['admin', 'user'])
@jwt_required()
def list_messages(group_id):
    """
    List all messages in group

    Parameters
    ----------
    group_id: int - group identifier

    Returns
    -------

    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    members = [members.id for members in group.members]
    if current_user['id'] not in members:
        return jsonify({'error': 'You must be a member of the group to view messages'}), 401

    messages = group.messages.order_by(Message.timestamp.desc()).all()
    message_schema = MessageSchema(many=True)
    result = message_schema.dump(messages)

    return jsonify({'messages': result, "total": len(messages)}), 200


@group_bp.route('/groups/<int:group_id>/messages/<int:message_id>', methods=['GET'])
@role_required(['admin', 'user'])
@jwt_required()
def get_message(group_id, message_id):
    """
    Get message details

    Parameters
    ----------
    group_id: int - group identifier
    message_id: int - message identifier

    Returns
    -------
    Dict - message details
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return jsonify({'error': 'Group not found'}), 404

    members = [members.id for members in group.members]
    if current_user['id'] not in members:
        return jsonify({'error': 'You must be a member of the group to view messages'}), 401

    message = Message.query.filter_by(id=message_id, group_id=group_id).first()
    if not message:
        return jsonify({'error': 'Message not found.'}), 404

    message_schema = MessageSchema()
    result = message_schema.dump(message)

    return jsonify({'message': result}), 200


@group_bp.route('/groups/<int:group_id>/messages/<int:message_id>', methods=['PUT'])
@role_required(['admin', 'user'])
@jwt_required()
def edit_message(group_id, message_id):
    """
    Edit existing message

    Parameters
    ----------
    group_id: int - group identifier
    message_id: int - message identifier

    Returns
    -------
    Dict - updated message details
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    message = Message.query.filter_by(id=message_id, group_id=group_id).first()
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if current_user['id'] != message.user_id:
        return jsonify({'error': 'You are not authorized to edit this message'}), 401

    message_data = request.json
    message.text = message_data['text']

    db.session.commit()

    message_schema = MessageSchema()
    result = message_schema.dump(message)

    return jsonify({'message': result}), 201


@group_bp.route('/groups/<int:group_id>/messages/<int:message_id>', methods=['DELETE'])
@role_required(['admin', 'user'])
@jwt_required()
def delete_message(group_id, message_id):
    """
    Delete a message

    Parameters
    ----------
    group_id: int - group identifier
    message_id: int - message identifier

    Returns
    -------
    Dict - success message
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    message = Message.query.filter_by(id=message_id, group_id=group_id).first()
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if current_user['id'] != message.user_id:
        return jsonify({'error': 'You are not authorized to delete this message'}), 401

    db.session.delete(message)
    db.session.commit()

    return jsonify({'message': 'Message deleted successfully'})


@group_bp.route('/groups/<int:group_id>/messages/<int:message_id>/like', methods=['POST'])
@role_required(['admin', 'user'])
@jwt_required()
def like_message(group_id, message_id):
    """
    Like a message

    Parameters
    ----------
    group_id: int - group identifier
    message_id: int - message identifier

    Returns
    -------
    Dict - success message
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    message = Message.query.filter_by(id=message_id, group_id=group_id).first()
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    if message.user_id == current_user['id']:
        return jsonify({'error': 'Cannot like your own message'}), 400

    like = Like.query.filter_by(user_id=current_user['id'], message_id=message_id).first()
    if like:
        return jsonify({'error': 'Already liked this message'}), 400

    like = Like(user_id=current_user['id'], message_id=message_id)

    db.session.add(like)
    db.session.commit()

    return jsonify({'message': 'Liked successfully'}), 201


@group_bp.route('/groups/<int:group_id>/messages/<int:message_id>/like', methods=['DELETE'])
@role_required(['admin', 'user'])
@jwt_required()
def unlike_message(group_id, message_id):
    """
    Undo liked message

    Parameters
    ----------
    group_id: int - group identifier
    message_id: int - message identifier

    Returns
    -------
    Dict - success message
    """
    current_user = get_jwt_identity()

    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    message = Message.query.filter_by(id=message_id, group_id=group_id).first()
    if not message:
        return jsonify({'error': 'Message not found'}), 404

    like = Like.query.filter_by(user_id=current_user['id'], message_id=message_id).first()
    if not like:
        return jsonify({'error': 'You have not liked this message'}), 400

    db.session.delete(like)
    db.session.commit()

    return jsonify({'message': 'Unliked successfully'}), 200
