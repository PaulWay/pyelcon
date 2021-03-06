import unittest

from elcon_frames import ElconCharger

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
            (0xE5, 0xF4)
        )
