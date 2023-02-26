from marshmallow import Schema, fields

from src.main.db import db
from src.main.model.user import UserSchema


class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    members = db.relationship('User', secondary='group_members', backref='groups')
    messages = db.relationship('Message', backref='groups', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    group_member = db.Table('group_members',
                            db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                            db.Column('group_id', db.Integer, db.ForeignKey('groups.id')))


class GroupSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    created_by = fields.Nested(UserSchema, dump_only=True)
    members = fields.List(fields.Nested(UserSchema), dump_only=True)
