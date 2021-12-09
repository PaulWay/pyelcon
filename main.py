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
