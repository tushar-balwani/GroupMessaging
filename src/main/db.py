from flask_sqlalchemy import SQLAlchemy

from src.main.app import app

db = SQLAlchemy(app)
