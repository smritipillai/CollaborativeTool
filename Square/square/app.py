import json
import os
import uuid
from collections import deque
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for, session, abort,send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room

from .model import *
from .fourm import  *

app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex
socketio = SocketIO(app)

server_list = ServerList()

TRASH = "/tmp/files"
Path(TRASH).mkdir(parents=True, exist_ok=True)

# Testing
# server = Server("test","test")
# user = User("admin","admin")
# user1 = User("user","user")
# user.setAdmin()
# server.addUser(user)
# server.addUser(user1)
# channel = Channel("public")
# server.addChannel(channel)
# server_list.addServer(server)


@app.route('/server', methods=['GET', 'POST'])
def createServer():
    if request.method == 'POST':
        server_name  = request.form.get('server-name')
        server_key   = uuid.uuid4().hex
        server = Server(server_name,server_key)
        user_name    = request.form.get('user-name')
        key     = request.form.get('user-key')
        user  = User(user_name,key)
        user.setAdmin()
        server.addUser(user)
        public_channel = Channel("public")
        server.addChannel(public_channel)
        server_list.addServer(server)

        session['user'] = user_name
        session['user-key'] = key
        session['server'] = server_key
        session['channel-name'] = "public"

        return redirect(url_for("server",server_key=server_key))

    elif request.method == 'GET':
        return render_template('create_server.html')

@app.route('/server/<string:server_key>',endpoint='server')
def joinServer(server_key):
    server = server_list.getServer(server_key)
    if server:
        user = server.validateUser(session.get("user",""),
                                   session.get("user-key",""))
        if user:
            return render_template('server.html',user=user.name)
        else:
            return redirect(url_for("join_server",server_key=server_key))
    abort(404)

@app.route('/server/<string:server_key>/join',methods=['POST','GET'],endpoint="join_server")
def joinServer(server_key):
    server = server_list.getServer(server_key)
    if server:
        if request.method == "POST":
            username   = request.form.get('user-name')
            key    = request.form.get('user-key')
            user = server.validateUser(username,key)
            if not user:
                user = User(username,key)
                server.addUser(user)
            session['user'] = user.name
            session['user-key'] = user.key
            session['server'] = server_key
            session['channel-name'] = "public"
            return redirect(url_for("server",server_key=server_key))
        elif request.method == "GET":
            return render_template('join_server.html',server_name=server.name)
    abort(404)

@app.route('/uploader', methods = ['POST'])
def uploadFile():
    server_key = session.get('server','')
    server = server_list.getServer(server_key)
    if server:
        print(session)
        user = session['user']
        channel_name = session['channel-name']
        if request.method == 'POST':
            f = request.files['file']
            file_name = uuid.uuid4().hex
            message_text = "<a href=\"{}/{}\">{}</a>".format(request.base_url,file_name,file_name)

            message = Message(user, message_text)
            channel = server.getChannel(channel_name)
            if channel:
                f.save(TRASH + "/" + file_name)
                channel.addMessage(message)
                socketio.emit('message', {'user': user,'message': message_text}, room=(channel_name + server_key))

            return redirect(url_for("server",server_key=server_key))
    abort(404)

@app.route('/uploader/<string:filename>')
def downloadFile(filename):
    print(filename)
    try:
        return send_from_directory(TRASH, filename=filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/')
def index():
    return "Hello World"

@socketio.on('create-channel')
def createChannel(data):
    server_key = session['server']
    channel_name = data['channelName']
    server = server_list.getServer(server_key)
    if server:
        channel = Channel(channel_name)
        server.addChannel(channel)
        emit('channel-list',server.getChannelNames(),room=server_key)

@socketio.on("join")
def Join(data):
    server_key = session.get('server','')
    server = server_list.getServer(server_key)
    join_room(server_key)
    if server:
        emit('channel-list',server.getChannelNames(),room=server_key)
        user_name = server.getUserNames()
        emit('user-list', user_name,room=server_key)

@socketio.on('join-channel')
def joinChannel(data):
    server_key = session.get('server',"")
    server = server_list.getServer(server_key)
    if server:
        channels = parse_channel(session.get('channel-name',""))
        for channel in channels:
            if channel:
                leave_room(channel + server_key)

        if server:
            channel_name = data['channelName']
            channel = server.getChannel(channel_name)
            if channel:
                session['channel-name'] = channel_name
                channels = parse_channel(channel_name)
                for c in channels:
                    join_room(c + server_key)
                emit('channel-list',server.getChannelNames(),room=server_key)
                messages = [{"user": x.name, "message": x.text} for x in channel.getMessages()]
                emit('load-message',messages,room=server_key)

@socketio.on('message')
def handle_message(data):
    user = session['user']
    server_key = session['server']
    channel_name = data['channelName']
    message_text = data['message']

    message = Message(user, message_text)
    server = server_list.getServer(server_key)
    if server:
        channel = server.getChannel(channel_name)
        if channel:
            channel.addMessage(message)
            emit('message', {'user': user,'message': message_text}, room=(channel_name + server_key))

if __name__ == '__main__':

    socketio.run(app)
