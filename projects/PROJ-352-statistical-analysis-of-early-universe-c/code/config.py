"""
Configuration management for the CMB analysis pipeline.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

@dataclass
class Config:
    """Project configuration container."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    data_raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    data_processed_dir: Path = field(default_factory=lambda: Path("data/processed"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    log_level: str = "INFO"
    random_seed: int = 42
    planck_release: str = "2018"
    nside: int = 128
    beam_fwhm_arcmin: float = 5.0
    noise_sigma_muK: float = 1.1
    
    def __post_init__(self):
        # Ensure paths are absolute relative to project root
        self.data_dir = self.project_root / self.data_dir
        self.data_raw_dir = self.project_root / self.data_raw_dir
        self.data_processed_dir = self.project_root / self.data_processed_dir
        self.output_dir = self.project_root / self.output_dir

_config: Optional[Config] = None

def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def update_config(**kwargs) -> Config:
    """Update configuration with provided values."""
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown config key: {key}")
    return config
