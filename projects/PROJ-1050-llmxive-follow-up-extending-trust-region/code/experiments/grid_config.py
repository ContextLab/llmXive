"""
Experiment Configuration Grid Management.

Defines the GridConfig dataclass and utilities for creating and managing
experimental sweeps over hyperparameters like alpha and horizon.
"""
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

@dataclass
class GridConfig:
    """Configuration for a single experimental run within a grid search."""
    alpha: float
    student_horizon: int
    num_episodes: int
    seed: int
    output_dir: str
    log_file_name: str
    teacher_horizon: int = 20  # Fixed teacher horizon for now
    env_size: int = 10  # Default environment size
    learning_rate: float = 0.01
    max_steps_per_episode: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridConfig':
        return cls(**data)

def create_default_grid() -> List[GridConfig]:
    """
    Create a default list of GridConfig objects for a full sweep.

    Sweeps alpha in {0.1, 0.3, 0.5, 0.7, 0.9} and horizon in {3, 5, 7, 10, 15}.
    """
    alphas = [0.1, 0.3, 0.5, 0.7, 0.9]
    horizons = [3, 5, 7, 10, 15]
    base_seed = 42
    output_dir = "data/raw"

    configs = []
    for i, alpha in enumerate(alphas):
        for j, horizon in enumerate(horizons):
            seed = base_seed + i * 100 + j
            configs.append(GridConfig(
                alpha=alpha,
                student_horizon=horizon,
                num_episodes=50,
                seed=seed,
                output_dir=output_dir,
                log_file_name=f"exp_alpha{alpha}_horizon{horizon}.csv"
            ))
    return configs

def run_grid_search(configs: List[GridConfig], callback=None) -> List[Dict[str, Any]]:
    """
    Run a grid search over the provided configurations.

    Args:
        configs: List of GridConfig objects to run.
        callback: Optional callback function(config, result) to invoke after each run.

    Returns:
        List of result dictionaries.
    """
    results = []
    for idx, config in enumerate(configs):
        # In a real implementation, this would call the training runner
        # For now, we return a placeholder structure that the runner fills
        result = {
            "config": config.to_dict(),
            "status": "pending",
            "metrics": {}
        }
        if callback:
            callback(config, result)
        results.append(result)
    return results
