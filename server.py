import socketio

host, port = "localhost", 3001

class Server:
    """
    This is the client class that will activate update_values method on
    'recieved_data' event.
    """
    def __init__(self, app):
        self.host = host
        self.port = port
        self.sio = socketio.AsyncServer()
        self.sio.attach(app)
        self.sio.on('send-data', self._on_message)

    async def _on_message(self, sid, data):
        await self.sio.emit('recieve-data', data)    
