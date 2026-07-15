from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class Config:
    seed: int = 42
    max_ram_gb: float = 7.0
    max_runtime_hours: float = 6.0

# Singleton instance or factory
def get_config() -> Config:
    return Config()
