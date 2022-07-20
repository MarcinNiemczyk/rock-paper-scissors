## Overview
Websocket game with classic rock-paper-scissors rules and interactive interface. <br>
Application is created for multiplayer purposes, user can only play online or through LAN.


### Demo
Demo version: http://rps-online-demo.herokuapp.com/

## Background

### User authentication
Application doesn't allow to create accounts, each session is a new player.

### Gameplay
User can start a game by clicking a button. System will try to find an opponent, and if there is not, it will create a new room with current player id, then user need to wait for opponent. If there is already room with waiting status, user joins and game starts automatically.

### Logs
Log system allows to display necessary information for the user such as current game score or waiting for player information. Every game room stores information about it's own socket id and connected users sockets, so logs can be displayed individually. All log messages can be modified in ```settings.py```.


### Credits
Player starts with set initial balance and can add more credits only if his balance is equal to zero. It is also possible to withdraw credits. Each game costs 3 credits, win adds 4 credits. Every value can be modified in ```settings.py```.


### Statistics
Game keeps track of every game and round statistics. User can access to daily summary view with win-lose ratio, earned credits or total played time and see detailed games below like score, played time, starting time, balance etc. It is possible to filter by date and select statistics from the past.


### Technologies
- Flask
- SocketIO
- SQLAlchemy
- Docker
- Docker Compose
- JavaScript
- HTML
- CSS
