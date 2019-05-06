import sys
import getopt
import time
import logging
import traceback

import sensors.BME680sensor as bme680_sensor

# Declaring constants
SENSORS_REFRESH_RATE = 60
STATUS_LED_PIN = 5
NUM_TRIES_READING_SENSORS = 10

sensors = {}

logging.basicConfig(level=logging.DEBUG)

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
                SENSORS_REFRESH_RATE = 3
                logging.basicConfig(level=logging.DEBUG)
                logging.info("target is remote. Running in 'preprod' mode")
        # when running on a "dev" computer (cause coding directly on raspberry pi is painful)
        elif opt in ("-e", "--env") and arg =="dev":
            try:
                import FakeRPi.GPIO as GPIO
                logging.basicConfig(level=logging.DEBUG)
                logging.info('target is local dev computer. Running in dev mode')
            except ImportError:
                logging.error("target is local but FakeRPi.GPIO was not found")
                sys.exit(2)            
else:
    # when option(s) is/are omitted
    logging.warning("No target environment configured. Considering running on a Raspberry PI in 'production' mode")
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        logging.error("target is remote but RPi.GPIO was not found")
        sys.exit(2)


def initialize_GPIO():
    # Setting GPIO mode to BCM
    logging.debug('Setting GPIO mode to BCM')
    GPIO.setmode(GPIO.BCM)

    # Initializing declaring status LED and setting up to LOW state
    logging.debug("Setting STATUS_LED pin to %d", STATUS_LED_PIN)
    GPIO.setup(STATUS_LED_PIN, GPIO.OUT, initial=GPIO.LOW)


def switch_status_led(light_mode=''):
    try:
        if light_mode == 'blink':
            logging.debug("STATUS_LED in 'blink' mode")
            while True:
                GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(STATUS_LED_PIN, GPIO.LOW)
        elif light_mode == 'off':
            logging.debug('STATUS_LED - switching manually OFF')
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
        elif light_mode == 'on':
            logging.debug('STATUS_LED - switching manually ON')
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
        else:
            if GPIO.input(STATUS_LED_PIN) == GPIO.HIGH:
                logging.debug('STATUS_LED - switching OFF')
                GPIO.output(STATUS_LED_PIN, GPIO.LOW)
                return
            logging.debug('STATUS_LED - switching ON')
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
        return
    except:
        logging.warning('problem occured with STATUS_LED switching')
    finally:
        return


try:
    initialize_GPIO()
    # Add as many sensors you want in sensors
    sensors['BME680'] = bme680_sensor.BME680sensor()

    reading_tries = 0

    while True:
        switch_status_led()
        try:
            for sensor_name, sensor in sensors.iteritems():
                print(sensor.get_values())
            # if no exception raised, resetting reading_tries
            reading_tries = 0
        except Exception as exc:
            print("exception de type ", exc.__class__)
            print("message", exc)
            if reading_tries < NUM_TRIES_READING_SENSORS:
                logging.info('Sensor may be not ready. Retrying')
                reading_tries += 1
            else:
                logging.error("Tried to read %i times sensors without result. Exiting...", NUM_TRIES_READING_SENSORS)
                GPIO.cleanup()
                sys.exit(2)
        finally:
            time.sleep(0.5)
            switch_status_led()
            time.sleep(SENSORS_REFRESH_RATE)

except KeyboardInterrupt:
    logging.info("Exiting - Keyboard interrupt")
    GPIO.cleanup()
    sys.exit()
except Exception:
    print traceback.format_exc()
