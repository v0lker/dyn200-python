import logging
import math
import minimalmodbus
import serial
import time

from misc import clip, sign_extend
from dataclasses import dataclass

log = logging.getLogger()
log.setLevel(logging.DEBUG)


DEFAULT_SERIAL_IFACE = "/dev/ttyS0"
DEFAULT_SLAVE_ID = 1
DEFAULT_BAUD = 14400



@dataclass
class Dyn200Settings:
    torque_filter: int = 50
    torque_fract: int = 1
    boot_zero: int = 1
    torque_dir: int = 0
    speed_filter: int = 10
    speed_fract: int = 0
    power_fract: int = 0

# default sensor settings:
DEFAULT_SETTINGS = Dyn200Settings()



class DYN200Modbus(minimalmodbus.Instrument):
    def __init__(self, slave_addr=DEFAULT_SLAVE_ID, serial_port=DEFAULT_SERIAL_IFACE, baud_rate=DEFAULT_BAUD, settings=DEFAULT_SETTINGS):
        self.slave_addr_ = slave_addr
        self.port_ = serial_port
        self.baud_rate_ = baud_rate
        self.serial_ = None
        self.serial_ = serial.Serial(self.port_, self.baud_rate_, timeout=0.5, parity=serial.PARITY_NONE)
        self.settings_ = settings
        minimalmodbus.Instrument.__init__(self, self.serial_, slaveaddress=self.slave_addr_) #, debug=True)


    def __del__(self):
        if self.serial_ is not None:
            self.serial_.close()


    def set_torque_filter(self, val: int):
        """
        allowed are 1...99, thus, one would assume that it's transmitted as a
        16b value, in particular, since there is another register at 0x08, but: big surprise..
        """
        val = clip(val, 1, 99)
        self.write_long(0x6, val)
        self.settings_.torque_filter = val

    def set_torque_fract(self, val: int):
        """
        0..4
        like the filter value, transmitted as 32b
        """
        val = clip(val, 0, 4)
        self.write_long(0x8, val)
        self.settings_.torque_fract = val

    def set_zero_on_boot(self, val: int):
        """
        0: disabled, 1: enabled
        """
        val = clip(val, 0, 1)
        self.write_long(0xa, val)
        self.settings_.boot_zero = val

    def set_zero(self):
        """
        set torque to zero; this will/(should..) be used as a new zero point
        """
        self.write_long(0x0, 0)

    def set_torque_dir(self, val: int):
        """
        0: default, 1: inverted
        """
        val = clip(val, 0, 1)
        self.write_long(0x12, val)
        self.settings_.torque_dir = val

    def set_speed_filter(self, val: int):
        """
        0...99
        """
        val = clip(val, 0, 99)
        self.write_long(0x1e, val)
        self.settings_.speed_filter = val

    def set_speed_fract(self, val: int):
        """
        0...3
        """
        val = clip(val, 0, 3)
        self.write_long(0x20, val)
        self.settings_.speed_fract = val

    def set_power_fract(self, val: int):
        """
        0...3
        """
        assert False, "unsupported  -- no address specified in data sheet.."
        val = clip(val, 0, 3)
        #self.write_long( addr, val)
        self.settings_.power_fract = val

    def configure_sensor(self, settings=None):
        if settings is None:
            settings = self.settings_

        self.set_torque_filter(settings.torque_filter)
        self.set_torque_fract(settings.torque_fract)
        self.set_zero_on_boot(settings.boot_zero)
        self.set_zero()  # for good measure. TODO: this might not actually work...
        self.set_torque_dir(settings.torque_dir)
        self.set_speed_filter(settings.speed_filter)
        self.set_speed_fract(settings.speed_fract)
        #self.set_power_fract(settings.power_fract)

    def get_torque(self):
        tau_raw = sign_extend(self.read_long(0x0))
        tau = tau_raw / (10 ** self.settings_.torque_fract)
        log.debug(f"torque: {tau_raw} -> {tau} Nm")
        return tau

    def get_speed(self):
        nu_raw = self.read_long(0x2) & 0xffffffff
        nu = nu_raw / (10 ** self.settings_.speed_fract)
        log.debug(f"speed: {nu_raw} -> {nu} 1/s")
        return nu

    def get_power(self):
        P_raw = self.read_long(0x4)
        P = P_raw / (10 ** self.settings_.power_fract)
        log.debug(f"power: {P_raw} -> {P} W")
        return P

    def get_torque_speed_power(self):
        data = self.read_registers(0, 6)

        t1, t2, s1, s2, p1, p2 = data

        tau_raw = sign_extend((t1 << 8) | t2)
        nu_raw = (s1 << 8) | s2
        P_raw = (p1 << 8) | p2

        tau = tau_raw / (10 ** self.settings_.torque_fract)
        nu = nu_raw / (10 ** self.settings_.speed_fract)
        P = P_raw / (10 ** self.settings_.power_fract)
        log.debug(f"torque: {tau_raw} -> {tau} Nm, speed: {nu_raw} -> {nu} 1/s, power: {P_raw} -> {P} W")

        return tau, nu, P




class DYN200Modbus_Mock(object):
    def __init__(self, slave_addr=DEFAULT_SLAVE_ID, serial_port=DEFAULT_SERIAL_IFACE, baud_rate=DEFAULT_BAUD, settings=DEFAULT_SETTINGS):
        self.slave_addr_ = slave_addr
        self.port_ = serial_port
        self.baud_rate_ = baud_rate
        self.serial_ = None
        self.settings_ = settings
        self.torque_ = .1
        self.speed_ = 10
        self.power_ = 1
        self.data_rate_ = 100  # [Hz]
        self.t_ = 0


    def __del__(self):
        pass


    def set_torque_filter(self, val: int):
        """
        allowed are 1...99, thus, one would assume that it's transmitted as a
        16b value, in particular, since there is another register at 0x08, but: big surprise..
        """
        val = clip(val, 1, 99)
        self.settings_.torque_filter = val

    def set_torque_fract(self, val: int):
        """
        0..4
        like the filter value, transmitted as 32b
        """
        val = clip(val, 0, 4)
        self.settings_.torque_fract = val

    def set_zero_on_boot(self, val: int):
        """
        0: disabled, 1: enabled
        """
        val = clip(val, 0, 1)
        self.settings_.boot_zero = val

    def set_zero(self):
        """
        set torque to zero immediately
        TODO: data sheet is a bit vague which register it actually is....
        """
        pass

    def set_torque_dir(self, val: int):
        """
        0: default, 1: inverted
        """
        val = clip(val, 0, 1)
        self.settings_.torque_dir = val

    def set_speed_filter(self, val: int):
        """
        0...99
        """
        val = clip(val, 0, 99)
        self.settings_.speed_filter = val

    def set_speed_fract(self, val: int):
        """
        0...3
        """
        val = clip(val, 0, 3)
        self.settings_.speed_fract = val

    def set_power_fract(self, val: int):
        """
        0...3
        """
        assert False, "unsupported  -- no address specified in data sheet.."
        val = clip(val, 0, 3)
        self.settings_.power_fract = val

    def configure_sensor(self, settings=None):
        if settings is None:
            settings = self.settings_

        self.set_torque_filter(settings.torque_filter)
        self.set_torque_fract(settings.torque_fract)
        self.set_zero_on_boot(settings.boot_zero)
        self.set_zero()  # for good measure. TODO: this might not actually work...
        self.set_torque_dir(settings.torque_dir)
        self.set_speed_filter(settings.speed_filter)
        self.set_speed_fract(settings.speed_fract)
        #self.set_power_fract(settings.power_fract)

    def set_torque(self, val):
        self.torque_ = val

    def get_torque(self):
        return self.torque_

    def get_speed(self):
        return self.speed_

    def get_power(self):
        return self.power_

    def set_torque_speed_power(self, torque, speed, power):
        self.torque_ = torque
        self.speed_ = speed
        self.power_ = power

    def get_torque_speed_power(self):
        dt = 1.0/self.data_rate_
        time.sleep(dt)
        self.t_ += dt
        return self.torque_ * math.sin(self.t_), self.speed_ * math.sin(self.t_), self.power_ * math.sin(self.t_)
