import binascii
import time
from bluepy import btle, thingy52

# the enum for a bluetooth device's "short local name" 
SHORT_NAME_ADTYPE = 8
# the short name that should be assigned to the Thingys
THINGY_SHORT_NAME = "LoRaSens"
# time between sensor polling
POLL_TIME = 2.0

# Identifiers for sensor events
e_temperature_handle = None
e_pressure_handle = None
e_humidity_handle = None
e_gas_hande = None

handles = {}

class Node():
	# default thingy's MAC address
	MAC_ADDR = 'DE:AA:A8:87:82:CA'

	def __init__(self, desired_data):
		self.dev = None
		self.desired_data = desired_data 

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
            print("Scanning for BTLE devices")

            # scan for 8 seconds
            scanner = btle.Scanner()
            devices = scanner.scan(8)

            # try and find device named 'LoraSense'
            mac_addr = None 
            for dev in devices:
                name = dev.getValueText(SHORT_NAME_ADTYPE)
                print("Device %s %s (%s), RSSI=%d dB" % (name, dev.addr, dev.addrType, dev.rssi)) 

                if name == THINGY_SHORT_NAME:
                    print('Found LoraSense Thingy')
                    mac_addr = dev.addr

            if mac_addr is None:
                print("Failed to find Thingy via BTLE")
                return False

	    print("Connecting to Thingy...")
	    self.dev = thingy52.Thingy52(mac_addr)
            
            print("Connected. Enabling sensors...")

            self.enable_sensors()

            self.dev.setDelegate(LoRaSenseDelegate())  

	    return True

        def start(self):
            while True:
                self.dev.waitForNotifications(POLL_TIME)

        def disconnect(self):
            self.dev.disconnect()

class LoRaSenseDelegate(thingy52.DefaultDelegate):
    def handleNotification(self, hnd, data):
        t = time.time()
        msg = None
        if hnd == e_temperature_handle:
            temp = binascii.b2a_hex(data)
            msg = '{}.{}'.format(
                    self._str_to_int(temp[:-2]),
                    int(temp[-2:],16))
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

        if msg is not None:    
            f = open(handles[hnd] + '.dat', 'w+')
            f.write(str(t) + ', ' + msg + '\n')
    
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
        eco2 = int(val[:2]) + (int(val[2:4]) << 8)
        tvoc = int(val[4:6]) + (int(val[6:8]) << 8)
        return eco2, tvoc

def main():
	desired_data = [
		'temperature',
		'humidity',
		'pressure',
		'gas'
	]
	node = Node(desired_data)
	success = node.scan_for_thingy()
	
	if success:
                try:
		    node.start()
                except Exception as e:
                    print('Stopping')
                    print(e)
                    node.disconnect()
if __name__ == '__main__':
    main()
