import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

class Config:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.project = data.get("project", {})
        self.paths = data.get("paths", {})
        self.simulation = data.get("simulation", {})
        self.mmlu = data.get("mmlu", {})
        self.logging = data.get("logging", {})

    @property
    def seed(self) -> int:
        return self.project.get("seed", 42)

    @property
    def data_dir(self) -> Path:
        return Path(self.paths.get("data_dir", "data"))

    @property
    def output_dir(self) -> Path:
        return Path(self.paths.get("output_dir", "data/metrics"))

    @property
    def figures_dir(self) -> Path:
        return Path(self.paths.get("figures_dir", "data/figures"))

    @property
    def buffer_cycles(self) -> int:
        return self.simulation.get("buffer_cycles", 100)

    @property
    def noise_sigma(self) -> float:
        return self.simulation.get("noise_sigma", 0.05)

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = reload_config()
    return _config

def reload_config() -> Config:
    global _config
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)
    _config = Config(data)
    return _config
