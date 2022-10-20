import os
from typing import Optional, List, Union

import pandas as pd

from boaviztapi.dto import BaseDTO
from boaviztapi.model.boattribute import Status
from boaviztapi.model.usage import ModelUsage, ModelUsageServer, ModelUsageCloud
from boaviztapi.model.usage.usage import ModelIntensitySource

_electricity_emission_factors_df = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                            '../../data/electricity/electricity_impact_factors.csv'))


class IntensitySource(BaseDTO):
    source: Optional[str] = None
    url: Optional[str] = None
    token: Optional[str] = None
    start_date: Optional[str] = None
    stop_date: Optional[str] = None


class WorkloadTime(BaseDTO):
    time_percentage: float = None
    load_percentage: float = None


class Usage(BaseDTO):
    years_use_time: Optional[float] = None
    days_use_time: Optional[float] = None
    hours_use_time: Optional[float] = None

    years_life_time: Optional[float] = None

    hours_electrical_consumption: Optional[float] = None
    time_workload: Optional[Union[float, List[WorkloadTime]]] = None

    usage_location: Optional[str] = None
    gwp_factor: Optional[float] = None
    pe_factor: Optional[float] = None
    adp_factor: Optional[float] = None

    gwp_source: Optional[IntensitySource] = None


class UsageServer(Usage):
    other_consumption_ratio: Optional[float] = None


class UsageCloud(UsageServer):
    instance_per_server: Optional[int] = None


def smart_mapper_usage(usage_dto: Usage) -> ModelUsage:
    usage_model = ModelUsage()

    if usage_dto.time_workload is not None:
        usage_model.time_workload.value = usage_dto.time_workload
        if type(usage_dto.time_workload) == float:
            usage_model.time_workload.unit = "%"
        else:
            usage_model.time_workload.unit = "(time_percentage:%, load_percentage: %)"

        usage_model.time_workload.status = Status.INPUT

    if usage_dto.hours_electrical_consumption is not None:
        usage_model.hours_electrical_consumption.value = usage_dto.hours_electrical_consumption
        usage_model.hours_electrical_consumption.status = Status.INPUT

    if usage_dto.years_life_time is not None:
        usage_model.life_time.value = usage_dto.years_life_time * 24 * 365
        usage_model.life_time.status = Status.INPUT

    if usage_dto.hours_use_time is not None or usage_dto.days_use_time is not None or usage_dto.years_use_time is not None:
        usage_model.use_time.value = (usage_dto.hours_use_time or 0) + \
                                     (usage_dto.days_use_time or 0) * 24 + \
                                     (usage_dto.years_use_time or 0) * 24 * 365

        usage_model.use_time.status = Status.INPUT

    if usage_dto.usage_location is not None:
        sub = _electricity_emission_factors_df
        sub = sub[sub['code'] == usage_dto.usage_location]
        if len(sub) == 0:
            pass
        else:

            usage_model.usage_location.value = usage_dto.usage_location
            usage_model.usage_location.status = Status.INPUT

    if usage_dto.gwp_factor is not None:
        usage_model.gwp_factor.value = usage_dto.gwp_factor
        usage_model.gwp_factor.status = Status.INPUT
    elif usage_dto.gwp_source is not None:
        gwp_source = mapper_intensity_source(usage_dto.gwp_source)
        usage_model.gwp_factor = gwp_source.get_intensity(usage_model.usage_location)

    if usage_dto.adp_factor is not None:
        usage_model.adp_factor.value = usage_dto.adp_factor
        usage_model.adp_factor.status = Status.INPUT

    if usage_dto.pe_factor is not None:
        usage_model.pe_factor.value = usage_dto.pe_factor
        usage_model.pe_factor.status = Status.INPUT

    return usage_model


def smart_mapper_usage_server(usage_dto: UsageServer) -> ModelUsageServer:
    usage_model_server = ModelUsageServer()

    if usage_dto.hours_electrical_consumption is not None:
        usage_model_server.hours_electrical_consumption.value = usage_dto.hours_electrical_consumption
        usage_model_server.hours_electrical_consumption.status = Status.INPUT

    if usage_dto.years_life_time is not None:
        usage_model_server.life_time.value = usage_dto.years_life_time * 24 * 365
        usage_model_server.life_time.status = Status.INPUT

    if usage_dto.hours_use_time is not None or usage_dto.days_use_time is not None or usage_dto.years_use_time is not None:
        usage_model_server.use_time.value = (usage_dto.hours_use_time or 0) + \
                                            (usage_dto.days_use_time or 0) * 24 + \
                                            (usage_dto.years_use_time or 0) * 24 * 365

        usage_model_server.use_time.status = Status.INPUT

    if usage_dto.time_workload is not None:
        usage_model_server.time_workload.value = usage_dto.time_workload
        usage_model_server.time_workload.status = Status.INPUT

    if usage_dto.usage_location is not None:
        sub = _electricity_emission_factors_df
        sub = sub[sub['code'] == usage_dto.usage_location]
        if len(sub) == 0:
            pass
        else:
            usage_model_server.usage_location.value = usage_dto.usage_location
            usage_model_server.usage_location.status = Status.INPUT

    if usage_dto.other_consumption_ratio is not None:
        usage_model_server.other_consumption_ratio.value = usage_dto.other_consumption_ratio
        usage_model_server.other_consumption_ratio.status = Status.INPUT

    return usage_model_server


def smart_mapper_usage_cloud(usage_dto: UsageCloud):
    usage_model_cloud = ModelUsageCloud()

    if usage_dto.hours_electrical_consumption is not None:
        usage_model_cloud.hours_electrical_consumption.value = usage_dto.hours_electrical_consumption
        usage_model_cloud.hours_electrical_consumption.status = Status.INPUT

    if usage_dto.years_life_time is not None:
        usage_model_cloud.life_time.value = usage_dto.years_life_time * 24 * 365
        usage_model_cloud.life_time.status = Status.INPUT

    if usage_dto.hours_use_time is not None or usage_dto.days_use_time is not None or usage_dto.years_use_time is not None:
        usage_model_cloud.use_time.value = (usage_dto.hours_use_time or 0) + \
                                           (usage_dto.days_use_time or 0) * 24 + \
                                           (usage_dto.years_use_time or 0) * 24 * 365

        usage_model_cloud.use_time.status = Status.INPUT

    if usage_dto.time_workload is not None:
        usage_model_cloud.time_workload.value = usage_dto.time_workload
        usage_model_cloud.time_workload.status = Status.INPUT

    if usage_dto.usage_location is not None:
        sub = _electricity_emission_factors_df
        sub = sub[sub['code'] == usage_dto.usage_location]
        if len(sub) == 0:
            pass
        else:
            usage_model_cloud.usage_location.value = usage_dto.usage_location
            usage_model_cloud.usage_location.status = Status.INPUT

    if usage_dto.other_consumption_ratio is not None:
        usage_model_cloud.other_consumption_ratio.value = usage_dto.other_consumption_ratio
        usage_model_cloud.other_consumption_ratio.status = Status.INPUT

    if usage_dto.instance_per_server is not None:
        usage_model_cloud.instance_per_server.value = usage_dto.instance_per_server
        usage_model_cloud.instance_per_server.status = Status.INPUT

    return usage_model_cloud


def mapper_intensity_source(dto_intensity_source: IntensitySource) -> ModelIntensitySource:
    intensity_source = ModelIntensitySource()

    if dto_intensity_source.source is not None:
        intensity_source.source.value = dto_intensity_source.source
        intensity_source.source.status = Status.INPUT

    if dto_intensity_source.url is not None:
        intensity_source.url = dto_intensity_source.url

    if dto_intensity_source.stop_date is not None:
        intensity_source.stop_date.value = dto_intensity_source.stop_date
        intensity_source.stop_date.status = Status.INPUT

    if dto_intensity_source.start_date is not None:
        intensity_source.start_date.value = dto_intensity_source.start_date
        intensity_source.start_date.status = Status.INPUT

    if dto_intensity_source.token is not None:
        intensity_source.token = dto_intensity_source.token

    return intensity_source
