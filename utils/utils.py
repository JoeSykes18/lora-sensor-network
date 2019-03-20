''' Enum for the types of message that are produced
'''
class MessageType():
  JOIN = 0
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

  @staticmethod
  def createJoinRequestPacket(id):
    pkt = Packet()
    pkt.src_id = bytes(id)
    pkt.dest_id = bytes(0)
    pkt.msg_type = bytes(MessageType.JOIN_REQUEST)
    pkt.payload = bytes(0)

    return pkt

  @staticmethod
  def createJoinResponsePacket(id):
    pkt = Packet()
    pkt.src_id = 0
    pkt.dest_id = id
    pkt.msg_type = MessageType.JOIN_ACK
    pkt.payload = 0
    return pkt

  @staticmethod
  def decode_packet(data):
    # first byte is ID
    src = chr(data[0])
    dest = chr(data[1])
    msg_type = int(chr(data[2]))
    payload = data[3:]
    payload = [chr(c) for c in payload]

    return Packet(src, dest, msg_type, payload)

  @staticmethod
  def encode_packet(packet):
    src = bytes(packet.src_id)
    dest = bytes(packet.dest_id)
    type = bytes(packet.msg_type)
    payload = bytes(packet.payload)

    return bytearray(src, dest, type, payload)
