import unittest

from battery import Battery


class BatteryTestCase(unittest.TestCase):
    """
    Test the battery class so we know it can charge and discharge.
    """

    def test_basic_properties(self):
        bat = Battery(3.0, cells=4)

        # Properties set in init
        self.assertEqual(bat.capacity, 3.0)
        self.assertEqual(bat.cells, 4)
        self.assertEqual(bat.charge_state, 1.5)  # half of capacity default
        # Class properties
        self.assertEqual(bat.minimum_voltage, 3.0)
        self.assertEqual(bat.maximum_voltage, 4.2)
        # Calculated properties
        # Half charge state, middle of voltage range
        self.assertEqual(bat.voltage, 14.4)
        self.assertEqual(repr(bat), "3.0Ah 4S battery with 1.500Ah charge")

    def test_charge(self):
        bat = Battery(3.0, cells=4)

        # Can't charge a battery if voltage under battery's current voltage
        bat.charge(volts=14.0, amps=3, seconds=60)
        self.assertEqual(bat.charge_state, 1.5)
        self.assertEqual(bat.voltage, 14.4)

        # Can charge battery if voltage over battery's current voltage
        bat.charge(volts=16.6, amps=3, seconds=60)
        # Basic properties haven't changed:
        self.assertEqual(bat.capacity, 3.0)
        self.assertEqual(bat.cells, 4)
        self.assertEqual(bat.minimum_voltage, 3.0)
        self.assertEqual(bat.maximum_voltage, 4.2)
        # Charge state has changed
        self.assertEqual(bat.charge_state, 1.55)
        # Voltage has risen slightly
        self.assertGreater(bat.voltage, 14.4)

        # At this stage we can push a battery beyond the charge voltage if we
        # give a long enough duration, but we can't go over the battery's
        # capacity.
        bat.charge(volts=16.6, amps=3, seconds=3600)  # Should be well over
        # But capacity is limited to
        self.assertEqual(bat.charge_state, bat.capacity)
        # And voltage is maxed out
        self.assertEqual(bat.voltage, 16.8)

    def test_discharge(self):
        bat = Battery(3.0, cells=4)

        # Discharge battery
        bat.discharge(amps=3, seconds=60)
        # Basic properties haven't changed:
        self.assertEqual(bat.capacity, 3.0)
        self.assertEqual(bat.cells, 4)
        self.assertEqual(bat.minimum_voltage, 3.0)
        self.assertEqual(bat.maximum_voltage, 4.2)
        # Charge state has changed
        self.assertEqual(bat.charge_state, 1.45)
        # Voltage has lowered slightly
        self.assertLess(bat.voltage, 14.4)

        # Can discharge only down to zero capacity
        bat.discharge(amps=3, seconds=3600)
        self.assertEqual(bat.charge_state, 0)
        self.assertEqual(bat.voltage, 12.0)
