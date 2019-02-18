#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AD65x8 Python Library - test_AD56x8.py
Copyright (c) 2019 David Goncalves
MIT Licence

Based on test_SPI.py from Adafruit_Python_GPIO Library
https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/tests/test_SPI.py
Copyright (c) 2014 Adafruit Industries
MIT Licence

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


"""

import unittest

from tests.MockGPIO import MockGPIO

from AD56x8 import AD56x8

from bitstring import BitArray


class TestAD56x8(unittest.TestCase):

    def test_device_attributes(self):
        """Test for population of attributes at instantiation of a particular DAC model"""
        gpio = MockGPIO()

        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)
        self.assertEqual(device.__getattribute__('device'), 'AD5628-1')
        self.assertEqual(device.__getattribute__('DATA_WIDTH'), 12)
        self.assertEqual(device.__getattribute__('VREF'), 2.5)
        self.assertEqual(device.__getattribute__('PU_DAC_MULT'), 0.0)

    def test_reset(self):
        """"Test for reset command to DAC input register and low-level SPI bus function"""
        gpio = MockGPIO()
        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Command under test
        device.reset()

        # Verify clock
        self.assertListEqual(gpio.pin_written[1], [0,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0, 1, 0, 1, 0, 1, 0, 1,
                                                   0])
        # Verify MOSI
        data_written = BitArray(gpio.pin_written[2]).uint

        # Expected result: Reset command (0x7) in CMD field of 32 bit input to DAC
        data_expected = 0x07000000

        print('Reset Command:', 'SPI:', data_written)
        self.assertEqual(data_expected, data_written)

        # Verify CS
        self.assertListEqual(gpio.pin_written[3], [1, 0, 1])

    def test_internal_ref_mode(self):
        gpio = MockGPIO()

        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Expected result: Reset command (0x8) in CMD field of 32 bit input to DAC
        result_base = 0x08000000

        for mode_key, mode_value in AD56x8.IREF_MODE.items():
            # Command under test
            device.internal_ref_mode(mode_key)
            data_written = BitArray(gpio.pin_written[2]).uint
            # Set CMD, IREF_fields of 32 bit register for comparison to return
            data_expected = result_base + mode_value
            print('Internal Ref Mode Command:', mode_key, 'SPI:', data_written)
            self.assertEqual(data_expected, data_written)
            gpio.clear()

    def test_clear_code_mode(self):
        gpio = MockGPIO()

        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Expected result: Clear Code command (0x5) in CMD field of 32 bit input to DAC
        result_base = 0x05000000

        # Iterate over CLEAR_CODE modes
        for mode_key, mode_value in AD56x8.CLEAR_CODES.items():
            # Command under test
            device.clear_code_mode(mode_key)
            data_written = BitArray(gpio.pin_written[2]).uint
            # Set CMD, CC_MODE fields of 32 bit register for comparison to return
            data_expected = result_base + mode_value
            print('Clear Code Command:', mode_key, "SPI:", data_written)
            self.assertEqual(data_expected, data_written)
            gpio.clear()

    def _dac_input_test_helper(self, command, result_base, debug_text):

        gpio = MockGPIO()

        # The test is performed over all models in the AD56x8 series
        for dac_model in AD56x8.AD56x8_MODEL_PARAMS.keys():

            device = AD56x8.AD56x8(dac_model, gpio=gpio, clk=1, do=2, cs=3)
            data_width = device.__getattribute__('DATA_WIDTH')

            # Test is performed for four different values (all 1s, all 0s, 0101... and 1010...)
            test_values = [int('0' * data_width, 2), int('1' * data_width, 2), int('01' * (data_width // 2), 2),
                           int('10' * (data_width // 2), 2)]

            if command in dir(device):
                if command == 'write_to_Input_Regs':
                    testfunc = device.write_to_Input_Regs
                elif command == 'write_to_Input_Reg_update_all':
                    testfunc = device.write_to_Input_Reg_update_all
                else:
                    self.fail('Unit Test Failure - incorrect DAC Input Test Function called')
            else:
                self.fail('Unit Test Failure - test function not in list of object methods')

            # Iterate over test values and all channels (both by key and value)
            for value in test_values:
                for channel in range(AD56x8.MAX_CHANNELS):
                    # Command under test
                    testfunc(channel, value)
                    data_written = BitArray(gpio.pin_written[2]).uint
                    # Set CMD, ADDR, DATA fields of 32 bit register for comparison to return
                    data_expected = (result_base | ((channel << 20) & 0xffffffff) | (value << (20 - data_width)))
                    print(debug_text, channel, value, "SPI:", data_written)
                    self.assertEqual(data_expected, data_written)
                    gpio.clear()
                for channel in AD56x8.DAC_CHANNELS.keys():
                    # Command under test
                    testfunc(AD56x8.DAC_CHANNELS[channel], value)
                    data_written = BitArray(gpio.pin_written[2]).uint
                    # Set CMD, ADDR, DATA fields of 32 bit register for comparison to return
                    data_expected = (result_base | ((AD56x8.DAC_CHANNELS[channel] << 20) & 0xffffffff) | (
                                value << (20 - data_width)))
                    print(debug_text, channel, value, "SPI:", data_written)
                    self.assertEqual(data_expected, data_written)
                    gpio.clear()

    def test_write_to_Input_Regs(self):

        result_base = 0x00000000
        test_command = 'write_to_Input_Regs'
        debug_text = "Write to Input Regs Command, Channel / Value:"
        self._dac_input_test_helper(test_command, result_base, debug_text)

    def test_update_DAC_Regs(self):
        gpio = MockGPIO()
        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Result Base: Set Update DAC command (0x1) in CMD field of 32 bit input to DAC
        result_base = 0x01000000

        # Iterate over channels (both by key and value)
        for channel in range(AD56x8.MAX_CHANNELS):
            # Command under test
            device.update_DAC_Regs(channel)
            data_written = BitArray(gpio.pin_written[2]).uint
            # Set CMD, ADDR fields of 32 bit register for comparison to return
            data_expected = (result_base | ((channel << 20) & 0xffffffff))
            print('Update DAC Command:', 'Channel:', channel, "SPI:", data_written)
            self.assertEqual(data_expected, data_written)
            gpio.clear()
        for channel in AD56x8.DAC_CHANNELS.keys():
            # Command under test
            device.update_DAC_Regs(AD56x8.DAC_CHANNELS[channel])
            data_written = BitArray(gpio.pin_written[2]).uint
            # Set CMD, ADDR fields of 32 bit register for comparison to return
            data_expected = (result_base | ((AD56x8.DAC_CHANNELS[channel] << 20) & 0xffffffff))
            print('Update DAC Command:', 'Channel:', channel, "SPI:", data_written)
            self.assertEqual(data_expected, data_written)
            gpio.clear()

    def test_write_to_Input_Reg_update_all(self):
        # Result Base: Set Power Mode command (0x2) in CMD field of 32 bit input to DAC
        result_base = 0x02000000

        # Helper function call to perform Input Register test
        test_command = 'write_to_Input_Reg_update_all'
        debug_text = "Write to Input Regs Command Update All DAC, Channel / Value:"
        self._dac_input_test_helper(test_command, result_base, debug_text)

    def test_power_mode(self):
        gpio = MockGPIO()
        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Result Base: Set Power Mode command (0x4) in CMD field of 32 bit input to DAC
        result_base = 0x04000000

        # Iterate over PD_MODES and channels (both by key and value)
        for mode_key, mode_val in AD56x8.PD_MODES.items():
            for channel in range(AD56x8.MAX_CHANNELS):
                # Command under test
                device.power_mode(mode_key, channel)
                data_written = BitArray(gpio.pin_written[2]).uint
                # Set CMD, PD_MODE, PD_CH_SEL fields of 32 bit register for comparison to return
                data_expected = (result_base | ((mode_val << 8) & 0xffffffff)
                                 | ((1 << channel) & 0xffffffff))
                print('Power Down Command:', mode_key, 'Channel:', channel, "SPI:", data_written)
                self.assertEqual(data_expected, data_written)
                gpio.clear()
            for channel_key, channel_val in AD56x8.DAC_CHANNELS.items():
                for channel in channel_key:
                    if channel in range(AD56x8.MAX_CHANNELS):
                        # Command under test
                        device.power_mode(channel_key, channel)
                        data_written = BitArray(gpio.pin_written[2]).uint
                        # Set CMD, PD_MODE, PD_CH_SEL fields of 32 bit register for comparison to return
                        data_expected = (result_base | ((channel_val << 8) & 0xffffffff)
                                         | ((1 << channel) & 0xffffffff))
                        print('Power Down Command:', mode_key, 'Channel:', channel, "SPI:", data_written)
                        self.assertEqual(data_expected, data_written)
                        gpio.clear()

    def test_LDAC_mode(self):
        gpio = MockGPIO()
        device = AD56x8.AD56x8('AD5628-1', gpio=gpio, clk=1, do=2, cs=3)

        # Result Base: Load LDAC register command (0x6) in CMD field of 32 bit input to DAC
        result_base = 0x06000000

        # Iterate over all LDAC modes and channels
        for mode_key, mode_value in AD56x8.LDAC_MODE.items():
            for channel in range(AD56x8.MAX_CHANNELS):
                # Command under test
                device.LDAC_mode(mode_key, channel)
                data_written = BitArray(gpio.pin_written[2]).uint
                # Set CMD, LDAC_MODE_CH fields of 32 bit register for comparison to return
                data_expected = (result_base | ((mode_value << channel) & 0xffffffff))
                print('LDAC Command:', mode_key, 'Channel:', channel, 'SPI:', data_written)
                self.assertEqual(data_expected, data_written)
                gpio.clear()


if __name__ == '__main__':
    unittest.main()
