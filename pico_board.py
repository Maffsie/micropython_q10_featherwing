from machine import I2C, SPI, Pin, SoftI2C
from rp2 import PIO, asm_pio

from bb_q10 import Keyboard
from helpers import Objdict
from ili9341 import Display

# TODO neopixel
# TODO tsc2004 touch controller
# TODO sdcard

buses = Objdict(
    {
        "i2c": None,
        "spi": None,
        "uart": None,
    }
)
pins = Objdict(
    {
        "A0": Pin(26),
        "A1": Pin(27),
        "A2": Pin(20),
        "A3": Pin(21),
        "A4": Pin(22),
        "A5": Pin(28),
        "D5": Pin(6),
        "D6": Pin(7),
        "D9": Pin(8),
        "D10": Pin(9),
        "D11": Pin(10),
        "D12": Pin(11),
        "D13": Pin(12),
        "D14": Pin(13),
        "i2c": Objdict(
            {
                "data": Pin(4),
                "clk": Pin(5),
            }
        ),
        "spi": Objdict(
            {
                "clk": Pin(18),
                "copi": Pin(19),
                "cipo": Pin(16),
                "dc": Objdict(
                    {
                        "lcd": Pin(9),
                    }
                ),
                "select": Objdict(
                    {
                        "sdcard": Pin(6),
                        "lcd": Pin(8),
                    }
                ),
            }
        ),
        "uart": Objdict(
            {
                "TX": Pin(0),
                "RX": Pin(1),
            }
        ),
    }
)
addrs = Objdict(
    {
        "keyboard": 0x1F,
        "touchpanel": 0x48,
    }
)
peripherals = Objdict(
    {
        "als": None,
        "display": None,
        "keyboard": None,
        "touchpanel": None,
    }
)


def setup():
    setup_buses()
    setup_peripherals()


def setup_buses():
    setup_bus_i2c()
    setup_bus_spi()


def setup_bus_i2c():
    global buses
    # buses.i2c = I2C(id=0, scl=pins.i2c.clk, sda=pins.i2c.data)
    buses.i2c = SoftI2C(scl=pins.i2c.clk, sda=pins.i2c.data, freq=100_000)


def setup_bus_spi():
    global buses
    buses.spi = SPI(id=0, sck=pins.spi.clk, mosi=pins.spi.copi, miso=pins.spi.cipo)


def setup_peripherals():
    setup_peripheral_als()
    setup_peripheral_display()
    setup_peripheral_keyboard()


def setup_peripheral_als():
    global peripherals
    peripherals.als = pins.A5
    peripherals.als.init(mode=Pin.IN)


def setup_peripheral_display():
    global peripherals
    peripherals.display = Display(
        spi=buses.spi, cs=pins.spi.select.lcd, dc=pins.spi.dc.lcd
    )


def setup_peripheral_keyboard():
    global buses, peripherals
    peripherals.keyboard = Keyboard(bus=buses.i2c, interrupt_pin=pins.D6)


def diag_i2c_scan():
    global buses
    if buses.i2c is None:
        setup_bus_i2c()
    for addr in buses.i2c.scan():
        print(f"Peripheral found on i2c address 0x{addr:x}")
