// Initialize socket connection
// Connect explicitly to localhost:5000 where the Flask server is running
const socket = io('http://localhost:5000');

// Get user data from sessionStorage
const username = sessionStorage.getItem('username');
const roomCode = sessionStorage.getItem('room_code');
const isHost = sessionStorage.getItem('is_host') === 'true';

// Redirect to home if no session data
if (!username || !roomCode) {
    window.location.href = '/';
}

// Get DOM elements
const roomCodeDisplay = document.getElementById('room-code-display');
const usernameDisplay = document.getElementById('username-display');
const waitingArea = document.getElementById('waiting-area');
const quizArea = document.getElementById('quiz-area');
const leaderboardSection = document.getElementById('leaderboard-section');
const playerList = document.getElementById('player-list');
const hostControls = document.getElementById('host-controls');
const startQuizBtn = document.getElementById('start-quiz-btn');
const timerDisplay = document.getElementById('timer-display');
const questionText = document.getElementById('question-text');
const mcqOptions = document.getElementById('mcq-options');
const textAnswer = document.getElementById('text-answer');
const answerInput = document.getElementById('answer-input');
const submitBtn = document.getElementById('submit-btn');
const submissionStatus = document.getElementById('submission-status');
const leaderboardBody = document.getElementById('leaderboard-body');
const errorMessage = document.getElementById('error-message');

// Quiz state
let quizStartTime = null;
let quizDuration = null;
let timerInterval = null;
let selectedAnswer = null;
let hasSubmitted = false;

// Display user and room info
roomCodeDisplay.textContent = roomCode;
usernameDisplay.textContent = username;

// Show host controls if user is host
if (isHost) {
    hostControls.style.display = 'block';
}

// Utility function to show error
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// Utility function to show submission status
function showSubmissionStatus(message, isSuccess) {
    submissionStatus.textContent = message;
    submissionStatus.className = 'submission-status ' + (isSuccess ? 'success' : 'error');
}

// Update player list
function updatePlayerList(players) {
    playerList.innerHTML = '';
    players.forEach(player => {
        const li = document.createElement('li');
        li.textContent = player;
        if (player === username) {
            li.textContent += ' (You)';
        }
        playerList.appendChild(li);
    });
}

// Start quiz button handler
startQuizBtn.addEventListener('click', () => {
    startQuizBtn.disabled = true;
    startQuizBtn.textContent = 'Starting...';

    socket.emit('start_quiz', {
        room_code: roomCode,
        username: username
    });
});

// Display question
function displayQuestion(question) {
    questionText.textContent = question.question;

    if (question.type === 'mcq') {
        // Show MCQ options
        mcqOptions.style.display = 'block';
        textAnswer.style.display = 'none';

        mcqOptions.innerHTML = '';
        question.options.forEach(option => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = option;
            btn.addEventListener('click', () => {
                // Remove selected class from all options
                document.querySelectorAll('.option-btn').forEach(b => {
                    b.classList.remove('selected');
                });
                // Add selected class to clicked option
                btn.classList.add('selected');
                selectedAnswer = option;
            });
            mcqOptions.appendChild(btn);
        });
    } else {
        // Show text input
        mcqOptions.style.display = 'none';
        textAnswer.style.display = 'block';
        answerInput.value = '';
    }
}

// Update timer display
function updateTimer() {
    if (!quizStartTime || !quizDuration) return;

    const now = Date.now() / 1000; // Convert to seconds
    const elapsed = now - quizStartTime;
    const remaining = Math.max(0, quizDuration - elapsed);

    // Update display
    timerDisplay.textContent = Math.ceil(remaining);

    // Change color based on remaining time
    timerDisplay.className = 'timer';
    if (remaining <= 10) {
        timerDisplay.classList.add('danger');
    } else if (remaining <= 30) {
        timerDisplay.classList.add('warning');
    }

    // Stop timer when time is up
    if (remaining <= 0) {
        clearInterval(timerInterval);
        timerDisplay.textContent = '0';
        submitBtn.disabled = true;

        // Disable all option buttons
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.disabled = true;
        });

        if (!hasSubmitted) {
            showSubmissionStatus('Time expired! No submission recorded.', false);
        }

        // Redirect to results page after a short delay
        setTimeout(() => {
            window.location.href = `/results/${roomCode}`;
        }, 3000);
    }
}

// Submit answer handler
submitBtn.addEventListener('click', () => {
    // Get answer based on question type
    let answer;
    if (mcqOptions.style.display !== 'none') {
        // MCQ question
        answer = selectedAnswer;
        if (!answer) {
            showError('Please select an option');
            return;
        }
    } else {
        // Text question
        answer = answerInput.value.trim();
        if (!answer) {
            showError('Please enter an answer');
            return;
        }
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    hasSubmitted = true;

    // Disable all option buttons
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.disabled = true;
    });

    // Disable text input
    if (answerInput) {
        answerInput.disabled = true;
    }

    // Emit submit answer event
    socket.emit('submit_answer', {
        room_code: roomCode,
        username: username,
        answer: answer
    });
});

// Socket event handlers

// Player list update
socket.on('player_list_update', (data) => {
    updatePlayerList(data.players);
});

// Quiz started
socket.on('quiz_started', (data) => {
    // Store quiz data
    quizStartTime = data.start_time;
    quizDuration = data.duration;

    // Hide waiting area, show quiz area
    waitingArea.style.display = 'none';
    quizArea.style.display = 'block';

    // Display question
    displayQuestion(data.question);

    // Start timer
    timerInterval = setInterval(updateTimer, 100); // Update every 100ms for smooth countdown
    updateTimer();
});

// Submission confirmed
socket.on('submission_confirmed', (data) => {
    submitBtn.textContent = 'Submitted';

    // Don't show results yet, just confirmation
    const message = "Answer submitted! Results will be shown at the end.";
    showSubmissionStatus(message, true);

    // Don't show leaderboard section here anymore
});

// Submission error
socket.on('submission_error', (data) => {
    showError(data.message);
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Answer';
    hasSubmitted = false;
});

// Leaderboard update
// Leaderboard update
socket.on('leaderboard_update', (data) => {
    // We receive updates but do not display them during the game
    // The leaderboard will only be shown on the results page
});

// Join error
socket.on('join_error', (data) => {
    showError(data.message);
    // Optionally redirect back to home after a delay
    setTimeout(() => {
        window.location.href = '/';
    }, 3000);
});

// Error handler
socket.on('error', (data) => {
    showError(data.message);
});

// Join the room on connection
socket.on('connect', () => {
    // If user refreshes the page, rejoin the room
    socket.emit('join_room', {
        username: username,
        room_code: roomCode
    });
});

socket.on('connect_error', (err) => {
    console.error('Connection failed:', err);
    showError('Connection to server lost. Reconnecting...');
});