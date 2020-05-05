#!/usr/bin/env python3
from datetime import datetime
from collections import deque
from enum import Enum


class UserStatus(Enum):
    OFFLINE = 1
    ONLINE = 2

class UserRole(Enum):
    ADMIN = 1
    USER = 2

class ChannelType(Enum):
    CHANNEL = 1
    DM = 2

class User(object):
    """User"""
    def __init__(self,name,key):
        self.name = name
        self.key = key
        self.status = UserStatus.ONLINE
        self.role = UserRole.USER

    def setAdmin(self):
        self.role = UserRole.ADMIN

class Message(object):
    """A chat message."""

    def __init__(self, display_name, message_text):
        self.name = display_name
        self.text = message_text
        self.date = datetime.now().strftime('%I:%M %p')


class Channel(object):
    """A messaging channel.

    A channel stores a maximum of 100 messages, and if new messages are
    added the oldest ones will be deleted.
    """

    def __init__(self, channel_name,channel_type=ChannelType.CHANNEL):
        self.name = channel_name
        self.channel_type = channel_type
        self.messages = deque(maxlen=100)

    def addMessage(self, message):
        """Add a message to channel."""
        self.messages.append(message)

    def getMessages(self):
        """Get list of previous messages"""
        return self.messages


class Server(object):
    """
    A server Has a list of user and channel
    """

    def __init__(self,name,key):
        self.name = name
        self.key = key
        self.channel_list = []
        self.user_list    = []

    def addChannel(self,channel):
        """Append a channel to the list."""
        self.channel_list.append(channel)

    def getChannel(self,channel_name):
        """Return a channel given the channel name."""
        names = parse_channel(channel_name)
        for channel in self.channel_list:
            for name in names:
                if name == channel.name:
                    return channel
        return None

    def getChannelNames(self):
        """Return list of channel names."""
        return [channel.name for channel in self.channel_list if channel.channel_type == ChannelType.CHANNEL]

    def getUserNames(self):
        """Returns the usernames"""
        return [user.name for user in self.user_list]

    def addUser(self,user):
        self.user_list.append(user)
        user_names = self.getUserNames()
        for user_name in user_names:
            dm = Channel("{}:{}".format(user.name,user_name),ChannelType.DM)
            self.addChannel(dm)


    def validateUser(self,name,key):
        for user in self.user_list:
            if user.name == name and user.key == key:
                return user
        return None

class ServerList(object):
    """
    List of available servers
    """

    def __init__(self):
        self.list = []

    def addServer(self,server):
        self.list.append(server)

    def getServer(self,server_key):
        """Return a server given the server name."""
        for server in self.list:
            if server.key == server_key:
                return server
        return None

def parse_channel(channel):
    if ":" in channel:
        sp = channel.split(":")
        return [sp[0] + ":" + sp[1], sp[1] + ":" + sp[0]]
    else:
        return [channel]
