# DSA Multiplayer Quiz

A real-time multiplayer quiz application where friends can compete against each other in Data Structures and Algorithms questions.

## 🚀 Features

- **Real-Time Multiplayer**: Join rooms with friends and play synchronously.
- **Dynamic Leaderboard**: See live updates of scores and rankings (hidden until the end!).
- **Timed Questions**: Challenge yourself with time-per-question limits.
- **Randomized Questions**: Every game pulls from a pool of DSA topics ensuring a fresh experience.
- **Results Page**: Detailed breakdown of scores and rankings at the end of the match.
- **Modern UI**: Polished, responsive design with glassmorphism aesthetics.

## 🛠️ Tech Stack

- **Backend**: Python (Flask, Flask-SocketIO)
- **Frontend**: HTML5, CSS3, JavaScript (Socket.IO Client)
- **Concurrency**: Gevent

## 📂 File Structure

```
dsa-quiz/
├── app.py              # Main Flask application and server logic
├── requirements.txt    # Project dependencies
├── static/             # Static assets
│   ├── style.css       # Global styles and themes
│   └── room.js         # Client-side game logic
└── templates/          # HTML templates
    ├── index.html      # Home page (Create/Join room)
    ├── room.html       # Game room interface
    └── results.html    # Final results page
```

## ⚙️ Installation & Setup

1.  **Prerequisite**: Ensure you have Python installed.

2.  **Install Dependencies**:
    Open a terminal in the project folder and run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**:
    ```bash
    python app.py
    ```

4.  **Access the Game**:
    Open your browser and navigate to:
    `http://localhost:5000`

## 🎮 How to Play with Friends

1.  **Host a Game**:
    *   Enter your username.
    *   Set the game duration (seconds per question).
    *   Click "Create Room".
    *   Share the **Room Code** (displayed at the top) with your friends.

2.  **Join a Game**:
    *   Open the app on another tab or computer (on the same network).
    *   Enter your username and the **Room Code**.
    *   Click "Join Room".

3.  **Start & Play**:
    *   Once everyone is in, the Host clicks "Start Quiz".
    *   Answer the questions before the time runs out!
    *   Results will be revealed automatically at the end.

## 📝 Notes
- To play across different devices on the same WiFi, use your computer's local IP address (e.g., `http://192.168.1.X:5000`) instead of `localhost`.
