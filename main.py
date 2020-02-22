from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asr8pskZDATaXXA3Mg23'
socketio = SocketIO(app)

@app.route('/')
def sessions():
    return render_template('index.html')

@socketio.on('chat message')
def chat_message(msg, methods=['GET', 'POST']):
    socketio.emit('chat message', msg)

if __name__ == '__main__':
    socketio.run(app)
