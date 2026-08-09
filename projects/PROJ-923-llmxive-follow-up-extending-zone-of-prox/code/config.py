"""
Configuration loader and dataclasses.
"""
import os
import yaml
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class SeedConfig:
    seed: int = 42

@dataclass
class ThresholdConfig:
    cap_threshold_low: float = 0.1
    cap_threshold_high: float = 0.9
    min_candidates: int = 2

@dataclass
class PathConfig:
    data_dir: str = "data"
    output_dir: str = "data/metrics"
    config_path: str = "config.yaml"

@dataclass
class SimulationConfig:
    num_cycles: int = 50
    learning_rate: float = 0.01
    noise_sigma: float = 0.05

@dataclass
class Config:
    seed: SeedConfig = field(default_factory=SeedConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def load_yaml_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def create_default_config() -> Config:
    return Config()

def save_default_config(path: str):
    config = create_default_config()
    with open(path, 'w') as f:
        yaml.dump(asdict(config), f)

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    if path is None:
        path = "config.yaml"
    return load_yaml_config(path)

def get_config_paths() -> Dict[str, str]:
    return {
        "data": "data",
        "output": "data/metrics"
    }

def validate_config(config: Dict[str, Any]) -> bool:
    # Basic validation
    required = ['seed', 'simulation']
    for key in required:
        if key not in config:
            logger.error(f"Missing config key: {key}")
            return False
    return True

def get_config(path: Optional[str] = None) -> Config:
    raw = load_config(path)
    # Map raw dict to dataclass if needed, or return dict
    return raw