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
    payload = [chr(c) for c in payload]

    return Packet(src, dest, msg_type, payload)

  @staticmethod
  def create_sensor_request(id, sensor_type):
    src_id = 0
    dest_id = id
    msg_type = typeMessageType.SENSOR_REQUEST
    payload = sensor_type
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def encode_packet(packet):
    return list(bytearray([packet.src_id, packet.dest_id, packet.type]) + bytearray(packet.payload))

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
