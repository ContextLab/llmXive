import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Configuration management for the project."""
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    
    # Drift analysis paths
    drift_metrics: str = "outputs/drift_metrics.csv"
    drift_metrics_final: str = "outputs/drift_metrics.csv"
    
    def __post_init__(self):
        self.data_dir = self.project_root / "data"
        self.outputs_dir = self.project_root / "outputs"

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config():
    global _config_instance
    _config_instance = None

def load_config_from_env():
    """Load configuration from environment variables if present."""
    # Placeholder for future env loading
    pass

def main():
    print("Configuration module loaded.")

if __name__ == "__main__":
    main()
