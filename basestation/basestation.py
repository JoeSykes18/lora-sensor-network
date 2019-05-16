from network import LoRa
import socket
import time
import os

from utils.utils import Packet, MessageType, SensorType


''' A wireless sensor network basestation
    designed to run on a LoPy
'''

LORA_FREQUENCY = 869000000
lora = LoRa(mode=LoRa.LORA, frequency=LORA_FREQUENCY, public=False)
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
        ]
        self.id = 0
        self.available_data = {}

    def open_socket(self):
        self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

    def setup_files(self, id, node_sensors):
        filename = ("node_" + str(id))
        if not filename in os.listdir():
            os.mkdir(filename)
            if 0 in node_sensors:
                sensorfile = (filename + '/' + str(SensorType(0)))
                with open(sensorfile, 'w') as f:
                    f.write('timestamp, temperature(deg C), latitude, longitude\n')
            if 1 in node_sensors:
                sensorfile = (filename + '/' + str(SensorType(1)))
                with open(sensorfile, 'w') as f:
                    f.write('timestamp, humidity (%), latitude, longitude\n')
            if 2 in node_sensors:
                sensorfile = (filename + '/' + str(SensorType(2)))
                with open(sensorfile, 'w') as f:
                    f.write('timestamp, eCO2 (ppm), TVOC (ppb), latitude, longitude\n')
            if 3 in node_sensors:
                sensorfile = (filename + '/' + str(SensorType(3)))
                with open(sensorfile, 'w') as f:
                    f.write('timestamp, pressure (hPa), latitude, longitude\n')


    def join_request(self, pkt):

        id = pkt.src_id
        ids = map(lambda n: n.id, self.nodes)
        if id in ids:
            log_print('Node join failed, ID %d already known' % id)
            return False

        # Add node to list
        node_sensors = self.decode_available_sensors(pkt.payload)
        node = Node(id,sensors_available=node_sensors)
        self.nodes.append(node)
        response = Packet.createJoinResponsePacket(id)
        response = Packet.encode_packet(response)
        self.s.setblocking(True)
        self.s.send(bytes(response))
        self.s.setblocking(False)
        #self.setup_files(id, node_sensors)
        print("Sent join acknowledgement")
        return True

    def decode_available_sensors(self, data):
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

        if data[3] == 1:
            available.append(SensorType.PRESS)

        return available

    def record_sensor_data(self, data, node, sensor):
        # first byte of the payload is the sensor type
        id = node.id
        # rest of the payload is the data
        # store
        current_time = str(time.time())
        sensorfile = ("node_" + str(id) + '/' + str(SensorType(sensor)))
        if sensor == 0:
            with open(sensorfile, 'w') as f:
                f.write(current_time + ', ' +  data['temp'] + ', ' + data['latitude'] + ', ' + data['longitude'] +  '\n')
        if sensor == 1:
            with open(sensorfile, 'w') as f:
                f.write(current_time + ', ' +  data['humid'] + ', ' + data['latitude'] + ', ' + data['longitude'] +  '\n')
        if sensor == 2:
            with open(sensorfile, 'w') as f:
                f.write(current_time + ', ' +  data['co2'] + ', ' + data['tvoc'] + ', ' + data['latitude'] + ', ' + data['longitude'] +  '\n')
        if sensor == 3:
            with open(sensorfile, 'w') as f:
                f.write(current_time + ', ' +  data['press'] + ', ' + data['latitude'] + ', ' + data['longitude'] +  '\n')

    def waitForPacket(self, id, msg_type, timeout):
        end = time.time() + timeout
        while time.time() < end:
            rx = self.s.recv(256)
            if rx:
                pkt = Packet.decode_packet(rx)
                if pkt.src_id == id or id == None:
                    if pkt.type == msg_type and pkt.dest_id == 0:
                        return pkt


    def start(self):
        print("Opening socket..")
        self.open_socket()

        # nodes must join within 60 seconds of basestation activation
        print("Looking for connections...")
        self.s.setblocking(False)
        t_end = time.time() + 12
        while time.time() < t_end:
            pkt = self.waitForPacket(None, MessageType.JOIN_REQUEST, 5)
            if pkt:
                print("Device found!")
                self.join_request(pkt)
        print("Polling for data...")
        # main control loop
        while True:

            # cycle through the sensors and find equipped nodes for each
            for sensor_type in ALL_SENSORS:
                print('Getting ', sensor_type , ' data...')
                time.sleep(2)
                for node in self.nodes:
                    # check if the node supports the sensor type
                    time.sleep(3)
                    print('Polling node with id = ', node.id , '...')

                    if sensor_type in node.sensors_available:
                        print("Sensor available!")
                        # create packet
                        pkt = Packet.create_sensor_request(node.id, sensor_type)

                        pkt = Packet.encode_packet(pkt)
                        # set blocking to avoid receiving whilst sending
                        self.s.setblocking(True)
                        self.s.send(bytes(pkt))
                        self.s.setblocking(False)
                        # wait for response before doing anything else
                        pkt = self.waitForPacket(node.id, MessageType.SENSOR_RESPONSE, 10)
                        # process response
                        if pkt:
                            print(pkt.payload)
                            data = Packet.decode_sensor_data(pkt.payload)
                            print(data)
                            #self.record_sensor_data(data, node, sensor)

                            #log_print('Received a packet of type %d but expected Sensor Response (%d)' % (pkt.type, MessageType.SENSOR_RESPONSE))
def main():

    base = Basestation([])
    base.start()

main()
