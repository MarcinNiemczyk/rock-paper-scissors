from datetime import datetime, date, timedelta
from flask import (Blueprint, redirect, render_template, request, session, 
                   flash, url_for)
from sqlalchemy import extract
from src import db
from src.models import Game, User
from src.settings import *

views = Blueprint('views', __name__)

@views.route('/credits', methods=['GET', 'POST'])
def credits():
    """Display current balance and allow user to deposit 
       or withdraw credits"""
    user = User.query.filter_by(id=session['user_id']).first()

    if request.method == 'POST':
        if request.form.get('deposit'):
            # User can add 10 credits only if his balance is zero
            if user.balance == 0:
                user.balance = 10
                db.session.commit()
                flash(alert_deposit_success)
                return redirect(url_for('views.credits'))
            else:
                flash(alert_deposit_balance)
        # Withdraw to reset credits
        else:
            if user.balance <= 0:
                flash(alert_withdraw_balance)
            else:
                amount = user.balance
                user.balance = 0
                db.session.commit()
                flash(alert_withdraw_success.format(amount))
    return render_template('credits.html', balance=user.balance)


@views.route('/statistics', defaults={'year': date.today().year,
             'month': date.today().month, 'day': date.today().day}, 
              methods=['GET', 'POST'])
@views.route('/statistics/<int:year>/<int:month>/<int:day>', 
              methods=['GET', 'POST'])
def statistics(year, month, day):
    """Show user's statistics for selected date, 
       by default date is current day"""

    # Handle date change input
    if request.method == 'POST':
        formdate = request.form.get('date')
        selected_date = datetime.strptime(formdate, '%Y-%m-%d')
        year = selected_date.year
        month = selected_date.month
        day = selected_date.day
        return redirect(url_for('views.statistics', year=year, month=month, 
                                 day=day))
    
    user = User.query.filter_by(id=session['user_id']).first()
    games = Game.query.filter_by(user_id=user.id)
    # Apply date filter to query
    games = games.filter(extract('year', Game.start_time)==year)
    games = games.filter(extract('month', Game.start_time)==month)
    games = games.filter(extract('day', Game.start_time)==day).all()

    summary, detailed_games = get_stats(games)

    selected_date = f'{year}-{month}-{day}'
    selected_date = datetime.strftime(datetime.strptime(selected_date, 
                                      '%Y-%m-%d'), '%Y-%m-%d')

    return render_template('statistics.html', balance=user.balance, 
                           games=detailed_games, selected_date=selected_date, 
                           year=year, month=month, day=day, summary=summary)


def get_stats(games):
    """Return statistics as day's summary and list of single games"""
    summary = {
        'wins': 0,
        'loses': 0,
        'user_id': session['user_id'],
        'credits': 0,
        'time': timedelta(seconds=0)
    }

    # List of selected day games with details
    detailed_games = []

    for game in games:
        # Format rounds score for single game result
        score = str(game.wins) + ' - ' + str(game.loses)

        duration = game.end_time - game.start_time
        summary['time'] += duration

        # Compare single game score and calculate result 
        if game.wins == game.loses:
            status = 'draw'
            summary['credits'] -= 3
        elif game.wins > game.loses:
            status = 'win'
            summary['wins'] += 1
            summary['credits'] += 1
        else:
            status = 'lose'
            summary['loses'] += 1
            summary['credits'] -= 3

        formatted_duration = str(duration).split(".")[0]
        start_time = str(game.start_time).split(".")[0]

        single_game = {
            'status': status,
            'score': score,
            'user_id': game.user_id,
            'balance': game.initial_balance,
            'start_time': start_time,
            'duration': formatted_duration
        }

        detailed_games.append(single_game)

    # Format summary duration time not to display milliseconds
    summary['time'] = str(summary['time']).split(".")[0]

    return summary, detailed_games
