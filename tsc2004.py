import time

from machine import I2C, Pin
from micropython import const

from helpers import Objdict

ADDR = const(0x4B)

Registers = Objdict(
    {
        "BatchDelay": Objdict({}),
        "Clock": Objdict({}),
        "Precharge": Objdict({}),
        "Stabtime": Objdict({}),
    }
)
Commands = Objdict({})

_MAX_12BIT = 0x0FFF
_RESISTOR_VAL = 280

# Control Byte 0
Registers.X = const(0x0 << 3)
Registers.Y = const(0x1 << 3)
Registers.Z1 = const(0x2 << 3)
Registers.Z2 = const(0x3 << 3)

Registers.Read = const(0x01)
Registers.PND0 = const(0x02)

Registers.AUX = const(0x4 << 3)
Registers.AUXHigh = const(0x8 << 3)
Registers.AUXLow = const(0x9 << 3)

Registers.Temp1 = const(0x5 << 3)
Registers.Temp2 = const(0x6 << 3)
Registers.TempHigh = const(0xA << 3)
Registers.TempLow = const(0xB << 3)

Registers.Status = const(0x7 << 3)

Registers.CFR0 = const(0xC << 3)
Registers.CFR1 = const(0xD << 3)
Registers.CFR2 = const(0xE << 3)

Registers.ConvFunc = const(0xF << 3)

# Control Byte 1
Commands.Command = const(1 << 7)
Commands.Normal = const(0x00)
Commands.Stop = const(1 << 0)
Commands.Reset = const(1 << 1)
Commands.Set12Bit = const(1 << 2)

# Config Register 0
Registers.Precharge.t20us = const(0x00 << 5)
Registers.Precharge.t84us = const(0x01 << 5)
Registers.Precharge.t276us = const(0x02 << 5)
Registers.Precharge.t340us = const(0x03 << 5)
Registers.Precharge.t1044us = const(0x04 << 5)
Registers.Precharge.t1108us = const(0x05 << 5)
Registers.Precharge.t1300us = const(0x06 << 5)
Registers.Precharge.t1364us = const(0x07 << 5)

Registers.Stabtime.t0us = const(0x00 << 8)
Registers.Stabtime.t100us = const(0x01 << 8)
Registers.Stabtime.t500us = const(0x02 << 8)
Registers.Stabtime.t1000us = const(0x03 << 8)
Registers.Stabtime.t5000us = const(0x04 << 8)
Registers.Stabtime.t10ms = const(0x05 << 8)
Registers.Stabtime.t50ms = const(0x06 << 8)
Registers.Stabtime.t100ms = const(0x07 << 8)

Registers.Clock.f4MHz = const(0x00 << 11)
Registers.Clock.f2MHz = const(0x01 << 11)
Registers.Clock.f1MHz = const(0x02 << 11)

Registers.CFR0_12Bit = const(1 << 13)
Registers.CFR0_Status = const(1 << 14)
Registers.CFR0_PenMode = const(1 << 15)

# Config Register 1
Registers.BatchDelay.t0ms = const(0x00)
Registers.BatchDelay.t1ms = const(0x01)
Registers.BatchDelay.t2ms = const(0x02)
Registers.BatchDelay.t4ms = const(0x03)
Registers.BatchDelay.t10ms = const(0x04)
Registers.BatchDelay.t20ms = const(0x05)
Registers.BatchDelay.t40ms = const(0x06)
Registers.BatchDelay.t100ms = const(0x07)

# Config Register 2
Registers.CFR2_MaveZ = const(1 << 2)
Registers.CFR2_MaveY = const(1 << 3)
Registers.CFR2_MaveX = const(1 << 4)
Registers.CFR2_Avg7 = const(0x01 << 11)
Registers.CFR2_Medium15 = const(0x03 << 12)

STATUS_DAV_X = 0x8000
STATUS_DAV_Y = 0x4000
STATUS_DAV_Z1 = 0x2000
STATUS_DAV_Z2 = 0x1000
STATUS_DAV_MASK = STATUS_DAV_X | STATUS_DAV_Y | STATUS_DAV_Z1 | STATUS_DAV_Z2
