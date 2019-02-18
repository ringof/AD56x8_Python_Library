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

import logging
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


'''
AD56x8 Register Structure Definitions

These classes define the structures of the several types of registers
used in the operation of the DAC; structure changes are dependant on the command
in use. Register Structures are written LSB first here for convenience.
'''

MAX_CHANNELS = 8


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
               'NORMAL': 0b11}

# AD56x8 Internal Reference Modes
IREF_MODE = {'ON': 0b1,
             'OFF': 0b0}

# AD56x8 LDAC Modes
LDAC_MODE = {True: 0b1,
             False: 0b0}

AD56x8_MODEL_PARAMS = {'AD5628-1': {'DATA_WIDTH': 12, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5628-3': {'DATA_WIDTH': 12, 'VREF': 5.0, 'PU_DAC_MULT': 0.5},
                       'AD5648-1': {'DATA_WIDTH': 14, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5648-3': {'DATA_WIDTH': 14, 'VREF': 5.0, 'PU_DAC_MULT': 0.5},
                       'AD5668-1': {'DATA_WIDTH': 16, 'VREF': 2.5, 'PU_DAC_MULT': 0.0},
                       'AD5668-3': {'DATA_WIDTH': 16, 'VREF': 5.0, 'PU_DAC_MULT': 0.5}}


class AD56x8(object):

    def __init__(self, dac_model, clk=None, cs=None, do=None, spi=None, gpio=None):

        """Initialize AD56x8 device with software SPI on the specified CLK,
        CS, and DO pins.  Alternatively can specify hardware SPI by sending an
        Adafruit_GPIO.SPI.SpiDev device in the spi parameter.
        """

        # Specified dac_model sets attributes (data width, reference voltage, multiplier)
        if dac_model in AD56x8_MODEL_PARAMS.keys():
            setattr(self, 'device', dac_model)
            for key, value in AD56x8_MODEL_PARAMS[dac_model].items():
                    setattr(self, key, value)
        else:
            raise ValueError('DAC device model specified not in known set')

        self._logger = logging.getLogger(self.device)

        # SPI Bus Setup
        self._spi = None

        # Handle hardware SPI
        if spi is not None:
            self._logger.debug('Using hardware SPI')
            self._spi = spi
        elif clk is not None and cs is not None and do is not None:
            self._logger.debug('Using software SPI')
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

        # Initialization of scratch representations of the AD56x8
        # configuration registers. This DAC series has no MISO/DOUT
        # to perform readback so you will need to keep track of
        # state and configuration in your application, perform a reset
        # following application restarts, and possibly analog readback
        # using a muxed ADC channel. Or get a better DAC.

        self.input = Input()

        self.ref_setup_cmd = RefSetup()
        self.ref_setup_cmd.reg.CMD = CMD_SETUP_INT_REF_REG

        self.power_down_cmd = PowerDown()
        self.power_down_cmd.reg.CMD = CMD_PWR_DOWN_UP_DAC

        self.clear_code_cmd = ClearCode()
        self.clear_code_cmd.reg.CMD = CMD_LOAD_CLEAR_CODE_REG

        self.ldac_cmd = LDAC()
        self.ldac_cmd.reg.CMD = CMD_LOAD_LDAC_REG

    def _Input_Reg_helper(self, command, channel, value):
        """Helper function to for handling setting an Input Register."""

        # Allow use of the channel name OR number for selection
        if channel in DAC_CHANNELS:
            self.input.reg.ADDR = DAC_CHANNELS[channel]
        elif channel in DAC_CHANNELS.values():
            self.input.reg.ADDR = channel
        else:
            raise ValueError('Input Reg Error: Bad DAC channel selection')

        self.input.reg.CMD = command

        # Shift data up to MSB end of the DATA field
        self.input.reg.DATA = value << (20 - self.DATA_WIDTH)

        self._write32(self.input.value)
        self._logger.debug('Input Reg. Command: %i', self.input.value)

    def write_to_Input_Regs(self, channel, value):
        """Set Input Register of specified channel."""

        self._Input_Reg_helper(CMD_WRITE_INPUT_REG_N, channel, value)

    def update_DAC_Regs(self, channel):
        """Update channel's DAC Register from its Input Register."""

        # Allow use of the channel name or number for selection
        if channel in DAC_CHANNELS:
            self.input.reg.ADDR = DAC_CHANNELS[channel]
        elif channel in DAC_CHANNELS.values():
            self.input.reg.ADDR = channel
        else:
            raise ValueError('Input Reg Error: Bad DAC channel selection')

        self.input.reg.CMD = CMD_UPDATE_DAC_REG_N

        self._write32(self.input.value)
        self._logger.debug('Input Reg. Command: %i', self.input.value)

    def write_to_Input_Reg_update_all(self, channel, value):
        """Update all DAC registers from Input Registers."""

        self._Input_Reg_helper(CMD_WRITE_INPUT_RE_N_UPDATE_ALL, channel, value)

    def power_mode(self, mode, channel):
        """Set power-up mode register.

        Note: While the datasheet does describe the ability to set PD modes
              across several channels at one time, this method only allows
              setting one channel at a time.
        """

        # Allow use of the channel name or number for selection
        if channel in DAC_CHANNELS:
            self.power_down_cmd.reg.PD_CH_SEL = (1 << DAC_CHANNELS[channel]) & 0xff
        elif channel in DAC_CHANNELS.values():
            self.power_down_cmd.reg.PD_CH_SEL = (1 << channel) & 0xff
        else:
            raise ValueError('Input Reg Error: Bad DAC channel selection')

        if mode not in PD_MODES:
            raise ValueError('Power Mode Error: Power down modes must be NORMAL, \
                            1K/GND, 100K/GND or TRISTATE')
        else:
            self.power_down_cmd.reg.PD_MODE = PD_MODES[mode]

        self._write32(self.power_down_cmd.value)
        self._logger.debug('Power Mode: %s', mode)

    def clear_code_mode(self, mode):
        """Set clear code mode register."""

        if mode not in CLEAR_CODES:
            raise ValueError('Clear Codes Error: \
                Clear code must be 0x0000, 0x8000 or 0xFFFF')
        self.clear_code_cmd.reg.CC_MODE = CLEAR_CODES[mode]
        self._write32(self.clear_code_cmd.value)
        self._logger.debug('Clear Code Mode: %s', mode)

    def LDAC_mode(self, mode, channel):
        """Load DAC Registers (LDAC) by command (SW LDAC)."""

        if mode not in LDAC_MODE:
            raise ValueError('LDAC Error: LDAC mode must be Boolean')
        else:
            # Allow use of the channel name or number for selection
            if channel in DAC_CHANNELS:
                self.ldac_cmd.reg.LDAC_MODE_CH = (LDAC_MODE[mode] << DAC_CHANNELS[channel]) & 0xff
            elif channel in DAC_CHANNELS.values():
                self.ldac_cmd.reg.LDAC_MODE_CH = (LDAC_MODE[mode] << channel) & 0xff
            else:
                raise ValueError('LDAC Error: Bad DAC channel selection')

        self._write32(self.ldac_cmd.value)
        self._logger.debug('LDAC Mode Command: %i ', self.ldac_cmd.value)

    def reset(self):
        """Reset device to power-up defaults."""

        self.input.reg.CMD = CMD_RESET

        self._write32(self.input.value)
        self._logger.debug("Reset Command")

    def internal_ref_mode(self, mode):
        """Configure internal reference mode register."""

        if mode not in IREF_MODE:
            raise ValueError('IREF mode must be ON or OFF')

        self.ref_setup_cmd.reg.IREF = IREF_MODE[mode]
        self._write32(self.ref_setup_cmd.value)
        self._logger.debug('Internal Ref Mode:  %s', mode)

    def _write32(self, value):
        """Write 32 bits to the SPI bus."""

        b = ('{:08x}'.format(value))
        wba = bytearray.fromhex(b)
        self._spi.write(wba)
        self._logger.debug('SPI value bytes written: %i', wba)
