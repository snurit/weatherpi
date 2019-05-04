import sys, getopt, imp, time, threading

# Declaring constants
SENSORS_REFRESH_RATE = 60
STATUS_LED_PIN = 5

# Trying to import BME680 library
try:
    imp.find_module('bme680')
    import bme680
except ImportError:
    print("Unable to import BME680 sensor library. Check pip installation. Exiting...")
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
                print("target is remote but RPi.GPIO was not found")
                sys.exit(2)
            # If we are in testing situation, using a short refresh rate
            if arg == "preprod":
                SENSORS_REFRESH_RATE = 1
        # when running on a "dev" computer (cause coding on raspberry is painful)
        elif opt in ("-e", "--env") and arg =="dev":
            try:
                import FakeRPi.GPIO as GPIO
            except ImportError:
                print("target is local but FakeRPi.GPIO was not found")
                sys.exit(2)            
else:
    # when option(s) is/are omitted
    print("No target configured. Considering running on a Raspberry PI in production mode")
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("target is remote but RPi.GPIO was not found")
        sys.exit(2)

# Setting GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Initalizing declaring status LED and setting up to LOW state
GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW)

def initialize_sensors():
    sensors = {}

    # Trying to get BME680 sensor on I2C 0x77 (Humidity, Temperature, Pressure and Air quality)
    sensor_bme = False

    try:
        sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except IOError:
        sensor_bme680 = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # Initializing sensors parameters only if found on I2C primary or secondary address
    if(sensor_bme):
        sensor_bme680.set_humidity_oversample(bme680.OS_2X)
        sensor_bme680.set_pressure_oversample(bme680.OS_4X)
        sensor_bme680.set_temperature_oversample(bme680.OS_8X)
        sensor_bme680.set_filter(bme680.FILTER_SIZE_3)

        sensor_bme680.set_gas_status(bme680.ENABLE_GAS_MEAS)
        sensor_bme680.set_gas_heater_temperature(320)
        sensor_bme680.set_gas_heater_duration(150)
        sensor_bme680.select_gas_heater_profile(0)

        sensors['BME680'] = sensor_bme680

    return sensors

def read_sensors(sensors):
    switch_status_led("blink")
    # getting BME680 or raising an exception
    try:
        sensor = sensors['BME680']
    except KeyError:
        print("BME680 not found. Exiting")
        sys.exit(2)

    if sensor.get_sensor_data():
        output = "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(sensor.data.temperature, sensor.data.pressure, sensor.data.humidity)

        if sensor.data.heat_stable:
            print("{0},{1} Ohms".format(output, sensor.data.gas_resistance))

        else:
            print(output)
    switch_status_led("off")

def switch_status_led(light_mode):
    if light_mode == "blink":
        while True:
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
    elif light_mode == "off":
        GPIO.output(STATUS_LED_PIN, GPIO.LOW)
    elif light_mode == "on":
        GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
    else:
        if GPIO.input(STATUS_LED_PIN) == GPIO.HIGH:
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
            return
        GPIO.output(STATUS_LED_PIN, GPIO.HIGH)

sensors = initialize_sensors()

try:
    while True:
        read_sensors(sensors)
        time.sleep(SENSORS_REFRESH_RATE)
except KeyboardInterrupt:
    GPIO.cleanup()
    sys.exit()
