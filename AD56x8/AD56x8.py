#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AD56x8 Python Library
Copyright (c) 2019 David Goncalves

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

from ctypes import Structure, Union, c_uint

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

'''
AD56x8 Register, Commands and Modes Definitions

These classes define the structures of the several types of registers
used in the operation of the DAC; structure changes are dependant on the
command in use.

Register Structures are written LSB first here for convenience.
'''

MAX_CHANNELS = 8


# 32 bit structure for quickly making a list of bytes for writes
class SPI32(Structure):
    _fields_ = [("a", c_uint, 8),
                ("b", c_uint, 8),
                ("c", c_uint, 8),
                ("d", c_uint, 8)]


class SPIWrite(Union):
    _fields_ = [("reg", SPI32),
                ("value", c_uint)]


class InputReg(Structure):
    _fields_ = [("DATA", c_uint, 20),
                ("ADDR", c_uint, 4),
                ("CMD", c_uint, 4),
                ("Pad_1", c_uint, 4)]


class Input(Union):
    _fields_ = [("reg", InputReg),
                ("value", c_uint)]


class RefSetupReg(Structure):
    _fields_ = [("IREF", c_uint, 1),
                ("Pad_2", c_uint, 23),
                ("CMD", c_uint, 4),
                ("Pad_1", c_uint, 4)]


class RefSetup(Union):
    _fields_ = [("reg", RefSetupReg),
                ("value", c_uint)]


class PowerDownReg(Structure):
    _fields_ = [("PD_CH_SEL", c_uint, 8),
                ("PD_MODE", c_uint, 2),
                ("Pad_2", c_uint, 14),
                ("CMD", c_uint, 4),
                ("Pad_1", c_uint, 4)]


class PowerDown(Union):
    _fields_ = [("reg", PowerDownReg),
                ("value", c_uint)]


class ClearCodeReg(Structure):
    _fields_ = [("CC_MODE", c_uint, 2),
                ("Pad_2", c_uint, 22),
                ("CMD", c_uint, 4),
                ("Pad_1", c_uint, 4)]


class ClearCode(Union):
    _fields_ = [("reg", ClearCodeReg),
                ("value", c_uint)]


class LDACReg(Structure):
    _fields_ = [("LDAC_MODE_CH", c_uint, 8),
                ("Pad_2", c_uint, 16),
                ("CMD", c_uint, 4),
                ("Pad_1", c_uint, 4)]


class LDAC(Union):
    _fields_ = [("reg", LDACReg),
                ("value", c_uint)]


# AD56x8 Commands
CMD_WRITE_INPUT_REG_N           = 0x0
CMD_UPDATE_DAC_REG_N            = 0x1
CMD_WRITE_INPUT_RE_N_UPDATE_ALL = 0x2
CMD_WRITE_AND_UPDATE_N          = 0x3
CMD_PWR_DOWN_UP_DAC             = 0x4
CMD_LOAD_CLEAR_CODE_REG         = 0x5
CMD_LOAD_LDAC_REG               = 0x6
CMD_RESET                       = 0x7
CMD_SETUP_INT_REF_REG           = 0x8

# AD56x8 DAC Channel Range
DAC_CHANNELS = {'DAC_A': 0x0,
                'DAC_B': 0x1,
                'DAC_C': 0x2,
                'DAC_D': 0x3,
                'DAC_E': 0x4,
                'DAC_F': 0x5,
                'DAC_G': 0x6,
                'DAC_H': 0x7,
                'ALL_DAC': 0xF}

# AD56x8 Power Down Modes
PD_MODES = {'NORMAL': 0b00,
            '1K_GND': 0b01,
            '100K_GND': 0b10,
            'TRISTATE': 0b11}

# AD56x8 Clear Codes Modes
CLEAR_CODES = {'0x0000': 0b00,
               '0x8000': 0b01,
               '0xFFFF': 0b10,
               'NOP': 0b11}

# AD56x8 Internal Reference Modes
IREF_MODE = {'ON': 0b1,
             'OFF': 0b0}

# AD56x8 LDAC Modes
LDAC_MODE = {'SW': 0b1,
             'HW': 0b0}

AD56x8_MODEL_PARAMS = {'AD5628-1':
                        {'DATA_WIDTH': 12, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5628-3':
                        {'DATA_WIDTH': 12, 'VREF': 5.0, 'PU_DAC_MULT': 0.5},
                       'AD5648-1':
                        {'DATA_WIDTH': 14, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5648-3':
                        {'DATA_WIDTH': 14, 'VREF': 5.0, 'PU_DAC_MULT': 0.5},
                       'AD5668-1':
                        {'DATA_WIDTH': 16, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5668-3':
                        {'DATA_WIDTH': 16, 'VREF': 5.0, 'PU_DAC_MULT': 0.5}}


class AD56x8(object):

    def __init__(self, dac_model, clk=None, cs=None, do=None, spi=None, gpio=None):
        """The constructor for the AD56x8 class.

        Args:
            AD56x8 DAC Specific Args
            dac_model (str): command constant

            Adafruit-GPIO Specific Args
            clk (int): DAC value to selected channel
            cs (str, int): Platform specific pin selection for CS
            do (str, int): Platform specific pin selection for DO
            spi (str, int): Platform specific pin selection for CS
            gpio (str, int): Platform specific selection for platform GPIO

        Attributes:
            DATA_WIDTH (int): Width of DAC value in bits
            VREF (float): Internal VREF voltage
            PU_DAC_MULT (float): Default power-up DAC output value

        Attributes are set for the specific DAC model upon construction, which
        are useful for calculating the DAC value to write for a desired
        output voltage

        Since this component does not have a MISO/DOUT line, it isn't possible
        to determine which/any commands have been received. Use a loopback to
        a ADC, or get a better part.
        """

        # Set DAC attributes specific to called model
        if dac_model in AD56x8_MODEL_PARAMS.keys():
            setattr(self, 'device', dac_model)
            for key, value in AD56x8_MODEL_PARAMS[dac_model].items():
                setattr(self, key, value)
        else:
            raise ValueError('AD56x8: DAC model specified not in known set')

        # Initialize device with software SPI on the specified CLK,
        # CS, and DO pins.  Alternatively can specify hardware SPI by sending
        # an Adafruit_GPIO.SPI.SpiDev device in the spi parameter.

        self._spi = None

        # Handle hardware SPI
        if spi is not None:
            self._spi = spi
        elif clk is not None and cs is not None and do is not None:
            # Default to platform GPIO if not provided.
            if gpio is None:
                gpio = GPIO.get_platform_gpio()
            self._spi = SPI.BitBang(gpio, clk, do, None, cs)
        else:
            raise ValueError('Must specify either hardware spi or clk, \
                                cs, and do for software SPI!')

        # SPI Configurations
        self._spi.set_clock_hz(5000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)

    def _Input_Reg_helper(self, command, channel, value):
        """Helper function to for handling setting an Input Register.

        Args:
            command (const): command constant
            value (int): DAC value to selected channel
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)

        Note: use the DATA_WIDTH and VREF attributes and store the
        IREF state to determine the value to produce the desired
        output voltage.
        """

        i = Input()
        if command == CMD_WRITE_INPUT_REG_N or \
                command == CMD_WRITE_INPUT_RE_N_UPDATE_ALL:
            i.reg.CMD = command
        else:
            raise ValueError('{}: Input Reg Error: Bad command selection'
                             .format(self.device))

        # Allow use of the channel name OR number for selection
        if channel in DAC_CHANNELS:
            i.reg.ADDR = DAC_CHANNELS[channel]
        elif channel in DAC_CHANNELS.values():
            i.reg.ADDR = channel
        else:
            raise ValueError('{}: Input Reg Error: Bad DAC channel selection'
                             .format(self.device))

        # Shift data up to MSB end of the DATA field
        i.reg.DATA = value << (20 - self.DATA_WIDTH)

        self._write32(i.value)

    def write_to_Input_Regs(self, channel, value):
        """Set Input Register of specified channel.

        Args:
            value (int): DAC value to selected channel
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)

        Note: use the DATA_WIDTH and VREF attributes and store the
        IREF state to determine the value to produce the desired
        output voltage.
        """

        self._Input_Reg_helper(CMD_WRITE_INPUT_REG_N, channel, value)

    def update_DAC_Regs(self, channel):
        """Update channel's DAC Register from its Input Register.

        Args:
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)

        Note: use the DATA_WIDTH and VREF attributes and store the
        IREF state to determine the value to produce the desired
        output voltage.
        """

        # Input mode register structure instance, load with command
        i = Input()
        i.reg.CMD = CMD_UPDATE_DAC_REG_N

        # Allow use of the channel name or number for selection
        if channel in DAC_CHANNELS:
            i.reg.ADDR = DAC_CHANNELS[channel]
        elif channel in DAC_CHANNELS.values():
            i.reg.ADDR = channel
        else:
            raise ValueError('{}: Input Reg Error: Bad DAC channel selection'
                             .format(self.device))
        self._write32(i.value)

    def write_to_Input_Reg_update_all(self, channel, value):
        """Update all DAC registers from Input Registers

        Args:
            value (int): DAC value to selected channel
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)

        Note: use the DATA_WIDTH and VREF attributes and store the
        IREF state to determine the value to produce the desired
        output voltage.
        """

        self._Input_Reg_helper(CMD_WRITE_INPUT_RE_N_UPDATE_ALL, channel, value)

    def power_mode(self, mode, channel):
        """Set power down mode for DAC.

        Args:
            mode (str): Power Mode:
                'NORMAL'
                '1K_GND': 1kOhm pulldown to GND
                '100K_GND': 100kOhm pulldown to GND
                'TRISTATE'
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)
        """

        # Power Down mode register structure instance, load with command
        power_down_cmd = PowerDown()
        power_down_cmd.reg.CMD = CMD_PWR_DOWN_UP_DAC

        # Allow use of the channel name or number for selection
        if channel in DAC_CHANNELS:
            power_down_cmd.reg.PD_CH_SEL = (1 << DAC_CHANNELS[channel]) & 0xff
        elif channel in DAC_CHANNELS.values():
            power_down_cmd.reg.PD_CH_SEL = (1 << channel) & 0xff
        else:
            raise ValueError('{self.device}: Input Reg Error: \
                            Bad DAC channel selection'.format(self.device))

        if mode not in PD_MODES:
            raise ValueError('{}: Power Mode Error: Power down modes must be \
                             NORMAL, 1K/GND, 100K/GND or TRISTATE'
                             .format(self.device))
        else:
            power_down_cmd.reg.PD_MODE = PD_MODES[mode]

        self._write32(power_down_cmd.value)

    def clear_code_mode(self, mode):
        """Set clear code mode for DAC

        Args:
            mode (str): Clear Code Modes:
                '0x0000': all outputs at zero when /CLR asserted
                '0x8000': all outputs at midscale when /CLR asserted
                '0xFFFF': all outputs at full scale when /CLR asserted
                'NOP': no operation
        """

        # Clear Code register structure instance, load with command
        clear_code_cmd = ClearCode()
        clear_code_cmd.reg.CMD = CMD_LOAD_CLEAR_CODE_REG

        if mode not in CLEAR_CODES:
            raise ValueError('{}: Clear Codes Error: Clear code must be \
                             0x0000, 0x8000 or 0xFFFF'
                             .format(self.device))

        clear_code_cmd.reg.CC_MODE = CLEAR_CODES[mode]

        self._write32(clear_code_cmd.value)

    def LDAC_mode(self, mode, channel):
        """Configure DAC to Load DAC Registers by command HW or SW command,
        by channel

        Args:
            mode (str): LDAC Mode:
                'SW': Software Commanded Load of DAC Register
                'HW': Hardware (/LDAC pin) Commanded Load of DAC Register
            channel (str, int): DAC Channel given either by:
                Name (DAC_A thru DAC_H and ALL_DAC)
                Integer in range(MAX_CHANNELS)
        """

        # LDAC register structure instance, load with command
        ldac_cmd = LDAC()
        ldac_cmd.reg.CMD = CMD_LOAD_LDAC_REG

        if mode not in LDAC_MODE:
            raise ValueError('{}: LDAC Error: LDAC mode must be Boolean'
                             .format(self.device))
        else:
            # Allow use of the channel name or number for selection
            if channel in DAC_CHANNELS:
                ldac_cmd.reg.LDAC_MODE_CH = \
                    (LDAC_MODE[mode] << DAC_CHANNELS[channel]) & 0xff
            elif channel in DAC_CHANNELS.values():
                ldac_cmd.reg.LDAC_MODE_CH = (LDAC_MODE[mode] << channel) & 0xff
            else:
                raise ValueError('{}: LDAC Error: Bad DAC channel selection'
                                 .format(self.device))

        self._write32(ldac_cmd.value)

    def reset(self):
        """Reset device to power-up defaults."""

        # Input register structure instance, load with reset command
        i = Input()
        i.reg.CMD = CMD_RESET

        self._write32(i.value)

    def internal_ref_mode(self, mode):
        """Configure internal reference mode register.

        Args:
            mode (str): IREF Mode:
                'ON': Internal Reference On
                'OFF': Internal Reference Off
        """

        # Reference Setup register structure instance, load with command
        ref_setup_cmd = RefSetup()
        ref_setup_cmd.reg.CMD = CMD_SETUP_INT_REF_REG

        if mode not in IREF_MODE:
            raise ValueError('{}: IREF mode must be ON or OFF'
                             .format(self.device))

        ref_setup_cmd.reg.IREF = IREF_MODE[mode]

        self._write32(ref_setup_cmd.value)

    def _write32(self, value):
        """Helper function to write 32 bits to the SPI bus.

        Args:
            value (int): data to be written to the SPI bus
        """

        # 32 Bit structure instance for converting value to an array of bytes
        w = SPIWrite()
        w.value = value
        wba = [w.reg.d, w.reg.c, w.reg.b, w.reg.a]

        self._spi.write(wba)