from client import Client
from server import Server
from aiohttp import web
from streamer import StreamerMessage, HOST, PORT
from threading import Thread
import random
import time
from midi_socket import MidiSocket

def activate_server():
    """
    activates socketio server in self.host and self.port.
    """
    app = web.Application()
    server = Server(app)
    web.run_app(app, host=HOST, port=PORT)

if __name__ == "__main__":
    midi_socket = MidiSocket()

    # TODO: check if sending ints cause errors.
    sensor_ids_and_data = [["1_a", 1], ["1_b", 4]]
    idx = 0
    while True:
        for (sensor_id, channel) in sensor_ids_and_data:
            midi_socket.emit(channel, random.randint(0, 127))
            midi_socket.emit(channel+1, random.randint(0, 127))
            midi_socket.emit(channel+2, random.randint(0, 127))
            time.sleep(0.016)

