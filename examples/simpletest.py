import Adafruit_GPIO.SPI as SPI
from AD56x8 import AD56x8
import time

# BeagleBone Black hardware SPI configuration.
SPI_PORT   = 1
SPI_DEVICE = 0
dac = AD56x8.AD56x8('AD5628-1',spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

#dac.reset()
dac.internal_ref_mode('ON')
dac.LDAC_mode(True, 'DAC_A')

counter = 0

while True:
    dac.write_to_Input_Reg_update_all('ALL_DAC', counter)
    voltage = 2*(dac.VREF)*(counter/(2**dac.DATA_WIDTH))
    counter = (counter + 1) % ((2**dac.DATA_WIDTH)-1)
    print("DAC A Voltage:", round(voltage, 3))
