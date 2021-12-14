# pack and unpack messages for an elcon battery charger
# author: Brett Downing and Paul Wayper
# Licensed under the GPL V3

from can import Message
from struct import pack, unpack

elcon_charger_id = 0xE5  # 229
elcon_manager_id = 0xF4  # 244
elcon_broadcast_id = 0x50  # 80
elcon_inverter_id = 0xEF  # 239


class ElconUtils(object):
    # Settings sent to and received from the charger
    voltage: float = float(0)
    current: float = float(0)
    hardware_failure: bool = False
    over_temperature: bool = False
    input_voltage: bool = False
    no_battery: bool = False
    timeout: bool = False

    # The CANBUS ID we receive messages to, and send them from
    our_id: int

    # No idea what these are, but keep them as they are for now
    pf = 6
    r = 0
    dp = 0
    priority = 6

    def __init__(self, our_id: int):
        self.our_id = our_id

    def pack_elcon_id(self, source:int, destination:int) -> int:
        """
        Pack the header as required by the Elcon CANBUS instructions.

        Uses the class's existing `pf`, `r`, `dp` and `priority` values,
        plus the given destination and source.
        """
        top_byte = ((self.priority & 0x07) << 2) | \
                   ((self.r        & 0x01) << 1) | \
                   (self.dp       & 0x01)
        # Ironically the arbitration ID needs to be an integer; we need to
        # unpack it from the bytes.
        return unpack('>I', pack('4B', top_byte, self.pf, destination, source))[0]

    def unpack_elcon_id(self, elcon_id: int):
        """
        Unpack the Elcon header for the destination and source addresses.

        This throws the given `pf`, `r`, `dp` and `priority` values away and
        just returns the destination and source as a tuple.
        """
        # Ironically the arbitration ID is an integer; we need to turn it into
        # bytes to unpack it.
        top_byte, pf, destination, source = unpack('4B', pack('>I', elcon_id))
        return (source, destination)

    def unpack_status(self, msg: Message):
        """
        Given a CANBUS message, attempts to unpack the Elcon charger status.

        If this message is from the our source ID (nominally the Elcon charger),
        then the object's `voltage` and `current` values, and the
        `hardware_failure`, `over_temperature`, `input_voltage`, `timeout` and
        `no_battery` flags will be updated, and `True` will be returned to
        indicate that the status is up to date.  Voltage and current are
        accurate to tenths of a unit.

        If this message is not from the Elcon charger, then it is ignored, and
        `False` is returned to indicate that the charger status values have
        not changed since the last message was received.
        """
        (pkt_source, pkt_dest) = self.unpack_elcon_id(msg.arbitration_id)
        # Receive a message from a source to us (the destination)
        if not (pkt_dest == self.our_id or pkt_dest == elcon_broadcast_id):
            print(f"Ignoring message from {pkt_source} to {pkt_dest}")
            return False  # Status is not up to date

        (voltage, current, flags) = unpack('>HHB', msg.data)
        self.msg_source = pkt_source
        self.voltage = float(voltage) / 10
        self.current = float(current) / 10
        self.hardware_failure = (flags & 0x01) != 0
        self.over_temperature = (flags & 0x02) != 0
        self.input_voltage = (flags & 0x04) != 0
        self.no_battery = (flags & 0x08) != 0
        self.timeout = (flags & 0x10) != 0
        return True  # Status is up to date, can use properties

    def pack_command(
        self, pkt_dest: int, voltage: float, current: float, enable: bool
    ) -> Message:
        """
        Pack a command to the charger to set its output voltage and current
        and enable flag.  Alternately, pack the charger's current output and
        state to the rest of the world.

        The message is sent from the class's ID, and uses the class's current
        flags (as packed by `pack_elcon_id` above).
        """
        if voltage == 0:
            print("Not sending a message - voltage must be positive")
            return None
        msg = Message()
        v = int(voltage * 10)
        i = int(current * 10)
        msg.dlc = 5
        # Send a message from us (source) to the destination
        msg.arbitration_id = self.pack_elcon_id(self.our_id, pkt_dest)
        flags = 0
        if pkt_dest == elcon_charger_id:
            # Message to charger
            flags = 1 if enable else 0
        else:
            # Message from charger to rest of world
            if self.hardware_failure:
                flags |= 0x01
            if self.over_temperature:
                flags |= 0x02
            if self.input_voltage:
                flags |= 0x04
            if self.no_battery:
                flags |= 0x08
            if self.timeout:
                flags |= 0x10

        msg.data = pack(">HHB", v, i, flags)
        msg.is_extended_id = True
        return msg
