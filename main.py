#!/usr/bin/env python3

import time
import pprint
import signal
import sys
import json
import threading
import logging
from pprint import pformat

from prometheus_client import Gauge, start_http_server
from ruuvitag_sensor.ruuvi import RuuviTagSensor

temp_gauge = Gauge('ruuvi_temperature_c', 'Temperature in Celsius', ['location'])
humidity_gauge = Gauge('ruuvi_humidity_percent', 'Humidity %', ['location'])
pressure_gauge = Gauge('ruuvi_pressure_hpa', 'Air pressure hPa', ['location'])
battery_gauge = Gauge('ruuvi_battery_v', 'Battery V', ['location'])
update_delay = 30
port = 9251
beacons = None
config_file = "/home/pi/ruuvi-exporter/config.json"
debug = False
testdata = True
testdata_file = "/home/pi/ruuvi-exporter/test/ruuvi-data-part.json"

class updateThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        logger.debug(f'start thread {self.name} to fetch ruuvi data in background and update the gauge')
#        while True:
        if beacons.keys():
            logger.debug(f'fetch data for: {beacons.keys()}')
            if not testdata:
                logger.debug(f'fetch data from ruuvi tag library')
                datas = RuuviTagSensor.get_data_for_sensors(beacons.keys(), 10)
            else:
                datas = {}
                with open(testdata_file) as test_file:
                    logger.debug(f'fetch data from {testdata_file}')
                    datas = json.load(test_file)
            data_response = pformat(datas)
            logger.debug(f'data:\n{data_response}')
            for key, value in datas.items() :
                b = beacons[key]
                location = b['name']
                logger.debug(f'==== {key} == location: {location} ====')
                sensor_data = datas[key]
                temperature = sensor_data['temperature']
                humidity = (sensor_data['humidity'] / 100.0)
                pressure = sensor_data['pressure']
                battery = (sensor_data['battery'] / 1000.0)
                if temperature != 0:
                    logger.debug(f"temperature: {temperature}")
                    temp_gauge.labels(location).set(temperature)
                if humidity != 0:
                    logger.debug(f"humidity: {humidity}")
                    humidity_gauge.labels(location).set(humidity)
                if pressure != 0:
                    logger.debug(f"pressure: {pressure}")
                    pressure_gauge.labels(location).set(pressure)
                if battery != 0:
                    logger.debug(f"battery: {battery}")
                    battery_gauge.labels(location).set(battery)
    #            time.sleep(update_delay)

def start_ruuvi_update_thread():
    thread = updateThread(1, "Ruuvi-Update-Thread", 1)
    thread.start()

def load_config():
    with open(config_file) as json_file:
        global beacons
        beacons = json.load(json_file)

def parse_args():
    logger.debug(f'parse args')
    if True:
        logger.setLevel(logging.DEBUG)

def setup_logging():
    logging.basicConfig(format='%(asctime)s %(levelname)-9s %(message)s', level=logging.WARNING)
    global logger
    logger = logging.getLogger(__name__)
    # logger.critical(f'test critical')
    # logger.error(f'test error')
    # logger.warning(f'test warning')
    # logger.info(f'test info')
    # logger.debug(f'test debug')

def log_config():
    config = pformat(beacons)
    logger.debug(f'config: {config}')

def start_server():
    logger.debug(f'Starting HTTP server on port {port} for Prometheus scraping')
    start_http_server(port)

def main():
    setup_logging()
    parse_args()
    load_config()
    log_config()
    start_ruuvi_update_thread()

if __name__ == '__main__':
    main()
