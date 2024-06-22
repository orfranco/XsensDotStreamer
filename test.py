from client import Client
from server import Server
from aiohttp import web
from streamer import StreamerMessage, HOST, PORT
from threading import Thread
import random
import time

def activate_server():
    """
    activates socketio server in self.host and self.port.
    """
    app = web.Application()
    server = Server(app)
    web.run_app(app, host=HOST, port=PORT)

if __name__ == "__main__":
    # initialize socketio for plugin:
    server_thread = Thread(target=activate_server)
    server_thread .daemon = True # for it to stop when main Thread stops.
    server_thread.start()
    client = Client(HOST, PORT)

    sensor_ids = ["1_a"]
    while True:
        for sensor_id in sensor_ids:
            streamer_msg = StreamerMessage(sensor_id, "10:00", random.random()*360.0, random.random()*360.0, random.random()*360.0)
            json_msg = streamer_msg.to_json()
            client.emit(json_msg)
            print(json_msg)
            time.sleep(0.05)
