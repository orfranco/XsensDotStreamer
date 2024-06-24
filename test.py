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

    # TODO: check if sending ints cause errors.
    sensor_ids_and_data = [["1_a", (60.0, 120.0, 180.0)], ["1_b", (240.0, 300.0, 359.0)]]
    while True:
        for (sensor_id, sensor_data) in sensor_ids_and_data:
            transition = random.randint(0, 3)
            streamer_msg = StreamerMessage(sensor_id, "10:00", sensor_data[0]+transition, sensor_data[1]+transition, sensor_data[2]+transition)
            json_msg = streamer_msg.to_json()
            client.emit(json_msg)
            print(json_msg)
            time.sleep(0.05)
