from src import create_app
from src import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")
