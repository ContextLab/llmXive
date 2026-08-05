import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch
import yaml

class Config:
    def __init__(self, **kwargs):
        # Default values
        self.model_name = "distilbert-base-uncased"
        self.dataset_name = "glue"
        self.subset = "sst2" # Example subset
        self.max_steps = 50
        self.warmup_steps = 10
        self.dream_ratio = 0.25
        self.dream_temperature_sweep = [0.5, 0.7, 0.9]
        self.num_seeds = 5
        self.max_wall_clock_hours = 5.0
        self.memory_limit_gb = 6.0
        self.results_dir = Path("data/results")
        self.checkpoints_dir = Path("data/checkpoints")
        self.log_dir = Path("data/logs")
        
        # Update with provided kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def load(cls, path: str) -> "Config":
        """Load config from a YAML file."""
        if not os.path.exists(path):
            # Return default config if file not found, or raise error
            # For robustness in sweep, we might want defaults
            logger.warning(f"Config file {path} not found. Using defaults.")
            return cls()
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

# Helper to get logger if needed in config init, but imported later to avoid circular
from utils.logger import get_logger
logger = get_logger(__name__)
