from datetime import datetime
from src import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    balance = db.Column(db.Integer)
    games = db.relationship('Game')


class Game(db.Model):
    # Single game session
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wins = db.Column(db.Integer, default=0)
    loses = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    initial_balance = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.now())
    end_time = db.Column(db.DateTime)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creation_time = db.Column(db.DateTime, default=datetime.now())
    room_socket = db.Column(db.Integer)
    status = db.Column(db.String(16))
    rounds = db.relationship('Round')
    scores = db.relationship('Game')


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    choice = db.Column(db.String(16))
    status = db.Column(db.String(16))
    user_id = db.Column(db.Integer)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_socket = db.Column(db.String(128))
