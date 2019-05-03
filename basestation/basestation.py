from network import LoRa
import socket
import time
from utils.utils import Packet, MessageType, SensorType

''' A wireless sensor network basestation
    designed to run on a LoPy
'''

LORA_FREQUENCY = 869000000
lora = LoRa(mode=LoRa.LORA)
ALL_SENSORS = [SensorType.TEMP, SensorType.HUMID, SensorType.AIR_QUAL, SensorType.PRESS]

def log_print(msg):
    print(msg)

class Node():
    ''' A node on the network that operates a number of sensors
    '''
    def __init__(self, id, frequency=LORA_FREQUENCY, sensors_available=ALL_SENSORS):
        self.id = id
        self.frequency = frequency
        self.sensors_available = sensors_available

class Basestation():
    ''' The basestation (master) designed to run on a LoPy
    '''

    def __init__(self, nodes):
        self.nodes = [
            Node(1)
        ]
        self.id = 0
        self.available_data = {}

    def open_socket(self):
        self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

    def join_request(self, pkt):
        id = pkt.src_id

        ids = map(lambda n: n.id, self.nodes)
        if id in ids:
            log_print('Node join failed, ID %d already known' % id)
            return False

        # Add node to list
        node_sensors = self.decode_available_data(pkt.payload)
        node = Node(id,sensors_available=node_sensors)
        self.nodes.append(node)
        response = Packet.createJoinResponsePacket(self.id)
        response = Packet.encode_packet(response)
        self.s.send(response)
        print("Sent join acknowledgement")


    def decode_available_data(self, data):
        if len(data) < 3:
            log_print('Cannot decode available data with less than 3 bytes')
            return False

        available = []

        if data[0] == '1':
            available.append(SensorType.TEMP)
        if data[1] == '1':
            available.append(SensorType.HUMID)
        if data[2] == '1':
            available.append(SensorType.AIR_QUAL)
        if data[3] == '1':
            available.append(SensorType.PRESS)


        return available

    def record_sensor_data(self, data):
        # first byte of the payload is the sensor type
        sensor_type = data[0]
        # rest of the payload is the data
        value = data[1:]
        # store
        print('Sensor type: %d, Value: %d' % (sensor_type, value))

    def start(self):
        print("Opening socket..")
        self.open_socket()

        # nodes must join within 60 seconds of basestation activation
        print("Looking for connections...")
        self.s.setblocking(False)
        t_end = time.time() + 190
        while time.time() < t_end:
            while True:
                rx = self.s.recv(256)
                if rx:
                    print(rx)
            # rx is a bit stream
            if rx:
                print(rx)
                pkt = Packet.decode_packet(rx)
                print(pkt.type, pkt.src_id )
                if pkt.type == MessageType.JOIN_REQUEST:
                    print("Device found!")
                    self.join_request(pkt)
        print("Polling for data...")
        # main control loop
        while True:

            # cycle through the sensors and find equipped nodes for each
            for sensor_type in ALL_SENSORS:
                print('Getting ', sensor_type , ' data...')
                for node in range(0,self.nodes):
                    # check if the node supports the sensor type
                    time.sleep(5)
                    print('Polling node with id = ', node.id , '...')

                    if sensor_type in node.sensors_available:
                        # create packet
                        pkt = Packet.create_sensor_request(node.id, sensor_type)
                        pkt = Packet.encode_packet(pkt)
                        # set blocking to avoid receiving whilst sending
                        self.s.setblocking(True)
                        self.s.send(pkt)
                        # wait for response before doing anything else
                        rx, port = self.s.recvfrom(256)
                        # process response
                        if rx:
                            pkt = Packet.decode_packet(rx)

                            if pkt.type == MessageType.SENSOR_RESPONSE:
                                self.record_sensor_data(pkt)
                            else:
                                print(rx)
                                #log_print('Received a packet of type %d but expected Sensor Response (%d)' % (pkt.type, MessageType.SENSOR_RESPONSE))
def main():
    base = Basestation([])
    base.start()

main()
