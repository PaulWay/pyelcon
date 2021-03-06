# battsim - simulate a Lithium Ion battery.
# Written by Paul Wayper
# Licensed under the GPL V3

class Battery(object):
    """
    A simulated battery that can be charged and discharged in amp-hours,
    and outputs its voltage according to the charge state of charge.
    """
    capacity = 10  # amp-hours
    charge_state = 5
    cells = 1  # number of cells
    minimum_voltage = 3.0  # volts
    storage_voltage = 3.75  # volts
    maximum_voltage = 4.2  # volts

    def __init__(self, capacity: float, cells: int):
        """
        Set up a new battery, with capacity given in amp-hours.

        The battery starts at 50% capacity, and the storage voltage.
        """
        self.capacity = capacity
        self.charge_state = capacity / 2  # Start at half capacity
        self.cells = cells

    def charge(self, volts: float, amps: float, seconds: float):
        """
        Add amp-hours to the battery, by taking the given amps over the given
        number of seconds.

        Will not charge if the given voltage is less than the battery's
        voltage.

        No real attention to 'power' in watts or yet.
        """
        if self.voltage > volts:
            return
        self.charge_state += (amps * seconds) / 3600
        if self.charge_state > self.capacity:
            self.charge_state = self.capacity

    def discharge(self, amps: float, seconds: float):
        """
        Subtract amp-hours from the battery, by producing the given amps over
        the given number of seconds.
        """
        self.charge_state -= (amps * seconds) / 3600
        if self.charge_state < 0:
            self.charge_state = 0

    @property
    def voltage(self) -> float:
        """
        Output the current voltage of the battery, based on its state of
        charge.

        This uses a hand-tuned cubic formula to simulate the voltage curve of
        a LiIon battery, with a flat but gradual increase in the centre and
        steep drop and climb at either end of charging.  So I can't really
        explain why these constants, but they seem to work.
        """
        vrange = self.maximum_voltage - self.minimum_voltage
        frac_charge = (self.charge_state / self.capacity) - 0.5  # range -0.5 to 0.5
        return (
            (frac_charge ** 3 * 3.6 + frac_charge * 0.1 + 0.5)
             * vrange + self.minimum_voltage
        ) * self.cells

    def __str__(self):
        return f"{self.capacity}Ah {self.cells}S battery with {self.charge_state:.3f}Ah charge"


class Charger(object):
    """
    A simulated charger, connected to a battery, that applies voltage and
    current to a battery over time to charge it.
    """
    volts: float = 0
    amps: float = 0

    def __init__(self, battery: Battery):
        self.battery = battery

    def set(self, volts: float, amps: float):
        self.volts = volts
        self.amps = amps

    def charge(self, seconds: float):
        self.battery.charge(self.volts, self.amps, seconds)

    @property
    def is_finished(self) -> bool:
        return self.volts < self.battery.voltage

