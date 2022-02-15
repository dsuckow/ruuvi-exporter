#!/usr/bin/env python3

import time
import pprint
import signal
import sys
import json
import threading

from prometheus_client import Gauge, start_http_server
from ruuvitag_sensor.ruuvi import RuuviTagSensor

temp_gauge = Gauge('ruuvi_temperature_c', 'Temperature in Celsius', ['location'])
humidity_gauge = Gauge('ruuvi_humidity_percent', 'Humidity %', ['location'])
pressure_gauge = Gauge('ruuvi_pressure_hpa', 'Air pressure hPa', ['location'])
battery_gauge = Gauge('ruuvi_battery_v', 'Battery V', ['location'])
update_delay = 30
port = 8000
beacons = None
config_file = "/home/pi/ruuvi-exporter/config.json"

class updateThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print("update thread started")
#        while True:
        if beacons.keys():
            print("fetch data for: "+str(beacons.keys()))
            datas = RuuviTagSensor.get_data_for_sensors(beacons.keys(), 10)
            print("data: "+str(datas))
            for key, value in datas.items() :
                print("=== " + key + " ===")
                b = beacons[key]
                location = b['name']
                print("location: "+location)
                sensor_data = datas[key]
                print("temperature: "+str(sensor_data['temperature']))
                print("humidity: "+str(sensor_data['humidity'] / 100.0))
                print("pressure: "+str(sensor_data['pressure']))
                print("battery: "+str(sensor_data['battery'] / 1000.0))
                temp_gauge.labels(location).set(sensor_data['temperature'])
                humidity_gauge.labels(location).set(sensor_data['humidity'] / 100.0)
                pressure_gauge.labels(location).set(sensor_data['pressure'])
                battery_gauge.labels(location).set(sensor_data['battery'] / 1000.0)
    #            time.sleep(update_delay)

def load_config():
    with open(config_file) as json_file:
        global beacons
        beacons = json.load(json_file)

def main():
    load_config()
    print("beacons: ", end="")
    print(beacons)
#    print("Starting HTTP server for Prometheus scraping")
#    start_http_server(port)

    thread = updateThread(1, "Ruuvi-Update-Thread", 1)
    thread.start()

if __name__ == '__main__':
    main()
