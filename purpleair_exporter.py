from collections import namedtuple
from datetime import datetime, timezone

import time
import requests

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

Location = namedtuple("Location", ["id", "name"])
locations = [Location("16831", "Balmain"), Location("23033", "Milson's Point")]
locations_index = {l.id: l for l in locations}

url = "https://www.purpleair.com/json?show=" + "|".join([l.id for l in locations])

session = requests.Session()


class PACollector:
    def collect(self):
        common_labels = ["id", "location", "name", "channel"]
        purpleair_utctimestamp = GaugeMetricFamily(
            "purpleair_utctimestamp",
            documentation="UTC timestamp from Purple Air (in Unix epoch)",
            labels=common_labels,
        )

        purpleair_particulate_matter_standard = GaugeMetricFamily(
            name="purpleair_particulate_matter_standard",
            documentation="Particulate matter µg/m3 from Purple Air",
            labels=common_labels + ["microns"],
        )
        purpleair_particulate_matter_environmental = GaugeMetricFamily(
            name="purpleair_particulate_matter_environmental",
            documentation="Particulate matter µg/m3 from Purple Air",
            labels=common_labels + ["microns"],
        )

        response = session.get(url)

        if response.status_code != 200:
            raise Exception(
                "non-200 code: " + str(response.status_code) + " " + response.text
            )
        print(response.text)

        data = response.json()
        sensors = data["results"]

        unix_epoch = datetime.utcfromtimestamp(sensors[0]["LastSeen"]).timestamp()

        for sensor in sensors:
            if sensor.get("ParentID"):
                channel = "B"
                parent_id = str(sensor["ParentID"])
            else:
                channel = "A"
                parent_id = str(sensor["ID"])
            labels = [
                str(sensor["ID"]),
                sensor["Label"],
                locations_index[parent_id].name,
                channel,
            ]
            purpleair_utctimestamp.add_metric(labels, unix_epoch)
            # PurpleAir mixed up cf=atm (atmospheric) and cf=1 (standard) so we swap them back.
            # See https://docs.google.com/document/d/15ijz94dXJ-YAZLi9iZ_RaBwrZ4KtYeCy08goGBwnbCU/edit.
            purpleair_particulate_matter_standard.add_metric(
                labels + ["1"], sensor["pm1_0_atm"]
            )
            purpleair_particulate_matter_standard.add_metric(
                labels + ["2.5"], sensor["pm2_5_atm"]
            )
            purpleair_particulate_matter_standard.add_metric(
                labels + ["10"], sensor["pm10_0_atm"]
            )

            purpleair_particulate_matter_environmental.add_metric(
                labels + ["1"], sensor["pm1_0_cf_1"]
            )
            purpleair_particulate_matter_environmental.add_metric(
                labels + ["2.5"], sensor["pm2_5_cf_1"]
            )
            purpleair_particulate_matter_environmental.add_metric(
                labels + ["10"], sensor["pm10_0_cf_1"]
            )

        yield purpleair_utctimestamp
        yield purpleair_particulate_matter_environmental
        yield purpleair_particulate_matter_standard


# Query the PA
REGISTRY.register(PACollector())
start_http_server(9564)

while True:
    time.sleep(60)
