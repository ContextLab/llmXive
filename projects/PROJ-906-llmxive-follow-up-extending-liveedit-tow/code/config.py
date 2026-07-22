import os
import random
from typing import List, Set, Dict, Any, Optional, Union
import numpy as np
import torch
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    dataset: str = "davis"
    batch_size: int = 1
    num_steps: int = 50
    seed: int = 42
    output_dir: str = "data/metrics"
    checkpoint_dir: str = "data/checkpoints"
    # Sensitivity analysis cutoffs (FR-007)
    sensitivity_cutoffs: Set[float] = None
    # Stratification thresholds (Plan.md)
    stratification_thresholds: Set[float] = None

    def __post_init__(self):
        if self.sensitivity_cutoffs is None:
            self.sensitivity_cutoffs = {0.01, 0.05, 0.1}
        if self.stratification_thresholds is None:
            self.stratification_thresholds = {0.5, 5.0}

def get_default_config() -> ExperimentConfig:
    return ExperimentConfig()

def ensure_directories(*paths: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Create directories for given paths.
    Accepts:
      - ensure_directories() -> No-op
      - ensure_directories(path_str) -> Creates single path
      - ensure_directories(path_obj) -> Creates single path
      - ensure_directories([path1, path2, ...]) -> Creates all paths in list
      - ensure_directories(*paths) -> Creates all paths passed as args
      - ensure_directories(target_dir) -> Creates single path
    """
    if not paths:
        return

    # Flatten arguments
    all_paths = []
    for arg in paths:
        if isinstance(arg, (list, tuple)):
            all_paths.extend(arg)
        else:
            all_paths.append(arg)

    for p in all_paths:
        if p is None:
            continue
        path_obj = Path(p) if isinstance(p, str) else p
        path_obj.mkdir(parents=True, exist_ok=True)

def set_random_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
