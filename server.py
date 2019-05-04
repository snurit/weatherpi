import sys, getopt, imp, time, logging

# Declaring constants
SENSORS_REFRESH_RATE = 60
STATUS_LED_PIN = 5

logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

# Trying to import BME680 library
try:
    imp.find_module('bme680')
    import bme680
except ImportError:
    logging.error("Unable to import BME680 sensor library. Check pip installation. Exiting...")
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
                logging.error("target is remote but RPi.GPIO was not found")
                sys.exit(2)
            # If we are in testing situation, using a short refresh rate
            if arg == "preprod":
                SENSORS_REFRESH_RATE = 1
                logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
                logging.info("target is remote. Running in 'preprod' mode")
        # when running on a "dev" computer (cause coding on raspberry is painful)
        elif opt in ("-e", "--env") and arg =="dev":
            try:
                import FakeRPi.GPIO as GPIO
                logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
            except ImportError:
                logging.error("target is local but FakeRPi.GPIO was not found")
                sys.exit(2)            
else:
    # when option(s) is/are omitted
    logging.warning("No target configured. Considering running on a Raspberry PI in production mode")
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        logging.error("target is remote but RPi.GPIO was not found")
        sys.exit(2)

def initialize_GPIO():
    # Setting GPIO mode to BCM
    GPIO.setmode(GPIO.BCM)

    # Cleaning in case of a previous "dirty" escape
    GPIO.cleanup()

    # Initalizing declaring status LED and setting up to LOW state
    GPIO.setup(STATUS_LED_PIN, GPIO.OUT, initial=GPIO.LOW)

def initialize_sensors():
    sensors = {}

    # Trying to get BME680 sensor on I2C (Humidity, Temperature, Pressure and Air quality)
    try:
        sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        logging.info("BME680 found on I2C_ADDR_PRIMARY")
    except IOError:
        logging.warning("BME680 not found on I2C_ADDR_PRIMARY. Searching on I2C_ADDR_SECONDARY...")
        try:
            sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
            logging.info("BME680 found on I2C_ADDR_SECONDARY")
        except IOError:
            logging.error("BME680 not found on I2C. Exiting...")
            GPIO.cleanup()
            sys.exit(2)

    # Initializing sensors parameters only if found on I2C primary or secondary address
    sensor_bme680.set_humidity_oversample(bme680.OS_2X)
    sensor_bme680.set_pressure_oversample(bme680.OS_4X)
    sensor_bme680.set_temperature_oversample(bme680.OS_8X)
    sensor_bme680.set_filter(bme680.FILTER_SIZE_3)

    sensor_bme680.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor_bme680.set_gas_heater_temperature(320)
    sensor_bme680.set_gas_heater_duration(150)
    sensor_bme680.select_gas_heater_profile(0)

    sensors['BME680'] = sensor_bme680
    logging.info("BME680 initialized")

    return sensors

def read_sensors(sensors):
    switch_status_led("blink")
    # getting BME680 or raising an exception
    try:
        sensor = sensors['BME680']
    except KeyError:
        logging.error("BME680 not found. Exiting")
        sys.exit(2)

    logging.debug("Attempting to read BME680 values")
    if sensor.get_sensor_data():
        output = "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(sensor.data.temperature, sensor.data.pressure, sensor.data.humidity)

        if sensor.data.heat_stable:
            print("{0},{1} Ohms".format(output, sensor.data.gas_resistance))

        else:
            print(output)
    switch_status_led("off")

def switch_status_led(light_mode):
    if light_mode == "blink":
        logging.debug("STATUS_LED in 'blink' mode")
        while True:
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
    elif light_mode == "off":
        logging.debug('STATUS_LED - switching manually OFF')
        GPIO.output(STATUS_LED_PIN, GPIO.LOW)
    elif light_mode == "on":
        logging.debug('STATUS_LED - switching manually ON')
        GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
    else:
        if GPIO.input(STATUS_LED_PIN) == GPIO.HIGH:
            logging.debug('STATUS_LED - switching OFF')
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
            return
        logging.debug('STATUS_LED - switching ON')
        GPIO.output(STATUS_LED_PIN, GPIO.HIGH)

try:
    initialize_GPIO()
    sensors = initialize_sensors()
    while True:
        read_sensors(sensors)
        time.sleep(SENSORS_REFRESH_RATE)
except KeyboardInterrupt:
    print("Exiting - Keyboard interrupt")
    GPIO.cleanup()
    sys.exit()
