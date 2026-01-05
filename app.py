from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dsa-quiz-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global in-memory storage for all rooms
rooms = {}

# Predefined DSA questions pool
QUESTIONS = [
    {
        "id": 1,
        "question": "What is the time complexity of binary search?",
        "type": "mcq",
        "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        "correct_answer": "O(log n)"
    },
    {
        "id": 2,
        "question": "Which data structure uses LIFO principle?",
        "type": "mcq",
        "options": ["Queue", "Stack", "Tree", "Graph"],
        "correct_answer": "Stack"
    },
    {
        "id": 3,
        "question": "What is the worst case time complexity of QuickSort?",
        "type": "mcq",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
        "correct_answer": "O(n^2)"
    },
    {
        "id": 4,
        "question": "In a max heap, the parent node is always greater than or equal to its children.",
        "type": "mcq",
        "options": ["True", "False"],
        "correct_answer": "True"
    },
    {
        "id": 5,
        "question": "What is the space complexity of merge sort?",
        "type": "mcq",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "correct_answer": "O(n)"
    }
]

def generate_room_code():
    """Generate a unique 6-digit room code"""
    while True:
        code = str(random.randint(100000, 999999))
        if code not in rooms:
            return code

def calculate_score(time_taken, duration, is_correct):
    """
    Calculate score based on correctness and speed
    Correct answer: max 1000 points, decreasing with time
    Wrong answer: 0 points
    """
    if not is_correct:
        return 0
    
    # Score decreases linearly from 1000 to 100 based on time taken
    # Faster submissions get higher scores
    max_score = 1000
    min_score = 100
    
    if time_taken >= duration:
        return 0
    
    score = max_score - ((max_score - min_score) * (time_taken / duration))
    return int(score)

def generate_leaderboard(room_code):
    """
    Generate sorted leaderboard for a room
    Sorted by: 1) score (desc), 2) time_taken (asc)
    """
    if room_code not in rooms:
        return []
    
    room = rooms[room_code]
    submissions = room.get('submissions', {})
    
    leaderboard = []
    for username, submission_data in submissions.items():
        leaderboard.append({
            'username': username,
            'score': submission_data['score'],
            'time_taken': submission_data['time_taken'],
            'is_correct': submission_data['is_correct']
        })
    
    # Sort by score (descending), then by time_taken (ascending)
    leaderboard.sort(key=lambda x: (-x['score'], x['time_taken']))
    
    return leaderboard

@app.route('/')
def index():
    """Serve the landing page"""
    return render_template('index.html')

@app.route('/room/<room_code>')
def room_page(room_code):
    """Serve the room page"""
    return render_template('room.html', room_code=room_code)

@app.route('/results/<room_code>')
def results_page(room_code):
    """Serve the results page"""
    return render_template('results.html', room_code=room_code)

@socketio.on('create_room')
def handle_create_room(data):
    """
    Create a new room with unique code
    Client sends: {username: str, duration: int}
    """
    username = data.get('username', 'Anonymous')
    duration = data.get('duration', 60)  # Default 60 seconds
    
    # Generate unique room code
    room_code = generate_room_code()
    
    # Select a random question for this room
    question = random.choice(QUESTIONS)
    
    # Initialize room data
    rooms[room_code] = {
        'host': username,
        'players': [username],
        'question': question,
        'start_time': None,
        'duration': duration,
        'submissions': {},
        'quiz_started': False
    }
    
    # Join the socket room
    join_room(room_code)
    
    # Send room code back to creator
    emit('room_created', {
        'room_code': room_code,
        'username': username,
        'is_host': True
    })

@socketio.on('join_room')
def handle_join_room(data):
    """
    Join an existing room
    Client sends: {username: str, room_code: str}
    """
    username = data.get('username', 'Anonymous')
    room_code = data.get('room_code', '')
    
    # Validate room exists
    if room_code not in rooms:
        emit('join_error', {'message': 'Room does not exist'})
        return
    
    room = rooms[room_code]
    
    # Check if username is already in room (Reconnect logic)
    if username in room['players']:
        join_room(room_code)
        
        emit('room_joined', {
            'room_code': room_code,
            'username': username,
            'is_host': (username == room['host'])
        })

        # Send current player list to reconnected user
        emit('player_list_update', {
            'players': room['players']
        })
        
        # If quiz is active, send state to reconnected user
        if room['quiz_started']:
            emit('quiz_started', {
                'question': room['question'],
                'start_time': room['start_time'],
                'duration': room['duration']
            })
            
        return
    
    # Check if quiz already started (block new players)
    if room['quiz_started']:
        emit('join_error', {'message': 'Quiz already started'})
        return
    
    # Add new player to room
    room['players'].append(username)
    join_room(room_code)
    
    # Notify user they joined successfully
    emit('room_joined', {
        'room_code': room_code,
        'username': username,
        'is_host': False
    })
    
    # Broadcast updated player list to all in room
    emit('player_list_update', {
        'players': room['players']
    }, room=room_code)

@socketio.on('start_quiz')
def handle_start_quiz(data):
    """
    Start the quiz (host only)
    Records server timestamp and broadcasts to all players
    Client sends: {room_code: str, username: str}
    """
    room_code = data.get('room_code', '')
    username = data.get('username', '')
    
    # Validate room exists
    if room_code not in rooms:
        emit('error', {'message': 'Room does not exist'})
        return
    
    room = rooms[room_code]
    
    # Validate host
    if room['host'] != username:
        emit('error', {'message': 'Only host can start the quiz'})
        return
    
    # Validate quiz not already started
    if room['quiz_started']:
        emit('error', {'message': 'Quiz already started'})
        return
    
    # Record server start time
    room['start_time'] = time.time()
    room['quiz_started'] = True
    
    # Broadcast quiz start to all players in room
    emit('quiz_started', {
        'question': room['question'],
        'start_time': room['start_time'],
        'duration': room['duration']
    }, room=room_code)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """
    Handle answer submission with server-side validation
    Client sends: {room_code: str, username: str, answer: str}
    """
    room_code = data.get('room_code', '')
    username = data.get('username', '')
    answer = data.get('answer', '')
    
    # Validate room exists
    if room_code not in rooms:
        emit('submission_error', {'message': 'Room does not exist'})
        return
    
    room = rooms[room_code]
    
    # Validate quiz has started
    if not room['quiz_started'] or room['start_time'] is None:
        emit('submission_error', {'message': 'Quiz has not started'})
        return
    
    # Validate user hasn't already submitted
    if username in room['submissions']:
        emit('submission_error', {'message': 'You have already submitted'})
        return
    
    # Calculate time taken
    submission_time = time.time()
    time_taken = submission_time - room['start_time']
    
    # Validate submission is within time limit
    if time_taken > room['duration']:
        emit('submission_error', {'message': 'Time expired'})
        return
    
    # Check if answer is correct
    correct_answer = room['question']['correct_answer']
    is_correct = (answer.strip() == correct_answer.strip())
    
    # Calculate score
    score = calculate_score(time_taken, room['duration'], is_correct)
    
    # Store submission
    room['submissions'][username] = {
        'answer': answer,
        'time_taken': round(time_taken, 2),
        'is_correct': is_correct,
        'score': score,
        'submission_time': submission_time
    }
    
    # Confirm submission to user
    emit('submission_confirmed', {
        'time_taken': round(time_taken, 2),
        'is_correct': is_correct,
        'score': score
    })
    
    # Generate and broadcast updated leaderboard to all players
    leaderboard = generate_leaderboard(room_code)
    emit('leaderboard_update', {
        'leaderboard': leaderboard
    }, room=room_code)

@socketio.on('request_leaderboard')
def handle_request_leaderboard(data):
    """
    Send current leaderboard to requesting user
    Client sends: {room_code: str}
    """
    room_code = data.get('room_code', '')
    
    if room_code not in rooms:
        emit('error', {'message': 'Room does not exist'})
        return
    
    leaderboard = generate_leaderboard(room_code)
    emit('leaderboard_update', {'leaderboard': leaderboard})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    # In production, would track user sessions and clean up
    # For MVP, keeping it simple with no cleanup
    pass

if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    print("Starting server on http://localhost:5000")
    server.serve_forever()