"""
Grid configuration utilities for the experimental sweep.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List
import numpy as np

@dataclass
class GridConfig:
    """
    Hyper‑parameter configuration for a single experiment run.
    """
    alpha: float
    horizon: int
    seed: int = 42

def create_default_grid() -> List[GridConfig]:
    """
    Generate the default hyper‑parameter grid.

    Returns
    -------
    List[GridConfig]
        Configurations covering the alpha sweep {0.1,0.3,0.5,0.7,0.9}
        and a modest set of horizon values.
    """
    alphas = [0.1, 0.3, 0.5, 0.7, 0.9]
    horizons = [3, 5, 7]
    grid: List[GridConfig] = []
    for a in alphas:
        for h in horizons:
            # Use a deterministic seed based on the pair (alpha, horizon)
            seed = int(a * 1000) + h
            grid.append(GridConfig(alpha=a, horizon=h, seed=seed))
    return grid
