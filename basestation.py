from network import LoRa
import socket
import time

''' A wireless sensor network basestation
    designed to run on a LoPy
'''

LORA_FREQUENCY = 869525000
lora = LoRa(mode=LoRa.LORA, frequency = LORA_FREQUENCY)
def log_print(msg):
    print(msg)

''' Enum for the types of sensor available to the network
'''
class SensorType():
    TEMP = 0
    HUMID = 1
    AIR_QUAL = 2

''' Enum for the types of message that are produced
'''
class MessageType():
    JOIN = 0
    SENSOR_RESPONSE = 1
    SENSOR_REQUEST = 2

ALL_SENSORS = [SensorType.TEMP, SensorType.HUMID, SensorType.AIR_QUAL]

class Node():
    ''' A node on the network that operates a number of sensors
    '''
    def __init__(self, id, frequency=LORA_FREQUENCY, sensors_available=ALL_SENSORS):
        self.id = id
        self.frequency = frequency
        self.sensors_available = sensors_available

class Packet():
    ''' Network packet utilities
    '''
    def __init__(self, id, msg_type, payload):
        self.id = id
        self.type = msg_type
        self.payload = payload

    @staticmethod
    def decode_packet(data):
        # first byte is ID
        id = data[0]
        msg_type = data[1]
        payload = data[2:]

        return Packet(id, msg_type, payload)

class Basestation():
    ''' The basestation (master) designed to run on a LoPy
    '''

    def __init__(self, nodes):
        self.nodes = [
            Node(1)
        ]
        self.available_data = {}

    def open_socket(self):
        self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

    def join_request(self, pkt):
        id = pkt.id

        ids = map(lambda n: n.id, self.nodes)
        if id in ids:
            log_print('Node join failed, ID %d already known' % id)
            return False

        # Add node to list
        node_sensors = self.decode_available_data(pkt[2:])
        node = Node(id,sensors_available=node_sensors)
        self.nodes.append(node)

    def create_sensor_request(self, id, sensor_type):
        request = b''
        # append ID
        request += id
        # append message type
        request += MessageType.SENSOR_REQUEST
        # append sensor type (payload)
        request += sensor_type
        return request

    def decode_available_data(self, data):
        if len(data) < 3:
            log_print('Cannot decode available data with less than 3 bytes')
            return False

        available = []

        if data[0] == 1:
            available.append(SensorType.TEMP)
        if data[1] == 1:
            available.append(SensorType.HUMID)
        if data[2] == 1:
            available.append(SensorType.AIR_QUAL)

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
        t_end = time.time() + 30
        while time.time() < t_end:
            rx, port = self.s.recvfrom(256)

            # rx is a bit stream
            if rx:
                print(rx)
                pkt = Packet.decode_packet(rx)

                print(pkt.type, pkt.id)
                if pkt.type == MessageType.JOIN:
                    print("Device found!")
                    self.join_request(pkt)
        print("Polling for data...")
        # main control loop
        while True:

		rx, port = self.s.recvfrom(256)
		if rx:
			print(rx)

            # cycle through the sensors and find equipped nodes for each
        for sensor_type in ALL_SENSORS:
            for node in range(0,self.nodes):
                # check if the node supports the sensor type
                if sensor_type in node.sensors_available:
                    # create packet
                    pkt = self.create_sensor_request(node.id, sensor_type)
                    # set blocking to avoid receiving whilst sending
                    self.s.setblocking(True)
                    self.s.send(pkt)
                    # wait a little while
                    time.sleep(4)
                    # wait for response before doing anything else
                    rx, port = self.s.recvfrom(256)
                    # process response
                    if rx:
                        pkt = Packet.decode_packet(rx)

                        if pkt.type == MessageType.SENSOR_RESPONSE:
                            self.record_sensor_data(pkt)
                        else:
                            log_print('Received a packet of type %d but expected Sensor Response (%d)' % (pkt.type, MessageType.SENSOR_RESPONSE))
def main():
    base = Basestation([])
    base.start()

main()
if __name__ == '__main__':
    main()
