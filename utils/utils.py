''' Enum for the types of message that are produced
'''
class MessageType():
  JOIN_REQUEST = 0
  JOIN_ACK = 1
  SENSOR_RESPONSE = 2
  SENSOR_REQUEST = 3

''' Enum for the types of sensor available to the network
'''
class SensorType():
    TEMP = 0
    HUMID = 1
    AIR_QUAL = 2
    PRESS = 3

ALL_SENSORS = [SensorType.TEMP, SensorType.HUMID, SensorType.AIR_QUAL, SensorType.PRESS]

class Packet():
  ''' Network packet utilities
  '''
  def __init__(self, src_id, dest_id, msg_type, payload):
    self.src_id = src_id
    self.dest_id = dest_id
    self.type = msg_type
    self.payload = payload

  def __str__(self):
    return ('Packet: src_id=%d | dest_id=%d | msg_type=%d | payload=' % (self.src_id, self.dest_id, self.type)) + str(self.payload)

  @staticmethod
  def createJoinRequestPacket(id, available_sensors=[]):
    src_id = id
    dest_id = 0
    msg_type = MessageType.JOIN_REQUEST
    payload = Packet.encodeAvailableSensors(available_sensors)

    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def createJoinResponsePacket(id):
    src_id = 0
    dest_id = id
    msg_type = MessageType.JOIN_ACK
    payload = 0
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def decode_packet(data):
    # first byte is ID
    src = data[0]
    dest = data[1]
    msg_type = data[2]
    payload = data[3:]
    return Packet(src, dest, msg_type, payload)


  @staticmethod
  def decode_sensor_data(data):
      sensor_data = {}

      #SensorType1 | Lat4 | Long4 | Temp2
      sensor_type = data[0]

      lat_data = data[1:5]
      lat = [chr(c) for c in lat_data]
      lat = str(lat)
      sensor_data['latitude'] = lat


      long_data = data[5:9]
      long = [chr(c) for c in long_data]
      long = str(long)
      sensor_data['longitude'] = long

      if sensor_type == SensorType.TEMP:
          temp = data[9:]
          print(temp[0])
          print(len(temp))
          temp = Packet.join_float(temp[0], temp[1])
          sensor_data['temp'] = temp
          print(temp)
      elif sensor_type == SensorType.PRESS:
          press_list = data[9:]
          press = [chr(c) for c in press_list]
          press = int(str(press))
          sensor_data['press'] = press
          print(press)
      elif sensor_type == SensorType.HUMID:
          humid = data[9:]
          sensor_data['humid'] = humid[0]
          print(humid)
      elif sensor_type == SensorType.AIR_QUAL:

          co2 = data[9:12]

          print(str(co2))
          co2 = int(str(co2))
          sensor_data['co2'] = co2
          tvoc_list = data[12:15]
          tvoc = [chr(c) for c in tvoc_list]
          tvoc = int(str(tvoc))
          sensor_data['tvoc'] = tvoc
          print(co2)
          print(tvoc)

      return sensor_data
  @staticmethod
  def create_sensor_request(id, sensor_type):
    src_id = 0
    dest_id = id
    msg_type = MessageType.SENSOR_REQUEST
    payload = [sensor_type]
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def createSensorResponse(id, sensor_type, data):
    src_id = id
    dest_id = 0
    msg_type = MessageType.SENSOR_RESPONSE
    # split LAT/LON strings into list of chars
    data[-1] = [c for c in data[-1]]
    data[-2] = [c for c in data[-2]]
    payload = [sensor_type]
    if sensor_type == SensorType.AIR_QUAL:
        payload.extend(data[0:4])
    else:
        payload.extend(data[0:3])
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def encode_packet(packet):
    return list(bytearray([packet.src_id, packet.dest_id, packet.type]) + bytearray(packet.payload))

  @staticmethod
  def join_float(int, dec):
      decimal = dec /100
      return int + decimal


  @staticmethod
  def encodeAvailableSensors(sensors):
    output = [0, 0, 0, 0]
    if 'temperature' in sensors:
      output[0] = 1
    if 'humidity' in sensors:
      output[1] = 1
    if 'gas' in sensors:
      output[2] = 1
    if 'pressure' in sensors:
      output[3] = 1
    return output
