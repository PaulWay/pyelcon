import asyncio
import can

from elcon_frames import (
    ElconUtils, elcon_charger_id, elcon_manager_id, elcon_broadcast_id
)


class ChargerDriver(object):
    """
    Drive an Elcon charger on the CANBUS network.

    Every `update_time` seconds, this will send a message on the CANBUS to
    an Elcon charger with the `volts` and `amps` to run at.  Messages will be
    sent from when the 'start' method is called until the 'finish' method is
    called.
    """
    volts: float = 0.0
    amps: float = 0.0
    efficiency_pct: float = 0.95
    max_watts: float = 1000.0
    update_time: int = 1
    verbose: bool = True

    def __init__(self, bus):
        self.bus = bus
        self.utils = ElconUtils(our_id=elcon_manager_id)
        self.running = False

    def _curb_amps_to_power(self):
        if (self.volts * self.amps) / self.efficiency_pct > self.max_watts:
            self.amps = (self.max_watts / self.volts) * self.efficiency_pct

    def start(self):
        self.running = True
        # Start task here

    def finish(self):
        self.running = False

    async def send_message(self):
        """
        Send the message to the charger.
        """
        while self.running:
            self._curb_amps_to_power()
            msg = self.utils.pack_command(
                elcon_charger_id, self.volts, self.amps, enable=True
            )
            if msg is not None:
                self.bus.send(msg)
                if self.verbose:
                    print(f"Charger told to run at {self.volts:.2f}V {self.amps:.2f}A")
            await asyncio.sleep(self.update_time)

    async def receive_status(self):
        """
        Receive status from charger, report status
        """
        async for msg in self.reader:
            if self.utils.unpack_status(msg):
                print(
                    f"Received from charger: {self.utils.voltage:.2f}V "
                    f"{self.utils.current:.2f}A "
                    f"HW={'XX' if self.utils.hardware_failure else 'OK'} "
                    f"Temp={'XX' if self.utils.over_temperature else 'OK'} "
                    f"Vin={'XX' if self.utils.input_voltage else 'OK'} "
                    f"Bat={'No' if self.utils.no_battery else 'OK'} "
                    f"T/O={'XX' if self.utils.timeout else 'OK'} "
                )
            else:
                pass

    async def main(self):
        """
        Run the receive and send coroutines
        """
        loop = asyncio.get_event_loop()
        self.reader = can.AsyncBufferedReader()
        notifier = can.Notifier(self.bus, [self.reader], loop=loop)
        await asyncio.gather(
            self.send_message(),
            self.receive_status(),
        )
        notifier.stop()

    def __repr__(self):
        if not self.running:
            return f"ChargerDriver: not running"
        return f"ChargerDriver: running at {self.volts:.2f}V {self.amps:.2f}A"
