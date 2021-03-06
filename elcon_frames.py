# pack and unpack messages for an elcon battery charger
# author: Brett Downing and Paul Wayper
# Licensed under the GPL V3

from can import Message

elcon_charger_id = 0xE5
elcon_manager_id = 0xF4
elcon_broadcast_id = 0x50
elcon_inverter_id = 0xEF


class ElconCharger(object):
    voltage = float(0)
    current = float(0)
    hardware_failure = False
    over_temperature = False
    input_voltage = False
    no_battery = False
    timeout = False

    #No idea what these are, but keep them as they are for now
    pf=6
    r=0
    dp=0
    priority=6

    def pack_elcon_id(self, destination:int, source:int) -> int:
        """
        Pack the header as required by the
        """
        # top_byte = ((self.priority & 0x07) << 2) | \
        #            ((self.r        & 0x01) << 1) | \
        #            (self.dp       & 0x01)
        # return pack()
        elcon_id =  ((self.priority & 0x07) << 26) | \
                    ((self.r        & 0x01) << 25) | \
                    ((self.dp       & 0x01) << 24) | \
                    ((self.pf       & 0xff) << 16) | \
                    ((destination   & 0xff) << 8) | \
                    ((source        & 0xff))
        return elcon_id

    def unpack_elcon_id(self, elcon_id: int):
        priority =       ((elcon_id >> 26) & 0x07)
        r =              ((elcon_id >> 25) & 0x01)
        dp =             ((elcon_id >> 24) & 0x01)
        pf =             ((elcon_id >> 16) & 0xff)
        # Throw those away, we only care about the below:
        destination =    ((elcon_id >> 8)  & 0xff)
        source =         ((elcon_id >> 0)  & 0xff)
        return (destination, source)

    def unpack_status(self, msg: Message):
        (destination, source) = unpack_elcon_id(msg.arbitration_id)
        if source == elcon_charger_id:
            print("Ignoring message")
            return False  # Status is not up to date

        self.voltage = ((msg.data[0] << 8) | (msg.data[1]))/10
        self.current = ((msg.data[2] << 8) | (msg.data[3]))/10
        self.hardware_failure = ((msg.data[4] & 0x01) != 0)
        self.over_temperature = ((msg.data[4] & 0x02) != 0)
        self.input_voltage = ((msg.data[4] & 0x04) != 0)
        self.no_battery = ((msg.data[4] & 0x08) != 0)
        self.timeout = ((msg.data[4] & 0x10) != 0)
        return True  # Status is up to date, can use properties

    def pack_command(self, voltage: float, current: float, enable: bool) -> Message:
        msg = Message()
        if voltage == 0 or current == 0:
            raise ValueError("positive voltage and current")
        v = int(voltage * 10)
        i = int(voltage * 10)
        msg.dlc = 5
        msg.data = bytearray(5)
        msg.data[0] = (v >> 8) & 0xff
        msg.data[1] = (v) & 0xff
        msg.data[2] = (i >> 8) & 0xff
        msg.data[3] = (i) & 0xff
        msg.data[4] = 1 if enable else 0

        msg.id = self.pack_elcon_id(elcon_charger_id, elcon_manager_id)
        msg.is_extended_id = True
        return msg



def test_pack_id():
    ec = ElconCharger()
    return (0x1806E5F4 == ec.pack_elcon_id(elcon_charger_id, elcon_manager_id))
