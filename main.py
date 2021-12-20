import asyncio
import can

import battery
import driver
import simulator

can0 = can.Bus('vcan0', bustype='socketcan')
bat = battery.Battery(capacity=10, cells=30)
driver = driver.ChargerDriver(can0)
driver.volts = 120
driver.amps = 10
driver.start()

sim = simulator.ElconCharger(can0, bat)
