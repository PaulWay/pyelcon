from datetime import datetime, timedelta
import asyncio

# from can import Bus, Message, Listener
import can

from battery import Battery
from elcon_frames import (
    ElconUtils, elcon_charger_id, elcon_manager_id, elcon_broadcast_id
)


class ElconCharger(object):
    """
    Simulate an Elcon charger connected to a CANBUS network.

    Elcon chargers emit their current status every second, and expect to
    receive a message no later than once every two seconds telling them what
    state to charge the battery.
    """
    status_interval = 1
    update_timeout = 2
    verbose = True

    def __init__(self, bus, battery):
        self.battery = battery
        self.bus = bus
        self.utils = ElconUtils(our_id=elcon_charger_id)
        self.active = False
        self.last_time = datetime.now()
        self.volts: float = 0.0
        self.amps: float = 0.0
        self.output_amps: float = 0.0

    async def emit_status(self):
        """
        Emit the charger's status every interval, to console and on CANBUS
        """
        while True:
            if self.active:
                print(
                    f"Charger active, set to {self.volts:.2f}V "
                    f"{self.amps:.2f}A, output {self.output_amps:.2f}A"
                )
            else:
                print(f"Charger inactive, last update {self.last_time:%X}")
            print(f"... Battery: {self.battery} at {self.battery.voltage:.2f}V")
            msg = self.utils.pack_command(
                elcon_broadcast_id, self.volts, self.output_amps, enable=True
            )
            if msg:  # voltage / current too low = None for msg
                self.bus.send(msg)
            await asyncio.sleep(self.status_interval)

    async def check_timeout(self):
        while True:
            if datetime.now() - self.last_time > timedelta(seconds=self.update_timeout):
                self.active = False
                self.utils.timeout = True
            await asyncio.sleep(self.status_interval)  # or update_timeout?

    async def read_messages(self):
        async for msg in self.reader:
            if self.utils.unpack_status(msg):
                charge_time = 0.0
                now = datetime.now()
                # Transfer data from utils message to voltage
                self.volts = self.utils.voltage
                self.amps = self.utils.current
                if self.active:
                    # Calculate time to charge battery from previous time
                    charge_time = (now - self.last_time).seconds
                    if self.battery.voltage > self.volts:
                        self.output_amps = 0.0
                    else:
                        self.battery.charge(self.volts, self.amps, charge_time)
                        self.output_amps = self.amps
                else:
                    self.active = True
                    self.utils.timeout = False
                self.last_time = now
                # if self.verbose:
                #     print(
                #         f"... set to {self.volts:.2f}V {self.amps:.2f}A, "
                #         f"output {self.output_amps:.2f}A"
                #     )
            else:
                if self.verbose:
                    print(f"Ignoring {msg}")

    async def main(self):
        loop = asyncio.get_event_loop()
        self.reader = can.AsyncBufferedReader()
        notifier = can.Notifier(self.bus, [self.reader], loop=loop)
        await asyncio.gather(
            self.emit_status(),
            self.check_timeout(),
            self.read_messages(),
        )
        notifier.stop()


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


"""
import simulator
import asyncio
cd = simulator.ChargerDriver(simulator.can0)
cd.volts = 120
cd.amps = 10
cd.start()
asyncio.run(cd.send_message())
"""

can0 = can.Bus('vcan0', bustype='socketcan')
bat = Battery(capacity=10, cells=30)
driver = ChargerDriver(can0)
driver.volts = 120
driver.amps = 10
driver.start()

sim = ElconCharger(can0, bat)
