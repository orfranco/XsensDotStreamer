# Requires installation of the correct Xsens DOT PC SDK wheel through pip
# For example, for Python 3.9 on Windows 64 bit run the following command
# pip install xsensdot_pc_sdk-202x.x.x-cp39-none-win_amd64.whl

import time
from threading import Thread

import xsensdot_pc_sdk
from callback_handler import CallbackHandler
from client import Client
from server import Server
from aiohttp import web


class Streamer:
    def __init__(self, measurement_mode, output_rate, host, port):
        self.version = xsensdot_pc_sdk.XsVersion()
        xsensdot_pc_sdk.xsdotsdkDllVersion(self.version)
        print(f"Using Xsens DOT SDK version: {self.version.toXsString()}")
        self._create_connection_manager()
        self._attach_callback_handler()
        self.connectedDOTCount = 0
        self.measurement_mode = measurement_mode
        self.output_rate = output_rate
        self.deviceList = list()
        self.counters = dict()
        self.stream_flag = False
        self.host, self.port = host, port

        # initialize socketio for plugin:
        self.server_thread = Thread(target=self._activate_server)
        self.server_thread .daemon = True # for it to stop when main Thread stops.
        self.server_thread.start()
        self.client = Client(HOST, PORT)

    def _activate_server(self):
        """
        activates socketio server in self.host and self.port.
        """
        app = web.Application()
        self.server = Server(app)
        web.run_app(app, host=self.host, port=self.port)

    def _send_message(self, device, packet):
        """
        this callback will be activated each time a packet arrives from sensors.
        it will send the packet through the socketio in the correct format.
        :param device: the dot sensor who sent the packet.
        :param packet: the packet arrived from sensor.
        """
        if self.stream_flag: # send only when stream_flag is up.
            # count the number of packets from each sensor:
            if device.portInfo().bluetoothAddress() not in self.counters:
                self.counters[device.portInfo().bluetoothAddress()] = 0
            self.counters[device.portInfo().bluetoothAddress()] += 1
            #print(f"{device.portInfo().bluetoothAddress()}"
             #     f": {self.counters[device.portInfo().bluetoothAddress()]}")
            print(self.counters)

            # build and send message to plugin:
            address = device.portInfo().bluetoothAddress()
            euler_x = packet.orientationEuler().x()
            euler_y = packet.orientationEuler().y()
            euler_z = packet.orientationEuler().z()
            msg = f"Payload id 20 bleSensorData,{address}" \
                  f"\neuler_x:{euler_x}" \
                  f"\neuler_y:{euler_y}" \
                  f"\neuler_z:{euler_z}"
            self.client.emit(msg)

    def _create_connection_manager(self):
        self.manager = xsensdot_pc_sdk.XsDotConnectionManager()
        if self.manager is None:
            print("Manager could not be constructed, exiting.")
            exit(-1)

    def _attach_callback_handler(self):
        self.callback = CallbackHandler(self._send_message)
        self.manager.addXsDotCallbackHandler(self.callback)

    def start_scan(self, ms):
        """
        starts scanning for devices for ms/1000 seconds.
        """
        print(f"Scanning for devices for {ms // 1000} seconds")
        self.manager.enableDeviceDetection()
        self.connectedDOTCount = 0
        startTime = xsensdot_pc_sdk.XsTimeStamp_nowMs()
        while (not self.callback.errorReceived()) and (
                xsensdot_pc_sdk.XsTimeStamp_nowMs() - startTime <= ms):
            time.sleep(0.1)
            nextCount = len(self.callback.getDetectedDots())
            if nextCount != self.connectedDOTCount:
                print(f"Number of connected DOTs: {nextCount}. stopping scan in "
                      f"{(ms - (xsensdot_pc_sdk.XsTimeStamp_nowMs() - startTime)) // 1000} seconds")
                self.connectedDOTCount = nextCount
        self.manager.disableDeviceDetection()
        print("Stopped scanning for devices.")

        if len(self.callback.getDetectedDots()) == 0:
            print("No Xsens DOT device(s) found. Aborting.")
            exit(-1)
        self._set_sensors_settings()

    def _set_sensors_settings(self):
        """
        for each sensor, adds it to self.device_list, and sets it profile and Output rate.
        """
        self.deviceList = list()
        for portInfo in self.callback.getDetectedDots():
            # find device and add it to self.device_list:
            address = portInfo.bluetoothAddress()
            print(f"Opening DOT with address: @ {address}")
            if not self.manager.openPort(portInfo):
                print(f"Connection to Device {address} failed, retrying...")
                print(f"Device {address} retry connected:")
                if not self.manager.openPort(portInfo):
                    print(f"Could not open DOT. Reason: {self.manager.lastResultText()}")
                    continue

            device = self.manager.device(portInfo.deviceId())
            if device is None:
                continue

            self.deviceList.append(device)
            print(f"Found a device with Tag: {device.deviceTagName()} @ address: {address}")

            # set device profile:
            filterProfiles = device.getAvailableFilterProfiles()
            print("Available filter profiles:")
            for f in filterProfiles:
                print(f.label())

            print(f"Current profile: {device.onboardFilterProfile().label()}")
            if device.setOnboardFilterProfile("General"):
                print("Successfully set profile to General")
            else:
                print("Setting filter profile failed!")

            # set device output rate:
            print(f"Setting Output Rate to {self.output_rate}fps:")
            device.setOutputRate(self.output_rate)

    def start_streaming(self, ms=0):  # ms=0 is infinite time.
        print("Putting device into measurement mode.")
        for device in self.deviceList:
            if not device.startMeasurement(self.measurement_mode):
                print(
                    f"Could not put device into measurement mode. Reason: "
                    f"{self.manager.lastResultText()}")
                continue

        orientationResetDone = False
        self.stream_flag = True
        startTime = xsensdot_pc_sdk.XsTimeStamp_nowMs()
        while xsensdot_pc_sdk.XsTimeStamp_nowMs() - startTime < ms or ms == 0:
            # if self.callback.packetsAvailable():
            #     for device in self.deviceList:
            #         self.callback.getNextPacket(device.portInfo().bluetoothAddress())
            orientationResetDone = self._reset_heading_if_needed(orientationResetDone,
                                                                 startTime)
        self.end_streaming()

    def _reset_heading_if_needed(self, orientationResetDone, startTime):
        if not orientationResetDone and xsensdot_pc_sdk.XsTimeStamp_nowMs() - startTime > 5000:
            for device in self.deviceList:
                print(
                    f"\nResetting heading for device {device.portInfo().bluetoothAddress()}: ",
                    end="", flush=True)
                if device.resetOrientation(xsensdot_pc_sdk.XRM_Heading):
                    print("OK", end="", flush=True)
                else:
                    print(f"NOK: {device.lastResultText()}", end="", flush=True)
            print("\n", end="", flush=True)
            orientationResetDone = True
        return orientationResetDone

    def end_streaming(self):
        for device in self.deviceList:
            print(
                f"\nResetting heading to default for device {device.portInfo().bluetoothAddress()}: ",
                end="", flush=True)
            if device.resetOrientation(xsensdot_pc_sdk.XRM_DefaultAlignment):
                print("OK", end="", flush=True)
            else:
                print(f"NOK: {device.lastResultText()}", end="", flush=True)
        print("\n", end="", flush=True)

        print("\nStopping measurement...")
        for device in self.deviceList:
            if not device.stopMeasurement():
                print("Failed to stop measurement.")
            if not device.disableLogging():
                print("Failed to disable logging.")

        print("Closing ports...")
        self.manager.close()
        print("Successful exit.")
        self.stream_flag = False


OUTPUT_RATE = 60
MEASUREMENT_MODE = xsensdot_pc_sdk.XsPayloadMode_ExtendedEuler
HOST, PORT = "localhost", 3001
SCANNING_TIME = 8000
STREAMING_TIME = 0  # set to zero if you want infinite time.
if __name__ == "__main__":
    streamer = Streamer(MEASUREMENT_MODE, OUTPUT_RATE, HOST, PORT)
    streamer.start_scan(SCANNING_TIME)
    streamer.start_streaming(STREAMING_TIME)
