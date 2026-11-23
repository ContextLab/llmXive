import yaml
import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(config_path: str = "code/config.yaml") -> Optional[Dict[str, Any]]:
    """
    Load and validate configuration from a YAML file.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")

    # Basic validation
    required_keys = ["global_seed", "topology_targets", "thresholds"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    return config

def set_seed(seed: int) -> None:
    """
    Set global random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: networkx functions use their own random_state parameter,
    # which is handled by passing the seed explicitly in generators.
