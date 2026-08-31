import os
import random
from typing import List, Set, Dict, Any, Optional, Union
import numpy as np
import torch
from pathlib import Path

# Constants for Sensitivity Analysis (FR-007)
SENSITIVITY_CUTOFFS: Set[float] = {0.01, 0.05, 0.1}

# Thresholds for Stratification (Plan.md)
STRATIFICATION_THRESHOLDS: Set[float] = {0.5, 5.0}

# Random seeds
DEFAULT_SEED = 42

class ExperimentConfig:
    """Configuration container for the experiment."""
    def __init__(
        self,
        dataset: str = "davis",
        flow_method: str = "farneback",
        model: str = "baseline",
        output_dir: str = "data",
        seed: int = DEFAULT_SEED,
    ):
        self.dataset = dataset
        self.flow_method = flow_method
        self.model = model
        self.output_dir = output_dir
        self.seed = seed

def get_default_config() -> ExperimentConfig:
    """Return the default experiment configuration."""
    return ExperimentConfig()

def get_default_config_dict() -> Dict[str, Any]:
    """Return the default configuration as a dictionary."""
    cfg = get_default_config()
    return {
        "dataset": cfg.dataset,
        "flow_method": cfg.flow_method,
        "model": cfg.model,
        "output_dir": cfg.output_dir,
        "seed": cfg.seed,
    }

def ensure_directories(*paths: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Create directories for the given paths.
    Accepts:
      - No args (no-op)
      - Single string or Path
      - List of strings/Paths
      - Multiple string/Path args
    """
    if not paths:
        return

    # Normalize inputs into a flat list of paths
    path_list: List[Path] = []
    for p in paths:
        if isinstance(p, (list, tuple)):
            path_list.extend([Path(x) for x in p])
        elif isinstance(p, Path):
            path_list.append(p)
        elif isinstance(p, str):
            path_list.append(Path(p))
        else:
            # Ignore unexpected types
            continue

    for p in path_list:
        p.mkdir(parents=True, exist_ok=True)

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)