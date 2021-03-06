from time import sleep

from machine import I2C, Pin
from micropython import const

from helpers import Objdict

ADDR = const(0x1F)

Register = Objdict(
    {
        "Pin": Objdict(
            {
                "Interrupts": Objdict({}),
            }
        ),
    }
)
Config = Objdict(
    {
        "Interrupts": Objdict({}),
        "Modifiers": Objdict({}),
    }
)
Keys = Objdict()

Register.WriteMask = const(1 << 7)
Register.Version = const(0x01)
Register.Config = const(0x02)
Register.Interrupts = const(0x03)
Register.Keys = const(0x04)
Register.Backlight = const(0x05)
Register.Debounce = const(0x06)  # Currently unimplemented in firmware
Register.Frequency = const(0x07)  # Currently unimplemented in firmware
Register.Reset = const(0x08)
Register.FIFO = const(0x09)
Register.Backlight2 = const(0x0A)

Register.Pin.Direction = const(0x0B)
Register.Pin.PullEnable = const(0x0C)
Register.Pin.PullUpDown = const(0x0D)
Register.Pin.Values = const(0x0E)
Register.Pin.Interrupts.Config = const(0x0F)
Register.Pin.Interrupts.State = const(0x10)

Config.AllowOverflow = const(1 << 0)
Config.Interrupts.Overflow = const(1 << 1)
Config.Interrupts.Capslock = const(1 << 2)
Config.Interrupts.Numlock = const(1 << 3)
Config.Interrupts.Keypress = const(1 << 4)
Config.Interrupts.Panic = const(1 << 5)
Config.Modifiers.Report = const(1 << 6)
Config.Modifiers.Modify = const(1 << 7)

Keys.Mask = const(0x1F)
Keys.Capslock = const(1 << 5)
Keys.Numlock = const(1 << 6)

# TODO: these should really be enums
InterruptReason = {
    1 << 0: "OverflowedFIFO",
    1 << 1: "ToggledCapslock",
    1 << 2: "ToggledNumlock",
    1 << 3: "Keypress",
    1 << 4: "Panic",
    1 << 5: "ChangedPin",
    1 << 6: "None",
    1 << 7: "None",
}
KeyStates = ("Idle", "Pressed", "Held", "Released")


class Keyboard:
    # TODO: split writebuf into writing just a register as well as writing a buffer
    def writebuf(self):
        sleep(0.01)
        self.bus.writeto(self._addr, self._buf)

    def readbuf(self):
        sleep(0.01)
        self.bus.readfrom_into(self._addr, self._buf)

    # TODO: write-then-read method (write register, write buffer, read single, read buffer)
    # FIXME: usage of self._buf[n] throughout feels really gross.. (infomercial voice) there's got to be a better way!

    def reset(self):
        # During reset, we clear the interrupt pin and IRQ
        # this is because reset seems to fire an interrupt
        tmp_pin = None
        if self._int_pin is not None:
            tmp_pin = self._int_pin
            self.interrupt_pin = None
        self._buf[0] = Register.Reset
        self.writebuf()
        sleep(0.05)
        if tmp_pin is not None:
            self.interrupt_pin = tmp_pin
            del tmp_pin

    # TODO: make features available based on firmware version
    #       current latest firmware, 0.4, includes Pin gubbins
    #       while 0.3 does not.. my unit (purchased a week or two back)
    #       came with firmware 0.3
    @property
    def firmware_version(self):
        self._buf[0] = Register.Version
        self.writebuf()
        self.readbuf()
        return "%i.%i" % (self._buf[0] >> 4, self._buf[0] & 0xF)

    @property
    def status(self):
        self._buf[0] = Register.Keys
        self.writebuf()
        self.readbuf()
        return self._buf[0]

    @property
    def pending_keys(self):
        return self.status & Keys.Mask

    @property
    def interrupt_pin(self):
        return self._int_pin

    # When the interrupt pin is set, we want to make sure
    #  we clear the IRQ from the previous pin and deinit it,
    #  we set up the right mode and pullup resistors on the pin,
    #  and re-register the IRQ if one was set
    @interrupt_pin.setter
    def interrupt_pin(self, pin):
        if self._int_pin is not None:
            self._int_pin.irq(None)
            del self._int_pin
        self._int_pin = pin
        if self._int_pin is not None:
            self._int_pin.init(mode=Pin.IN, pull=Pin.PULL_UP)
            self.callback = self.callback

    @property
    def callback(self):
        return self._cb

    @callback.setter
    def callback(self, cb):
        if self._int_pin is None:
            raise ValueError("No interrupt pin set!")
        self._cb = cb
        if self._cb is None:
            self._int_pin.irq(None)
        else:
            self._int_pin.irq(handler=self._cb, trigger=Pin.IRQ_FALLING)

    # FIXME: InterruptReason[reason] fails in certain circumstances
    #        such as keypress when FIFO is overflowed
    #        need to figure out how to determine if it's something like
    #        Interrupt.Keypress | Interrupt.OverflowedFIFO
    #        I don't know what other circumstances there are
    @property
    def last_interrupt(self):
        self._buf[0] = Register.Interrupts
        self.writebuf()
        self.readbuf()
        self._last_int_reason = self._buf[0]
        self._buf[0] = Register.Interrupts | Register.WriteMask
        self._buf[1] = 0x0
        self.writebuf()
        return InterruptReason[self._last_int_reason]

    # TODO: am I happy with chr(buf[1]),state[buf[0]]? i don't think so
    def read_key(self):
        if self.pending_keys == 0:
            return
        self._buf[0] = Register.FIFO
        self.writebuf()
        self.readbuf()
        self.keypresses.append((chr(self._buf[1]), KeyStates[self._buf[0]]))

    @property
    def backlight(self):
        self._buf[0] = Register.Backlight
        self.writebuf()
        self.readbuf()
        return int(self._buf[0])

    @backlight.setter
    def backlight(self, value):
        if value not in range(0, 256):
            raise ValueError("Backlight must be between 0 and 255")
        self._buf[0] = Register.Backlight | Register.WriteMask
        self._buf[1] = value
        self.writebuf()

    # TODO: find a better name for this, 'input_buffer' isn't very clear
    @property
    def input_buffer(self):
        return "".join([key[0] for key in self.keypresses if key[1] == "Pressed"])

    # TODO: rename this to something indicating it's the default callback
    def _def_callback(self, pin):
        while self.pending_keys > 0:
            self.read_key()

    # FIXME: there should be asynchronous means of doing Sweet Fades(tm)
    def fade_down(self):
        if self.backlight == 0:
            return
        for _ in range(0, self.backlight)[::-1]:
            sleep(self.fade_step)
            self.backlight = _

    def fade_up(self):
        if self.backlight == 255:
            return
        for _ in range(self.backlight, 256):
            sleep(self.fade_step)
            self.backlight = _

    def fade_to(self, brightness):
        if self.backlight == brightness:
            return
        # FIXME: this feels real gross
        if self.backlight > brightness:
            for _ in range(brightness, self.backlight + 1)[::-1]:
                sleep(self.fade_step)
                self.backlight = _
        else:
            for _ in range(self.backlight, brightness + 1):
                sleep(self.fade_step)
                self.backlight = _

    # TODO: cleanup __init__, this feels messy
    def __init__(
        self,
        bus=None,
        address=ADDR,
        interrupt_pin=None,
        interrupt_callback=None,
        backlight=255,
        fade_step=0.002,
    ):
        self._int_pin = None
        self._last_int_reason = None
        self._cb = self._def_callback
        self._buf = bytearray(2)
        self._addr = address
        self.fade_step = fade_step
        self.keypresses = []
        if bus is None:
            bus = I2C(0, sda=Pin(0), scl=Pin(1))
        self.bus = bus
        self.reset()
        sleep(0.01)
        self.backlight = 0
        if interrupt_pin is not None:
            self.interrupt_pin = interrupt_pin
        if interrupt_pin is not None and interrupt_callback is not None:
            self.callback = interrupt_callback
        self.fade_to(backlight)
