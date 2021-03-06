# pack and unpack messages for an elcon battery charger
# author: Brett Downing and Paul Wayper
# Licensed under the GPL V3

from can import Message
from struct import pack, unpack

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
        Pack the header as required by the Elcon CANBUS instructions.

        Uses the class's existing `pf`, `r`, `dp` and `priority` values,
        plus the given destination and source.
        """
        top_byte = ((self.priority & 0x07) << 2) | \
                   ((self.r        & 0x01) << 1) | \
                   (self.dp       & 0x01)
        return pack('4B', top_byte, self.pf, destination, source)

    def unpack_elcon_id(self, elcon_id: int):
        """
        Unpack the Elcon header for the destination and source addresses.

        This throws the given `pf`, `r`, `dp` and `priority` values away and
        just returns the destination and source as a tuple.
        """
        top_byte, pf, destination, source = unpack('4B', elcon_id)
        return (destination, source)

    def unpack_status(self, msg: Message):
        """
        Given a CANBUS message, attempts to unpack the Elcon charger status.

        If this message is from the Elcon charger ID (0xE5, as defined above),
        then the object's `voltage` and `current` values, and the
        `hardware_failure`, `over_temperature`, `input_voltage`, `timeout` and
        `no_battery` flags will be updated, and `True` will be returned to
        indicate that the status is up to date.  Voltage and current are
        accurate to tenths of a unit.

        If this message is not from the Elcon charger, then it is ignored, and
        `False` is returned to indicate that the charger status values have
        not changed since the last message was received.
        """
        (destination, source) = unpack_elcon_id(msg.arbitration_id)
        if source == elcon_charger_id:
            print(f"Ignoring message from {source} to {destination}")
            return False  # Status is not up to date

        (voltage, current, flags) = unpack('HHB', msg.data)
        self.voltage = float(voltage) / 10
        self.current = float(current) / 10
        self.hardware_failure = (flags & 0x01) != 0
        self.over_temperature = (flags & 0x02) != 0
        self.input_voltage = (flags & 0x04) != 0
        self.no_battery = (flags & 0x08) != 0
        self.timeout = (flags & 0x10) != 0
        return True  # Status is up to date, can use properties

    def pack_command(self, voltage: float, current: float, enable: bool) -> Message:
        if voltage == 0 or current == 0:
            print("Not sending a message - voltage and current must be positive")
            return None
        msg = Message()
        v = int(voltage * 10)
        i = int(voltage * 10)
        msg.dlc = 5
        msg.id = self.pack_elcon_id(elcon_charger_id, elcon_manager_id)
        flags = 1 if enable else 0
        msg.data = pack("HHB", v, i, flags)
        msg.is_extended_id = True
        return msg
