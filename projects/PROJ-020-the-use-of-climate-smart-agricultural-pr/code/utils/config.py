import os
import sys
from pathlib import Path
from typing import List, Optional, Set

class ConfigError(Exception):
    pass

class Config:
    def __init__(self):
        self._target_countries: List[str] = ["KEN", "IND", "VNM"]
        self._target_years: List[int] = [2015, 2020, 2023]
        self._data_dir: Path = Path("data")
        self._max_ram_gb: int = 7

    def set_target_countries(self, countries: List[str]):
        self._target_countries = countries

    def set_target_years(self, years: List[int]):
        self._target_years = years

    def set_data_dir(self, path: Path):
        self._data_dir = path

    def set_max_ram_gb(self, gb: int):
        self._max_ram_gb = gb

    @property
    def target_countries(self) -> List[str]:
        return self._target_countries

    @property
    def target_years(self) -> List[int]:
        return self._target_years

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def max_ram_gb(self) -> int:
        return self._max_ram_gb

_config = Config()

def get_config() -> Config:
    return _config

def reset_config():
    global _config
    _config = Config()

def get_target_countries() -> List[str]:
    return _config.target_countries

def get_target_years() -> List[int]:
    return _config.target_years

def get_data_dir() -> Path:
    return _config.data_dir

def get_raw_data_dir() -> Path:
    return _config.data_dir / "raw"

def get_processed_data_dir() -> Path:
    return _config.data_dir / "processed"

def get_state_dir() -> Path:
    return _config.data_dir / "state"

def get_max_ram_gb() -> int:
    return _config.max_ram_gb

def get_memory_limit_bytes() -> int:
    return _config.max_ram_gb * 1024 * 1024 * 1024
