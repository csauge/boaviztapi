from typing import Optional, List

from boaviztapi.dto.component import CPU, RAM, Disk, PowerSupply
from boaviztapi.dto.usage import UsageServer, UsageCloud
from boaviztapi.dto import BaseDTO


class DeviceDTO(BaseDTO):
    pass


class ModelServer(BaseDTO):
    manufacturer: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    year: Optional[str] = None
    archetype: Optional[str] = None


class ConfigurationServer(BaseDTO):
    cpu: Optional[CPU] = None
    ram: Optional[List[RAM]] = None
    disk: Optional[List[Disk]] = None
    power_supply: Optional[PowerSupply] = None


class Server(DeviceDTO):
    model: Optional[ModelServer] = None
    configuration: Optional[ConfigurationServer] = None
    usage: Optional[UsageServer] = None


class Cloud(Server):
    usage: Optional[UsageCloud] = None