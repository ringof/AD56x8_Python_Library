import Adafruit_GPIO.SPI as SPI
from AD56x8 import AD56x8


DAC_CH = ['DAC_A', 'DAC_B', 'DAC_C', 'DAC_D', 'DAC_E', 'DAC_F', 'DAC_G', 'DAC_H']

# BeagleBone Black hardware SPI configuration.
SPI_PORT   = 1
SPI_DEVICE = 0
dac = AD56x8.AD56x8('AD5628-1', spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

dac.reset()
dac.internal_ref_mode('ON')

# Configure all channels for SW LDAC
for ch in DAC_CH:
    dac.LDAC_mode('SW', ch)

counter = 0

while True:
    for ch in DAC_CH:
        dac.write_to_Input_Reg(ch, counter)
        dac.update_DAC_Reg(ch)

    voltage = 2*(dac.VREF)*(counter/(2**dac.DATA_WIDTH))
    counter = (counter + 1) % ((2**dac.DATA_WIDTH)-1)
    print("DAC Voltage:", round(voltage, 3))
