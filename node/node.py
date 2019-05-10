import sys
sys.path.append('/home/pi/lora-sensor-network/')
import binascii
import time
import os
import threading
from gps import *
from bluepy import btle, thingy52
from utils import Packet, MessageType
from gpsinterface import GpsInterface
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
from lora import LoRaUtil

DATA_FOLDER = "../data"
TEMP_DATA_FILE = "../data/temperature.csv"
PRESSURE_DATA_FILE = "../data/pressure.csv"
GAS_DATA_FILE = "../data/gas.csv"
HUMIDITY_DATA_FILE = "../data/humidity.csv"

PRINT_BTLE_DEVICES = False

# the enum for a bluetooth device's "short local name"
SHORT_NAME_ADTYPE = 8
# the short name that should be assigned to the Thingys
THINGY_SHORT_NAME = "LoRaSens"
# time between sensor polling
POLL_TIME = 2.0

MAX_LORA_JOIN_ATTEMPTS = 10

# Identifiers for sensor events
e_temperature_handle = None
e_pressure_handle = None
e_humidity_handle = None
e_gas_hande = None

handles = {}

gpsp = None

class Node(threading.Thread):
    # default thingy's MAC address
    MAC_ADDR = 'DE:AA:A8:87:82:CA'

    def __init__(self, id, desired_data):
        threading.Thread.__init__(self)
        self.id = id
        self.dev = None
        self.desired_data = desired_data
        self.gps = None
        self.joined_lora = False
        self.running = True
        
        self.init_lora()
        self.init_files()
        self.init_gps()

    def init_files(self):
        print('Initialising files...')
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        if not os.path.isfile(TEMP_DATA_FILE):
            with open(TEMP_DATA_FILE, 'w') as f:
                f.write('timestamp, temperature(deg C), latitude, longitude, altitude\n')
        if not os.path.isfile(PRESSURE_DATA_FILE):
            with open(PRESSURE_DATA_FILE, 'w') as f:
                f.write('timestamp, pressure (hPa), latitude, longitude, altitude\n')
        if not os.path.isfile(GAS_DATA_FILE):
            with open(GAS_DATA_FILE, 'w') as f:
                f.write('timestamp, eCO2 (ppm), TVOC (ppb), latitude, longitude, altitude\n')
        if not os.path.isfile(HUMIDITY_DATA_FILE):
            with open(HUMIDITY_DATA_FILE, 'w') as f:
                f.write('timestamp, humidity (%), latitude, longitude, altitude\n')

    def init_lora(self):
        BOARD.setup()
        self.lora = LoRaUtil(verbose=False)
        self.lora_thread = threading.Thread(target=self.lora.start)
        self.lora_thread.start()

    def init_gps(self):
        print('Starting GPS thread...')
        self.gps = GpsInterface()
        self.gps.start()

    def enable_sensors(self):
        # enable environmental interface
        self.dev.environment.enable()
        # enable each sensor
        if 'temperature' in self.desired_data:
            self.dev.environment.configure(temp_int=1000)
            self.dev.environment.set_temperature_notification(True)
        if 'pressure' in self.desired_data:
            self.dev.environment.configure(press_int=1000)
            self.dev.environment.set_pressure_notification(True)
        if 'humidity' in self.desired_data:
            self.dev.environment.configure(humid_int=1000)
            self.dev.environment.set_humidity_notification(True)
        if 'gas' in self.desired_data:
            self.dev.environment.configure(gas_mode_int=1)
            self.dev.environment.set_gas_notification(True)

        global e_temperature_handle
        global e_pressure_handle
        global e_humidity_handle
        global e_gas_handle
        global handles

        e_temperature_handle = self.dev.environment.temperature_char.getHandle()
        e_pressure_handle = self.dev.environment.pressure_char.getHandle()
        e_humidity_handle = self.dev.environment.humidity_char.getHandle()
        e_gas_handle = self.dev.environment.gas_char.getHandle()

        handles = {e_temperature_handle: 'temperature', e_pressure_handle: 'pressure',
                e_humidity_handle: 'humidity', e_gas_handle: 'gas'}

    def scan_for_thingy(self):
        print("[NODE] Scanning for BTLE devices")

        # scan for 8 seconds
        scanner = btle.Scanner()
        devices = scanner.scan(8)

        # try and find device named 'LoraSense'
        mac_addr = None
        for dev in devices:
            name = dev.getValueText(SHORT_NAME_ADTYPE)
            if PRINT_BTLE_DEVICES:
                print("[NODE] Device %s %s (%s), RSSI=%d dB" % (name, dev.addr, dev.addrType, dev.rssi))
            if name == THINGY_SHORT_NAME:
                print('[NODE] Found LoraSense Thingy')
                mac_addr = dev.addr
                break

        if mac_addr is None:
            print("[NODE] Failed to find Thingy via BTLE")
            return False

        print("[NODE] Connecting to Thingy...")
        self.dev = thingy52.Thingy52(mac_addr)

        print("[NODE] Connected. Enabling sensors...")

        self.enable_sensors()

        #self.dev.setDelegate(LoRaSenseDelegate(self.gps))
        self.dev.setDelegate(LoRaSenseDelegate(None))

        return True

    def waitForPacket(self, src_id, msg_type, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
                resp = self.lora.recv()
                print(resp)
                if resp:
                        pkt = Packet.decode_packet(resp)
                        print(pkt)
                        print('Selfid=', self.id)
                        if pkt.src_id == src_id and pkt.dest_id == self.id and pkt.type == msg_type:
                                return pkt
        return False

    def join_lora_network(self):
        print('[NODE] Attempting to join LoRa network...') 
        attempts = 0
        while not self.joined_lora and attempts < MAX_LORA_JOIN_ATTEMPTS:
            # send over LoRa and wait for response
            pkt = Packet.createJoinRequestPacket(self.id, self.desired_data) 
            pkt_str = Packet.encode_packet(pkt)
            self.lora.send(pkt_str)
            attempts = attempts + 1
            pkt = self.waitForPacket(0, MessageType.JOIN_ACK)
            if pkt:  
                self.joined_lora = True
                print('[NODE] LoRa network joined successfully')        
            else:
                print('[NODE] Failed to join LoRa network, retrying...')

    def run(self):
        while self.running:
            if self.dev is None:
                self.scan_for_thingy()
            else:
                self.dev.waitForNotifications(POLL_TIME)

            if self.joined_lora:
                print('TODO receive lora')
            else:
                self.join_lora_network()
        #self.disconnect()

    def disconnect(self):
        if self.dev is not None:
            print('Disconnecting from Thingy...')
            self.dev.disconnect()
        if self.gps is not None:
            print("Killing GPS thread...")
            self.gps.stop()
            #self.gps.join() # wait for thread to finish

    def stop(self):
        self.running = False

class LoRaSenseDelegate(thingy52.DefaultDelegate):

    def __init__(self, gps):
        self.gps = gps

    def handleNotification(self, hnd, data):
        t = time.time()
        msg = None
        if hnd == e_temperature_handle:
            temp = binascii.b2a_hex(data)
            msg = '{}.{}'.format(
                        self._str_to_int(temp[:-2]), int(temp[-2:],16))
            print('Temp received:', msg, 'degC')
        elif hnd == e_pressure_handle:
            (press_int, press_dec) = self._extract_pressure_data(data)
            msg = '{}.{}'.format(press_int, press_dec)
            print('Pressure received:', msg,'hPa')
        elif hnd == e_humidity_handle:
            hum = binascii.b2a_hex(data)
            msg = '{}'.format(self._str_to_int(hum))
            print('Humidity received:', msg, '%')
        elif hnd == e_gas_handle:
            eco2, tvoc = self._extract_gas_data(data)
            msg = '{}, {}'.format(eco2, tvoc)
            print('AQ received: eCO2', eco2, 'ppm', 'TVOC ppb:', tvoc)
        else:
            return

        lat, long, alt = self.getGPSData()
        gps_msg = str(lat) + ', ' + str(long) + ',' + str(alt) 
        if msg is not None:
            with open(handles[hnd] + '.csv', 'a') as f:
                f.write(str(t) + ', ' + msg + ', ' + gps_msg + '\n')

    def _str_to_int(self, s):
        i = int(s, 16)
        if i >= 2**7:
            i -= 2**8
        return i

    def _extract_pressure_data(self, data):
        val = binascii.b2a_hex(data)
        pressure_int = 0
        for i in range(0,4):
            pressure_int += (int(val[i*2:(i*2)+2], 16) << 8*i)
        pressure_dec = int(val[-2:], 16)
        return (pressure_int, pressure_dec)

    def _extract_gas_data(self, data):
        val = binascii.b2a_hex(data)
        eco2 = int(val[:2], 16) + (int(val[2:4], 16) << 8)
        tvoc = int(val[4:6], 16) + (int(val[6:8], 16) << 8)
        return eco2, tvoc

    def getGPSData(self):
        print('Fetching GPS data...')
        data = self.gps.getCurrent()
        print('GPS data fetched')
        return data['lat'], data['lon']

def main():
    desired_data = [
            'temperature',
            'humidity',
            'pressure',
            'gas'
            ]
    node = Node(1, desired_data)

    try:
        node.start()
    except Exception as e:
        print('Exception:')
        print(e)
        node.disconnect()
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    main()
