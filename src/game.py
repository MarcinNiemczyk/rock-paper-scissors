from datetime import datetime
from flask import Blueprint, render_template, session
from flask_socketio import emit, join_room, leave_room
from src import db, socketio
from src.models import User, Room, Round, Game
from src.settings import *

game = Blueprint('game', __name__)

@game.route('/')
def index():
    if 'user_id' not in session:
        # Eeach new session is a new player
        user = User(balance=initial_credits)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
    else:
        # Find user to display his balance on the screen
        user = User.query.filter_by(id=session['user_id']).first()
    return render_template('index.html', balance=user.balance)


@socketio.on('connection')
def connection(socket_id):
    """Add socket id to session to communicate with user individually"""
    session['socket_id'] = socket_id
    session['room_id'] = None
    emit('update-log', message_connection.format(session['user_id']))


@socketio.on('play')
def play():
    """Find game room for user"""
    user = User.query.filter_by(id=session['user_id']).first()
    # Ensure user has enough credits to play
    if user.balance >= game_cost:
        room = Room.query.filter_by(status='waiting').first()
        if room:
            # Join existing room
            session['room_id'] = room.id
            join_room(room.room_socket)
            room.status = 'playing'
            db.session.commit()

            create_game(user)

            emit('update-balance', user.balance)
            emit('update-log', message_enter.format(session['user_id']), 
                  to=room.room_socket)
            emit('found-game', message_starting, to=room.room_socket)
        else:
            # Create new room
            room = Room(room_socket=user.id, status='waiting')
            db.session.add(room)
            db.session.commit()
            join_room(room.room_socket)
            session['room_id'] = room.id

            create_game(user)

            emit('update-balance', user.balance)
            emit('play-waiting', {'message': message_join_queue,
                                  'waiting_message': waiting_message,
                                  'frequency': waiting_frequency})
    else:
        # Send alert about inability to play
        return emit('low-balance', message_low_balance)


def create_game(user):
    """Create game data and charge user for game fee"""
    game = Game(user_id=user.id, initial_balance=user.balance, 
                room_id=session['room_id'], start_time=datetime.now())
    db.session.add(game)
    db.session.commit()
    user.balance -= game_cost
    db.session.commit()


@socketio.on('cancel')
def cancel():
    """Allow user cancel waiting for second player"""
    room = Room.query.filter_by(id=session['room_id']).first()
    game = Game.query.filter_by(room_id=room.id, user_id=session['user_id']).first()
    user = User.query.filter_by(id=session['user_id']).first()

    # Undo game data and game fee
    db.session.delete(game)
    db.session.delete(room)
    user.balance += game_cost
    db.session.commit()
    session['room_id'] = None

    emit('update-balance', user.balance)
    emit('cancel-waiting', message_cancel)


@socketio.on('leave')
def leave():
    """Handle game finish"""
    room = Room.query.filter_by(id=session['room_id']).first()
    user = User.query.filter_by(id=session['user_id']).first()
    game = Game.query.filter_by(user_id=user.id, end_time=None).first()

    # Handle user's leave while second player made a move
    round = Round.query.filter_by(room_id=room.id, status='waiting').first()
    if round:
        db.session.delete(round)
        db.session.commit()

    leave_room(room.room_socket)

    room.status = 'finished'
    db.session.commit()

    # Choose the winner and finish the game
    if game.wins > game.loses:
        user.balance += win_credits
        db.session.commit()
    game.end_time = datetime.now()
    db.session.commit()
    session['room_id'] = None

    emit('update-balance', user.balance)
    emit('opponent-left', message_leave.format(session['user_id']), to=room.room_socket)


@socketio.on('disconnect')
def disconnect():
    """Handle user disconnect in different game states"""
    if session.get('room_id'):
        if session['room_id']:
            room = Room.query.filter_by(id=session['room_id']).first()
            if room.status == 'waiting':
                cancel()
            else:
                leave()


@socketio.on('game-choice')
def game_choice(choice):
    """Compare user's shape to opponent's shape"""
    opponent = Round.query.filter_by(room_id=session['room_id'], status='waiting').first()
    round = Round(choice=choice, room_id=session['room_id'], 
                      user_id=session['user_id'], user_socket=session['socket_id'])
    room = Room.query.filter_by(id=session['room_id']).first()
    emit('update-log', message_choice.format(choice))

    # Ensure second player made a move
    if opponent:
        # Compare decisions
        if choice == opponent.choice:
            opponent.status = 'draw'
            round.status = 'draw'
        elif choice == 'rock':
            if opponent.choice == 'paper':
                opponent.status = 'win'
                round.status = 'lose'
            else:
                opponent.status = 'lose'
                round.status = 'win'
        elif choice == 'paper':
            if opponent.choice == 'scissors':
                opponent.status = 'win'
                round.status = 'lose'
            else:
                opponent.status = 'lose'
                round.status = 'win'
        elif choice == 'scissors':
            if opponent.choice == 'rock':
                opponent.status = 'win'
                round.status = 'lose'
            else:
                opponent.status = 'lose'
                round.status = 'win'
        emit('receive-status', {'status': round.status, 
             'message': message_status_choice.format(opponent.choice, round.status)},
              to=session['socket_id'])
        emit('receive-status', {'status': opponent.status, 
             'message': message_status_choice.format(round.choice, opponent.status)},
              to=opponent.user_socket)
    else:
        # Wait for second player to move
        round.status = 'waiting'
        emit('update-log', message_ready.format(session['user_id']), to=room.room_socket)
        emit('receive-status', {'status': round.status, 'message': message_status_waiting},
             to=session['socket_id'])
    # Store single round in database
    db.session.add(round)
    db.session.commit()


@socketio.on('update-score')
def score():
    """Update game score to every user in room"""
    room = Room.query.filter_by(id=session['room_id']).first()
    game = Game.query.filter_by(room_id=room.id, user_id=session['user_id']).first()
    rounds = Round.query.filter_by(room_id=session['room_id'], user_id=session['user_id'])

    wins = rounds.filter_by(status='win').count()
    loses = rounds.filter_by(status='lose').count()
    game.wins = wins
    game.loses = loses
    db.session.commit()

    emit('update-log', message_score.format(wins, loses), to=session['socket_id'])
