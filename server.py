import sys, getopt, imp, time, logging

# Declaring constants
SENSORS_REFRESH_RATE = 60
STATUS_LED_PIN = 5

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('weatherPi')
logger.setLevel(logging.DEBUG)

# Trying to import BME680 library
try:
    import bme680
except ImportError:
    logger.error("Unable to import BME680 sensor library. Check pip installation. Exiting...")
    sys.exit(2)

# managing launching options
if len(sys.argv) > 1:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "e:", ["env="])
    except getopt.GetoptError:
        print("server.py -e <environment>")
        sys.exit(2)
    for opt, arg in opts:
        # When running on a remote raspberry pi
        if opt in ("-e", "--env") and arg in ("prod", "preprod"):
            try:
                import RPi.GPIO as GPIO
            except ImportError:
                logger.error("target is remote but RPi.GPIO was not found")
            finally:
                sys.exit(2)
            # If we are in testing situation, using a short refresh rate
            if arg == "preprod":
                SENSORS_REFRESH_RATE = 1
                logging.basicConfig(level=logging.DEBUG)
                logger.info("target is remote. Running in 'preprod' mode")
        # when running on a "dev" computer (cause coding directly on raspberry pi is painful)
        elif opt in ("-e", "--env") and arg =="dev":
            try:
                import FakeRPi.GPIO as GPIO
                logging.basicConfig(level=logging.DEBUG)
                logger.info('target is local dev computer. Running in dev mode')
            except ImportError:
                logger.error("target is local but FakeRPi.GPIO was not found")
            finally:
                sys.exit(2)            
else:
    # when option(s) is/are omitted
    logger.warning("No target environnement configured. Considering running on a Raspberry PI in 'production' mode")
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        logger.error("target is remote but RPi.GPIO was not found")
    finally:
        sys.exit(2)

def initialize_GPIO():
    # Setting GPIO mode to BCM
    logger.debug('Setting GPIO mode to BCM')
    GPIO.setmode(GPIO.BCM)

    # Initalizing declaring status LED and setting up to LOW state
    logger.debug("Setting STATUS_LED pin to %d", STATUS_LED_PIN)
    GPIO.setup(STATUS_LED_PIN, GPIO.OUT, initial=GPIO.LOW)

def initialize_sensors():
    logger.debug('Initializing sensors')
    sensors = {}

    # Trying to get BME680 sensor on I2C (Humidity, Temperature, Pressure and Air quality)
    try:
        sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        logger.info("BME680 found on I2C_ADDR_PRIMARY")
    except IOError:
        logger.warning("BME680 not found on I2C_ADDR_PRIMARY. Searching on I2C_ADDR_SECONDARY...")
        try:
            sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
            logger.info("BME680 found on I2C_ADDR_SECONDARY")
        except IOError:
            logger.error("BME680 not found on I2C. Exiting...")
            GPIO.cleanup()
            sys.exit(2)

    # Initializing sensors parameters only if found on I2C primary or secondary address
    logger.debug('BME680 - Setting temperature, humidity and pressure oversample')
    sensor_bme680.set_humidity_oversample(bme680.OS_2X)
    sensor_bme680.set_pressure_oversample(bme680.OS_4X)
    sensor_bme680.set_temperature_oversample(bme680.OS_8X)
    sensor_bme680.set_filter(bme680.FILTER_SIZE_3)

    logger.debug('BME680 - Enabling gaz measeurement and paramaters')
    sensor_bme680.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor_bme680.set_gas_heater_temperature(320)
    sensor_bme680.set_gas_heater_duration(150)
    sensor_bme680.select_gas_heater_profile(0)

    sensors['BME680'] = sensor_bme680
    logger.info("BME680 initialized")

    return sensors

def read_sensors(sensors):
    switch_status_led("blink")
    # getting BME680 or raising an exception
    try:
        sensor = sensors['BME680']
    except KeyError:
        logger.error('BME680 not found. Exiting...')
        sys.exit(2)

    logger.debug('Attempting to read BME680 values')
    if sensor.get_sensor_data():
        logger.debug('BME680 ready for reading. Processing ...')
        output = "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(sensor.data.temperature, sensor.data.pressure, sensor.data.humidity)

        if sensor.data.heat_stable:
            logger.debug('BME680 gas measurement ready for reading. Processing...')
            print("{0},{1} Ohms".format(output, sensor.data.gas_resistance))

        else:
            print(output)
    switch_status_led("off")

def switch_status_led(light_mode):
    try:
        if light_mode == "blink":
            logger.debug("STATUS_LED in 'blink' mode")
            while True:
                GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(STATUS_LED_PIN, GPIO.LOW)
        elif light_mode == "off":
            logger.debug('STATUS_LED - switching manually OFF')
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
        elif light_mode == "on":
            logger.debug('STATUS_LED - switching manually ON')
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
        else:
            if GPIO.input(STATUS_LED_PIN) == GPIO.HIGH:
                logger.debug('STATUS_LED - switching OFF')
                GPIO.output(STATUS_LED_PIN, GPIO.LOW)
                return
            logger.debug('STATUS_LED - switching ON')
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
        return
    except:
        logger.warning("problem occured with STATUS_LED switching")
    finally:
        return

try:
    initialize_GPIO()
    sensors = initialize_sensors()
    while True:
        read_sensors(sensors)
        time.sleep(SENSORS_REFRESH_RATE)
except KeyboardInterrupt:
    print("Exiting - Keyboard interrupt")
finally:
    GPIO.cleanup()
    sys.exit()
