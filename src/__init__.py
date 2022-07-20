import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    DB_URI = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI.replace('postgres://', 
                                                           'postgresql://')

    from src.models import User, Game, Room, Round

    with app.app_context():
        db.init_app(app)
        db.create_all()
        db.session.commit()
        socketio.init_app(app)

    from src.game import game
    from src.views import views

    app.register_blueprint(game)
    app.register_blueprint(views)

    return app
