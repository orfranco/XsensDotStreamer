import mido
from mido import Message

MIDI_PORT = "OR MIDI 2"

class MidiSocket:
    def __init__(self): 
        self.output = mido.open_output(MIDI_PORT)

    def emit(self, channel, value):
        message = Message("control_change", control=channel, value=value)
        print("control_change: control:", channel, " , value:", value)
        self.output.send(message)

    def get_available_midi_ports():
        print("Available MIDI Output Ports:")
        for port in mido.get_output_names():
           print(port)

