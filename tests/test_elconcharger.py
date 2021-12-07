from can import Message

import unittest

from elcon_frames import ElconUtils, elcon_charger_id, elcon_manager_id

magic_id = 0x1806E5F4

class ElconUtilsTests(unittest.TestCase):

    def test_pack_id(self):
        eu = ElconUtils(elcon_charger_id)
        self.assertEqual(
            eu.pack_elcon_id(elcon_charger_id, elcon_manager_id),
            magic_id
        )

    def test_unpack_id(self):
        eu = ElconUtils(elcon_charger_id)
        self.assertEqual(
            eu.unpack_elcon_id(magic_id),
            (elcon_charger_id, elcon_manager_id)
        )

    def test_unpack_status(self):
        eu = ElconUtils(elcon_charger_id)
        msg = Message(arbitration_id=magic_id, data=b'\x01\x00\x00\x10\x08')
        # Message is from the charger, can decode
        self.assertTrue(ec.unpack_status(msg))
        # Check message details
        self.assertEqual(eu.voltage, 25.6)
        self.assertEqual(eu.current, 1.6)
        self.assertFalse(eu.hardware_failure)
        self.assertFalse(eu.over_temperature)
        self.assertFalse(eu.input_voltage)
        self.assertTrue(eu.no_battery)
        self.assertFalse(eu.timeout)

        # Add tests of failure modes here

    def test_pack_status(self):
        eu = ElconUtils(elcon_charger_id)
        msg = eu.pack_command(51.2, 3.2, True)
        self.assertIsInstance(msg, Message)
        self.assertEqual(msg.arbitration_id, 0x1806E5F4)
        self.assertEqual(msg.data, b'\x02\x00\x00\x20\x01')
