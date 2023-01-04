import socketio


class Client:
    """
    This is the client class that will activate update_values method on
    'recieved_data' event.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sio = socketio.Client()
        self.sio.connect(f'http://{self.host}:{self.port}')
        print(f"socketio connected to server in http://{self.host}:{self.port}!")

    def emit(self, msg):
        self.sio.emit('send-data', msg)
