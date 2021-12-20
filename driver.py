import asyncio
import can

from utils import (
    ElconUtils, elcon_charger_id, elcon_manager_id, elcon_broadcast_id
)


class ChargerDriver(object):
    """
    Drive an Elcon charger on the CANBUS network.

    Every `update_time` seconds, this will send a message on the CANBUS to
    an Elcon charger with the `volts` and `amps` to run at.  Messages will be
    sent from when the 'start' method is called until the 'stop' method is
    called.  The 'finished' method will cause the driver to exit completely.
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
        self.finished = False

    def _curb_amps_to_power(self):
        if (self.volts * self.amps) / self.efficiency_pct > self.max_watts:
            self.amps = (self.max_watts / self.volts) * self.efficiency_pct

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def finish(self):
        # Any shutdown
        self.finished = True

    async def send_message(self):
        """
        Send the message to the charger.
        """
        while not self.finished:
            if self.running:
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

    def split_cmd_float(self, cmd):
        cmd, val_s = cmd.split()
        try:
            return float(val_s)
        except ValueError:
            print(f"Didn't understand {val_s} as a float")
            return None

    async def read_command_line(self):
        while not self.finished:
            cmd = input("Cmd: ").strip().lower()

            if cmd in ('help', 'h', '?'):
                print("Help - commands we recognise:")
                print("start    : start sending messages")
                print("stop     : stop sending messages")
                print("volts <x>: set output voltage to <x>")
                print("amps <x> : set output amperage to <x>")
                print("watts <x>: set maximum wattage to <x>")
                print("quit     : finish operation and exit")
            if cmd in ('start', 'go'):
                self.start()
            elif cmd in ('stop', ):
                self.stop()
            elif cmd in ('finish', 'exit', 'quit', 'q'):
                self.finish()
            elif cmd.startswith('volts'):
                volts = self.split_cmd_float(cmd)
                if volts is not None:
                    self.volts = volts
            elif cmd.startswith('amps'):
                amps = self.split_cmd_float(cmd)
                if amps is not None:
                    self.amps = amps
            elif cmd.startswith('watts'):
                watts = self.split_cmd_float(cmd)
                if watts is not None:
                    self.max_watts = watts
            else:
                print(f"Unrecognised command '{cmd}'")


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
