from fastapi import APIRouter, Body

from boaviztapi.dto.usage.usage import IntensitySource, mapper_intensity_source, Usage, smart_mapper_usage
from boaviztapi.model.component import Component
from boaviztapi.model.device import Device
from boaviztapi.service.verbose import verbose_usage

usage_router = APIRouter(
    prefix='/v1/usage_router',
    tags=['Usage Router']
)


@usage_router.post("/gwp/current_intensity")
async def get_intensity(itensity_source: IntensitySource = Body(None),
                        location: str = "global"):
    intensity_source = mapper_intensity_source(itensity_source)
    intensity = intensity_source.get_intensity(location)
    return intensity


@usage_router.post("/gwp/forcast_intensity")
async def get_intensity_forcast(itensity_source: IntensitySource = Body(None),
                                location: str = "global"):
    intensity_source = mapper_intensity_source(itensity_source)
    forcast = intensity_source.get_forcast(location)
    return forcast


@usage_router.post("/simple_usage")
async def get_simple_usage(usage: Usage = None):
    usage_model = smart_mapper_usage(usage)
    component = Component(usage=usage_model)
    return verbose_usage(component)
