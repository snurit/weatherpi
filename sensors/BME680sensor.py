from sensors.AbstractSensor import AbstractSensor
import sys
import logging

try:
    import RPi.GPIO as GPIO
except ImportError:
    logging.debug('Unable to load RPi.GPIO library. Trying to load FakeRPI for local dev purposes')
    try:
        import FakeRPi as GPIO
    except ImportError:
        logging.debug('Unable to load FakeRPI library. Try fixing this issue by installing RPi.GPIO')
        sys.exit(2)

# Trying to import BME680 library
try:
    import bme680
except ImportError:
    logging.error("Unable to import BME680 sensor library. Check pip installation. Exiting...")
    sys.exit(2)


class BME680sensor(AbstractSensor):

    sensor = None
    values = {}

    def __init__(self):
        super(BME680sensor, self).__init__()
        try:
            self.sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
            logging.info("BME680 found on I2C primary address")
        except IOError:
            try:
                self.sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
                logging.info("BME680 found on I2C secondary address")
            except IOError:
                logging.error("BME680 not found on I2C. Exiting...")
                GPIO.cleanup()
                sys.exit(2)
        self.initialize()

    def initialize(self):
        try:
            self.sensor.set_humidity_oversample(bme680.OS_2X)
            self.sensor.set_pressure_oversample(bme680.OS_4X)
            self.sensor.set_temperature_oversample(bme680.OS_8X)
            self.sensor.set_filter(bme680.FILTER_SIZE_3)

            self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
            self.sensor.set_gas_heater_temperature(320)
            self.sensor.set_gas_heater_duration(150)
            self.sensor.select_gas_heater_profile(0)

            if self.sensor.get_sensor_data():
                self.values = {
                    'temp': self.sensor.data.temperature,
                    'pres': self.sensor.data.pressure,
                    'hum': self.sensor.data.humidity
                }

                if self.sensor.data.heat_stable:
                    self.values['gaz'] = self.sensor.data.gas_resistance
        except Exception:
            logging.warning('BME680 initialization failed')

    def get_values(self):
        return self.values

    def get_instance(self):
        return self

    def to_string(self):
        return "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH {3} Ohms".format(
            self.values['temp'],
            self.values['pres'],
            self.values['hum'],
            self.values['gaz']
        )
