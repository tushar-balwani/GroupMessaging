from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from src.main.app import app

from src.main.db import db
from src.main.config import DevelopmentConfig

from src.main.model.group import Group
from src.main.model.user import User
from src.main.model.message import Message

migrate = Migrate()
jwt = JWTManager(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Group': Group, 'Message': Message}


def unauthorized_response():
    return jsonify({'error': 'Missing Token Header'}), 401


@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return unauthorized_response()


@app.errorhandler(401)
def unauthorized(e):
    return unauthorized_response()


def create_app(config_name=DevelopmentConfig):
    app.config.from_object(config_name)

    db.init_app(app)

    # # Create tables and default admin user at start of project
    # with app.app_context():
    #     db.create_all()
    #
    #     # Create the admin user
    #     admin_user = User(username='admin', password='admin', is_admin=True)
    #     db.session.add(admin_user)
    #
    #     db.session.commit()

    from src.main.route.user import admin_bp
    app.register_blueprint(admin_bp, name='admin_bp')

    from src.main.route.group import group_bp
    app.register_blueprint(group_bp, name='group_bp')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run('localhost', 5000, debug=True)
