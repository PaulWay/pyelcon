
#GPLv3
# pack and unpack messages for an elcon battery charger
# author: Brett Downing

from can import Message

elcon_charger_id = 0xE5
elcon_manager_id = 0xF4
elcon_broadcast_id = 0x50
elcon_inverter_id = 0xEF


class elcon_charger:
  voltage = float(0)
  current = float(0)
  hardware_failure = False
  over_temperature = False
  input_voltage = False
  no_battery = False
  timeout = False


  def pack_elcon_id(priority: int, r:int, dp:int, pf:int, destination:int, source:int) -> int:
    elcon_id =  ((priority    & 0x07) << 26) | \
                ((r           & 0x01) << 25) | \
                ((dp          & 0x01) << 24) | \
                ((pf          & 0xff) << 16) | \
                ((destination & 0xff) << 8) | \
                (source       & 0xff)
    return elcon_id

  def unpack_elcon_id(elcon_id: int):
    priority =       ((elcon_id >> 26) & 0x07)
    r =              ((elcon_id >> 25) & 0x01)
    dp =             ((elcon_id >> 24) & 0x01)
    pf =             ((elcon_id >> 16) & 0xff)
    destination =    ((elcon_id >> 8)  & 0xff)
    source =         ((elcon_id >> 0)  & 0xff)
    return (priority, r, dp, pf, destination, source)


  def unpack_status(self, msg: Message):
    (priority, r, dp, pf, destination, source) = unpack_elcon_id(msg.arbitration_id)
    if source == elcon_charger_id
    self.voltage = ((msg.data[0] << 8) | (msg.data[1]))/10
    self.current = ((msg.data[2] << 8) | (msg.data[3]))/10
    self.hardware_failure = ((msg.data[4] & 0x01) != 0)
    self.over_temperature = ((msg.data[4] & 0x02) != 0)
    self.input_voltage = ((msg.data[4] & 0x04) != 0)
    self.no_battery = ((msg.data[4] & 0x08) != 0)
    self.timeout = ((msg.data[4] & 0x10) != 0)
  return (self.voltage, self.current, self.hardware_failure, self.over_temperature, self.input_voltage, self.no_battery, self.timeout)


  def pack_command(voltage: float, current: float, enable: bool) -> Message:
    msg = Message()
    if voltage > 0:
      if current > 0:
        v = int(voltage * 10)
        i = int(voltage * 10)
        msg.data = bytearray(5)
        msg.data[0] = (v >> 8) & 0xff
        msg.data[1] = (v) & 0xff
        msg.data[2] = (i >> 8) & 0xff
        msg.data[3] = (i) & 0xff
        if enable:
          msg.data[4] = 1
        else:
          msg.data[4] = 0
        
        #No idea what these are
        pf=6
        r=0
        dp=0
        priority=6

        msg.id = pack_elcon_id(priority, r, dp, pf, elcon_charger_id, elcon_manager_id)
        msg.is_extended_id = True
        msg.dlc = 5
        return msg
    raise ValueError("positive voltage and current")



def check_pack_id():
  pf=6
  r=0
  dp=0
  priority=6
  return (0x1806E5F4 == pack_elcon_id(priority, r, dp, pf, elcon_charger_id, elcon_manager_id))