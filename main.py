#!/usr/bin/env python3

import time
import pprint
import signal
import sys
import json
import threading
import logging
import os
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

PID_FILENAME = "ruuvi-exporter.pid"

class UpdateThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        logger.debug(f'start thread {self.name} to fetch ruuvi data in background and update the gauge')
        while True:
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
                parse_data(datas)
            time.sleep(update_delay)

def parse_data(data):
    data_response = pformat(data)
    logger.debug(f'data:\n{data_response}')
    for key, value in data.items() :
        b = beacons[key]
        location = b['name']
        logger.debug(f'==== {key} == location: {location} ====')
        sensor_data = data[key]
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

def start_ruuvi_update_thread():
    thread = UpdateThread(1, "Ruuvi-Update-Thread", 1)
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

def log_config_and_process():
    config = pformat(beacons)
    logger.debug(f'config: {config}')
    pid = os.getpid()
    logger.debug(f'pid: {pid}')
    try:
        with open(PID_FILENAME, "x") as pid_file:
            pid_file.write(str(pid))
    except OSError as e:
        logger.error(f'can\'t open ruuvi-exporter.pid: {e}, process is either running or has a stale pid file!')
        sys.exit(e.errno)

def start_metrics_server():
    logger.debug(f'Starting HTTP server on port {port} for Prometheus scraping')
    start_http_server(port)

def sigterm_handler(sig, frame):
    logger.info(f'receive signal {sig} on {frame}')
    if os.path.exists(PID_FILENAME):
        os.remove(PID_FILENAME)
    sys.exit(0)

def init_signal_handler():
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

def main():
    setup_logging()
    init_signal_handler()
    parse_args()
    load_config()
    log_config_and_process()
    start_ruuvi_update_thread()
    start_metrics_server()

if __name__ == '__main__':
    main()
