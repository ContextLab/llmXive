import os
import random
from typing import List, Set, Dict, Any, Optional
import numpy as np
import torch

# Constants from Spec FR-007 and Plan.md Dataset Strategy
SENSITIVITY_CUTOFFS: Set[float] = {0.01, 0.05, 0.1}
STRATIFICATION_THRESHOLDS: Set[float] = {0.5, 5.0}

# Random seeds for reproducibility
RANDOM_SEED = 42

class ExperimentConfig:
    def __init__(self, dataset: str = "davis", model: str = "baseline", output_dir: str = "data/metrics"):
        self.dataset = dataset
        self.model = model
        self.output_dir = output_dir
        self.seed = RANDOM_SEED
        self.sensitivity_cutoffs = SENSITIVITY_CUTOFFS
        self.stratification_thresholds = STRATIFICATION_THRESHOLDS

def get_default_config() -> ExperimentConfig:
    return ExperimentConfig()

def ensure_directories(*paths: Any) -> None:
    """
    Robust directory creation utility that handles multiple call signatures:
    1. ensure_directories() -> No-op
    2. ensure_directories(path_str) -> Creates single path
    3. ensure_directories(path_obj) -> Creates single path
    4. ensure_directories([path1, path2, ...]) -> Creates all paths in list
    5. ensure_directories(*paths) -> Creates all paths passed as args
    """
    if not paths:
        return

    # Flatten the input into a list of paths to process
    paths_to_create = []
    for p in paths:
        if isinstance(p, (list, tuple)):
            paths_to_create.extend(p)
        else:
            paths_to_create.append(p)

    for p in paths_to_create:
        if p is None:
            continue
        # Convert to string if it's a Path object or similar
        path_str = str(p)
        if path_str:
            os.makedirs(path_str, exist_ok=True)