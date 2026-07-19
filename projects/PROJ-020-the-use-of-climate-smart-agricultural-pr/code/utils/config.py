import os
import sys
from pathlib import Path
from typing import List, Optional, Set

class ConfigError(Exception):
    pass

class Config:
    def __init__(self):
        self._target_countries = ["Kenya", "India", "Vietnam"]
        self._target_years = [2015, 2016, 2017, 2018, 2019, 2020]
        self._data_dir = Path(os.getenv("DATA_DIR", "data"))
        self._max_ram_gb = int(os.getenv("MAX_RAM_GB", 7))

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
    return get_config().target_countries

def get_target_years() -> List[int]:
    return get_config().target_years

def get_data_dir() -> Path:
    return get_config().data_dir

def get_raw_data_dir() -> Path:
    return get_data_dir() / "raw"

def get_processed_data_dir() -> Path:
    return get_data_dir() / "processed"

def get_state_dir() -> Path:
    return get_data_dir() / "state"

def get_max_ram_gb() -> int:
    return get_config().max_ram_gb

def get_memory_limit_bytes() -> int:
    return get_max_ram_gb() * 1024 * 1024 * 1024
