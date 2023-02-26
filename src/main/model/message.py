from datetime import datetime
from marshmallow import Schema, fields

from src.main.db import db


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('Like', backref='message', lazy='dynamic')


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))


class LikeSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    message_id = fields.Int(required=True)


class MessageSchema(Schema):
    id = fields.Int(dump_only=True)
    text = fields.Str(required=True)
    user_id = fields.Int(required=True)
    group_id = fields.Int(required=True)
    timestamp = fields.DateTime(dump_only=True)
    likes = fields.Nested(LikeSchema, many=True, dump_only=True)
