import os
from eventlet import listen, wsgi
from square.app import app

wsgi.server(listen(('0.0.0.0', 8080)), app)
