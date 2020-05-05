import json
import os
import uuid
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for, session, abort
from flask_socketio import SocketIO, emit, join_room, leave_room

from .model import *
from .fourm import  *

app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex
socketio = SocketIO(app)

server_list = ServerList()

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
            return redirect(url_for("server",server_key=server_key))
        elif request.method == "GET":
            return render_template('join_server.html',server_name=server.name)
    abort(404)


@app.route('/server/<string:server_key>/<string:channel_name>')
def joinChannel(server_key,channel_name):
    server = server_list.getServer(server_key)
    channel = server.getChannel(channel_name)
    if channel:
        session['channel'] = channel_name
        join_room(channel_name)
        return redirect(url_for("join_server",server_key=server_key))

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
        emit('channel-list',server.getChannelNames())

@socketio.on("join")
def Join(data):
    server_key = session.get('server','')
    server = server_list.getServer(server_key)
    if server:
        emit('channel-list',server.getChannelNames())
        user_name = server.getUserNames()
        emit('user-list', user_name)

@socketio.on('join-channel')
def joinChannel(data):
    server_key = session['server']
    server = server_list.getServer(server_key)
    channels = parse_channel(session.get('channelName',""))
    for channel in channels:
        leave_room(channel)

    if server:
        channel_name = data['channelName']
        channel = server.getChannel(channel_name)
        if channel:
            session['channelName'] = channel_name
            channels = parse_channel(channel_name)
            for c in channels:
                join_room(c)
            emit('channel-list',server.getChannelNames())
            messages = [{"user": x.name, "message": x.text} for x in channel.getMessages()]
            emit('load-message',messages)

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
            emit('message', {'user': user,'message': message_text}, room=channel_name)

if __name__ == '__main__':

    socketio.run(app)
