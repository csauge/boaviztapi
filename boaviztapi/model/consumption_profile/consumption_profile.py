import dataclasses
import math
import os
from typing import Dict, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

import boaviztapi.utils.fuzzymatch as fuzzymatch
from boaviztapi.dto.usage.usage import WorkloadTime
from boaviztapi.model.boattribute import Boattribute, Status

fuzzymatch.pandas()

_cpu_profile_consumption_df = pd.read_csv(os.path.join(os.path.dirname(__file__),
                                                       '../../data/consumption_profile/cpu/cpu_profile.csv'))


class ConsumptionProfileModel:
    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value


class RAMConsumptionProfileModel(ConsumptionProfileModel):
    DEFAULT_RAM_CAPACITY = 15
    DEFAULT_WORKLOADS = None
    RAM_ELECTRICAL_FACTOR_PER_GO = 0.284

    _DEFAULT_MODEL_PARAMS = {
        'a': DEFAULT_RAM_CAPACITY * RAM_ELECTRICAL_FACTOR_PER_GO
    }

    def __init__(self):
        self.workloads = Boattribute(
            default=self.DEFAULT_WORKLOADS,
            unit="workload_rate:W"
        )
        self.params = Boattribute(default=self._DEFAULT_MODEL_PARAMS)

    def compute_consumption_profile_model(self, ram_capacity: int = DEFAULT_RAM_CAPACITY) -> int:
        self.params.value = {'a': self.RAM_ELECTRICAL_FACTOR_PER_GO * ram_capacity}
        self.params.status = Status.COMPLETED
        self.params.source = f"(ram_electrical_factor_per_go : {self.RAM_ELECTRICAL_FACTOR_PER_GO}) * (" \
                             f"ram_capacity: {ram_capacity}) "
        return self.params.value

    def apply_consumption_profile(self, load_percentage: float) -> float:
        return self.params.value['a']

    def apply_multiple_workloads(self, time_workload: List[WorkloadTime]) -> float:
        total = 0
        for workload in time_workload:
            total += (workload.time_percentage / 100) * self.apply_consumption_profile(workload.load_percentage)
        return total


class CPUConsumptionProfileModel(ConsumptionProfileModel):
    DEFAULT_CPU_MODEL_RANGE = 'Xeon Platinum'
    DEFAULT_WORKLOADS = None

    _DEFAULT_MODEL_PARAMS = {
        'a': 171.2,
        'b': 0.0354,
        'c': 36.89,
        'd': -10.13
    }

    _TDP_RATIOS_WORKLOAD = [0, 10, 50, 100]
    _TDP_RATIOS = [0.12, 0.32, 0.75, 1.02]

    _DEFAULT_MODEL_BOUNDS = (
        [0, 0, 0, -math.inf],
        [math.inf, math.inf, math.inf, math.inf]
    )
    _MODEL_PARAM_NAME = ['a', 'b', 'c', 'd']

    def __init__(self):
        self.workloads = Boattribute(
            default=self.DEFAULT_WORKLOADS,
            unit="workload_rate:W"
        )
        self.params = Boattribute(default=self._DEFAULT_MODEL_PARAMS)

    @property
    def list_workloads(self) -> Tuple[List[float], List[float]]:
        load = [item.load_percentage for item in self.workloads.value]
        power = [item.power_watt for item in self.workloads.value]
        return load, power

    def apply_consumption_profile(self, load_percentage: float) -> float:
        return self.__log_model(
            load_percentage,
            self.params.value['a'],
            self.params.value['b'],
            self.params.value['c'],
            self.params.value['d']
        )

    def apply_multiple_workloads(self, time_workload: List[WorkloadTime]) -> float:
        total = 0
        for workload in time_workload:
            total += (workload.time_percentage / 100) * self.apply_consumption_profile(workload.load_percentage)
        return total

    def compute_consumption_profile_model(self,
                                          cpu_manufacturer: str = None,
                                          cpu_model_range: str = None,
                                          cpu_tdp: int = None) -> Union[Dict[str, float], None]:
        model = self.lookup_consumption_profile(cpu_manufacturer, cpu_model_range)
        if self.workloads.is_set():
            model = self.__compute_model_adaptation(base_model=model or self._DEFAULT_MODEL_PARAMS)
            self.params.set_completed(model, source="From workload")

        elif cpu_tdp is not None:
            model = self.__compute_model_adaptation_with_tdp(
                base_model=model or self._DEFAULT_MODEL_PARAMS,
                cpu_tdp=cpu_tdp
            )
            self.params.set_completed(model, source="From TDP")

        elif cpu_model_range is not None:
            self.params.set_completed(model, source="From CPU model range")

        else:
            self.params.set_default(self._DEFAULT_MODEL_PARAMS)

        return self.params.value

    def __compute_model_adaptation_with_tdp(self, base_model: Dict[str, float], cpu_tdp: float) -> Dict[str, float]:
        @dataclasses.dataclass
        class _TDPWorkloadPower:
            load_percentage: float = None
            power_watt: float = None
        self.workloads.set_completed([
            _TDPWorkloadPower(load_percentage=w, power_watt=cpu_tdp * r)
            for w, r in zip(self._TDP_RATIOS_WORKLOAD, self._TDP_RATIOS)
        ])
        return self.__compute_model_adaptation(base_model=base_model)

    def __compute_model_adaptation(self, base_model: Dict[str, float]) -> Dict[str, float]:
        base_model_list = self.__model_dict_to_list(base_model)
        bounds = self.__adapt_model_bounds(base_model_list)
        x_data, y_data = self.list_workloads
        popt, _ = curve_fit(f=self.__log_model,
                            xdata=x_data,
                            ydata=y_data,
                            p0=base_model_list,
                            bounds=bounds)
        return self.__model_list_to_dict(popt.tolist())

    def __adapt_model_bounds(self, base_model_list: List[float]) -> Tuple[List[float], List[float]]:
        default_lower_bounds, default_upper_bounds = self._DEFAULT_MODEL_BOUNDS
        lower_bounds, upper_bounds = [], []
        for lower_b, upper_b, model_param in zip(default_lower_bounds, default_upper_bounds, base_model_list):
            lower_bounds.append(max(lower_b, model_param - abs(0.5 * model_param)))
            upper_bounds.append(min(upper_b, model_param + abs(1.5 * model_param)))
        return lower_bounds, upper_bounds

    def __model_dict_to_list(self, model: Dict[str, float]) -> List[float]:
        return [model[param_name] for param_name in self._MODEL_PARAM_NAME]

    def __model_list_to_dict(self, model: List[float]) -> Dict[str, float]:
        return {param_name: param for param_name, param in zip(self._MODEL_PARAM_NAME, model)}

    @staticmethod
    def __log_model(x: float, a: float, b: float, c: float, d: float) -> float:
        return a * np.log(b * (x + c)) + d

    @staticmethod
    def lookup_consumption_profile(
            cpu_manufacturer: str = None,
            cpu_model_range: str = None
    ) -> Optional[Dict[str, float]]:
        sub = _cpu_profile_consumption_df

        if cpu_manufacturer is not None:
            tmp = sub[sub['manufacturer'].fuzzymatch(cpu_manufacturer)]
            if len(tmp) > 0:
                sub = tmp.copy()

        if cpu_model_range is not None:
            tmp = sub[sub['model_range'].fuzzymatch(cpu_model_range)]
            if len(tmp) > 0:
                sub = tmp.copy()

        if len(sub) == 1:
            row = sub.iloc[0]
            return {
                'a': row.a,
                'b': row.b,
                'c': row.c,
                'd': row.d,
            }
