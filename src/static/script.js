function displayLog(message) {
  const div = document.createElement('div')
  div.textContent = message
  var logs = document.querySelector('.logs-container')
  logs.append(div)
  // Automatically scroll logs
  logs.scrollTop = logs.scrollHeight
}

function foundGame(message) {
  // If player was waiting, end waiting log loop
  if (interval) {
    clearInterval(interval)
  }
  var playButton = document.getElementById('playButton')
  var playLabel = document.getElementById('playLabel')
  var leaveButton = document.getElementById('leaveRoom')
  var game = document.querySelector('.game')
  playButton.classList.remove('cancel')
  playButton.innerHTML = 'START GAME'
  playButton.classList.add('hidden')
  playLabel.classList.add('hidden')
  leaveButton.classList.remove('hidden')
  game.classList.remove('hidden')
  displayLog(message)
}

function leaveRoom() {
  var playButton = document.getElementById('playButton')
  var playLabel = document.getElementById('playLabel')
  var leaveButton = document.getElementById('leaveRoom')
  var game = document.querySelector('.game')
  leaveButton.classList.add('hidden')
  playButton.classList.remove('hidden')
  playLabel.classList.remove('hidden')
  game.classList.add('hidden')
}

function selectShape(select, deselect1, deselect2) {
  deselect1.classList.add('deselect')
  deselect2.classList.add('deselect')
  clicked = true
  socket.emit('game-choice', select.name)
}

function resetShapes(rock, paper, scissors) {
  socket.emit('update-score')
  rock.removeAttribute('class')
  paper.removeAttribute('class')
  scissors.removeAttribute('class')
  clicked = false
}

let interval
// Prevent user for multiple clicks before initiated function ends
let clicked = false

// Handle mobile menu
document.querySelector('.toggle-menu').onclick = () => {
  document.querySelector('nav').classList.toggle('active')
}


const socket = io.connect();

if (window.location.pathname == '/') {
  socket.on('connect', () => {
    socket.emit('connection', socket.id)
  
    const playButton = document.getElementById('playButton')
    const leaveButton = document.getElementById('leaveRoom')
  
    playButton.addEventListener('click', () => {
      if (clicked == false) {
        // Ensure play button's state
        if (playButton.classList.contains('cancel')) {
          socket.emit('cancel')
          clicked = true
        } else {
          socket.emit('play')
          clicked = true
        }
      }
    })
  
    socket.on('update-log', log => {
      displayLog(log)
    })
  
    socket.on('play-waiting', data => {
      displayLog(data.message)
      playButton.innerHTML = 'CANCEL'
      playButton.classList.add('cancel')
      clicked = false
      displayLog(data.waiting_message)
      interval = setInterval(function() {
        displayLog(data.waiting_message)
      }, data.frequency)
    })
  
    socket.on('cancel-waiting', message => {
      clearInterval(interval)
      displayLog(message)
      playButton.innerHTML = 'START GAME'
      playButton.classList.remove('cancel')
      clicked = false
    })
  
    socket.on('found-game', message => {
      foundGame(message)
    })
  
    leaveButton.addEventListener('click', () => {
      socket.emit('leave')
      leaveRoom()
    })
  
    socket.on('opponent-left', message => {
      displayLog(message)
      socket.emit('leave')
      leaveRoom()
    })
  
    socket.on('disconnect', () => {
      socket.emit('disconnect')
    })

    socket.on('low-balance', message => {
      displayLog(message)
      clicked = false
    })
  
    socket.on('update-balance', balance => {
      var credits = document.getElementById('credits')
      credits.innerHTML = 'Credits (' + balance +')'
    })

    // Game state
    const rock = document.getElementById('rock')
    const paper = document.getElementById('paper')
    const scissors = document.getElementById('scissors')
  
    rock.addEventListener('click', () => {
      selectShape(rock, paper, scissors)
    })
  
    paper.addEventListener('click', () => {
      selectShape(paper, rock, scissors)
    })
  
    scissors.addEventListener('click', () => {
      selectShape(scissors, paper, rock)
    })
  
    socket.on('receive-status', data => {
      if (data.status != 'waiting') {
        displayLog(data.message)
        resetShapes(rock, paper, scissors)
      }
    })
  })
}


