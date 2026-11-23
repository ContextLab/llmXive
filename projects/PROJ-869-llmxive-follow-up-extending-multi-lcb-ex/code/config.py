import os
import json
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Config:
    """Project configuration management."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_root: Path = field(init=False)
    code_root: Path = field(init=False)
    tests_root: Path = field(init=False)
    specs_root: Path = field(init=False)
    
    # Paths
    RAW_DATA_DIR: Path = field(init=False)
    PROCESSED_DATA_DIR: Path = field(init=False)
    ANCHORS_PATH: str = "data/anchors.json"
    FEASIBILITY_LOG_PATH: str = "data/feasibility_log.json"
    POWER_CHECK_PATH: str = "data/power_check.yaml"
    PIPELINE_STATE_PATH: str = "data/pipeline_state.json"
    
    # Seeds
    RANDOM_SEED: int = 42

    def __post_init__(self):
        self.data_root = self.project_root / "data"
        self.code_root = self.project_root / "code"
        self.tests_root = self.project_root / "tests"
        self.specs_root = self.project_root / "specs"
        
        self.RAW_DATA_DIR = self.data_root / "raw"
        self.PROCESSED_DATA_DIR = self.data_root / "processed"

config = Config()

def get_path(path_str: str) -> Path:
    """Resolve a path relative to project root."""
    return config.project_root / path_str

# Expose specific paths for convenience
ANCHORS_PATH = config.ANCHORS_PATH
FEASIBILITY_LOG_PATH = config.FEASIBILITY_LOG_PATH
POWER_CHECK_PATH = config.POWER_CHECK_PATH
PIPELINE_STATE_PATH = config.PIPELINE_STATE_PATH
