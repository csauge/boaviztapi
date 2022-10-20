import os
from datetime import datetime, timedelta

import pandas as pd
import requests

from boaviztapi.model.boattribute import Boattribute, Status

_electricity_emission_factors_df = pd.read_csv(
    os.path.join(os.path.dirname(__file__), '../../data/electricity/electricity_impact_factors.csv'))

_cpu_profile_path = os.path.join(os.path.dirname(__file__), '../../data/consumption_profile/cpu/cpu_profile.csv')
_cloud_profile_path = os.path.join(os.path.dirname(__file__), '../../data/consumption_profile/cloud/cpu_profile.csv')
_server_profile_path = os.path.join(os.path.dirname(__file__),
                                    '../../data/consumption_profile/server/server_profile.csv')


class ModelUsage:
    DEFAULT_USAGE_LOCATION = "EEE"
    DEFAULT_USE_TIME_IN_HOURS = 24 * 365
    DEFAULT_LIFE_TIME_IN_HOURS = 24 * 365 * 3  # 3 years
    DEFAULT_WORKLOAD = 50.
    DEFAULT_POWER_CONSUMPTION = 0

    _DAYS_IN_HOURS = 24
    _YEARS_IN_HOURS = 24 * 365

    def __init__(self, **kwargs):
        self.hours_electrical_consumption = Boattribute(
            unit="W",
            default=self.DEFAULT_POWER_CONSUMPTION
        )
        self.time_workload = Boattribute(default=self.DEFAULT_WORKLOAD, unit="%")
        self.consumption_profile = None
        self.usage_location = Boattribute(
            unit="CodSP3 - NCS Country Codes - NATO",
            default=self.DEFAULT_USAGE_LOCATION
        )
        self.adp_factor = Boattribute(
            unit="KgSbeq/kWh",
            default=default_impact_factor,
            args={"impact_type": "adpe",
                  "usage_location": self.usage_location,
                  "emission_factors_df": _electricity_emission_factors_df})
        self.gwp_factor = Boattribute(
            unit="kgCO2e/kWh",
            default=default_impact_factor,
            args={"impact_type": "gwp",
                  "usage_location": self.usage_location,
                  "emission_factors_df": _electricity_emission_factors_df})
        self.pe_factor = Boattribute(
            unit="MJ/kWh",
            default=default_impact_factor,
            args={"impact_type": "pe",
                  "usage_location": self.usage_location,
                  "emission_factors_df": _electricity_emission_factors_df})

        self.use_time = Boattribute(
            unit="hours",
            default=self.DEFAULT_USE_TIME_IN_HOURS
        )
        self.life_time = Boattribute(
            unit="hours",
            default=self.DEFAULT_LIFE_TIME_IN_HOURS
        )

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value


class ModelUsageServer(ModelUsage):
    DEFAULT_OTHER_CONSUMPTION_RATIO = 0.33
    DEFAULT_LIFE_TIME_IN_HOURS = 24 * 365 * 3  # 3 years
    DEFAULT_POWER_CONSUMPTION = 300  # 300 watt

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.other_consumption_ratio = Boattribute(unit="ratio /1", default=self.DEFAULT_OTHER_CONSUMPTION_RATIO)


class ModelUsageCloud(ModelUsageServer):
    DEFAULT_INSTANCE_PER_SERVER = 1
    DEFAULT_LIFE_TIME_IN_HOURS = 24 * 365 * 2  # 2 years

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instance_per_server = Boattribute(default=self.DEFAULT_INSTANCE_PER_SERVER)

class ModelIntensitySource:
    def __init__(self):
        self.time_window = Boattribute(default=10, unit="minutes")
        self.source = Boattribute(default="boavizta")
        self.url = None
        self.token = None
        self.start_date = Boattribute(default=datetime.now().isoformat(), unit="ISO 8601")
        self.stop_date = Boattribute(unit="ISO 8601")

    def get_forcast(self, location):
        if self.source.value == "carbon_aware_api":
            r = requests.get(
                f"{self.url}/emissions/forecasts/current?location={location}&dataStartAt={self.start_date.value}&dataEndAt={self.stop_date.value}&windowSize={self.time_window.value}",
                headers={'Authorization': self.token})
            return r.json()
        return None

    def get_intensity(self, location):
        intensity = Boattribute()
        if self.source.value == "carbon_aware_api":
            request = requests.get(
                f"{self.url}/emissions/average-carbon-intensity?location={location}&startTime={self.start_date.value}&endTime={self.stop_date.value}",
                headers={'Authorization': self.token})
            intensity.source = "carbon_aware_api"
            intensity.value = request.json()
            intensity.status = Status.COMPLETED
        else:
            sub = _electricity_emission_factors_df
            sub = sub[sub['code'] == location]
            intensity.source = sub.iloc[0].gwp_emission_source
            intensity.value = sub.iloc[0].gwp_emission_factor
            intensity.status = Status.COMPLETED
        return intensity


def default_impact_factor(args):
    sub = args["emission_factors_df"]
    sub = sub[sub['code'] == args["usage_location"].value]
    return getattr(sub.iloc[0], f"{args['impact_type']}_emission_factor"), getattr(sub.iloc[0], f"{args['impact_type']}_emission_source") , Status.COMPLETED
