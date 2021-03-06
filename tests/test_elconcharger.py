from can import Message

import unittest

from elcon_frames import ElconCharger, elcon_charger_id, elcon_manager_id

class ElconChargerTests(unittest.TestCase):

    def test_pack_id(self):
        ec = ElconCharger()
        self.assertEqual(
            ec.pack_elcon_id(elcon_charger_id, elcon_manager_id),
            0x1806E5F4
        )

    def test_unpack_id(self):
        ec = ElconCharger()
        self.assertTrue(
            ec.unpack_elcon_id(0x1806E5F4),
            (elcon_charger_id, elcon_manager_id)
        )

    def test_unpack_status(self):
        ec = ElconCharger()
        msg = Message(arbitration_id=0x1806E5F4, data=b'\x01\x00\x00\x10\x08')
        # Message is from the charger, can decode
        self.assertTrue(ec.unpack_status(msg))
        # Check message details
        self.assertEqual(ec.voltage, 25.6)
        self.assertEqual(ec.current, 1.6)
        self.assertFalse(ec.hardware_failure)
        self.assertFalse(ec.over_temperature)
        self.assertFalse(ec.input_voltage)
        self.assertTrue(ec.no_battery)
        self.assertFalse(ec.timeout)

        # Add tests of failure modes here

    def test_pack_status(self):
        ec = ElconCharger()
        msg = ec.pack_command(51.2, 3.2, True)
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.arbitration_id, 0x1806E5F4)
        self.assertEqual(msg.data, b'\x02\x00\x00\x20\x01')
