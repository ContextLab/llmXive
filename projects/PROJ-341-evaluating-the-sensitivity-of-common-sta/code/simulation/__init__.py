# Simulation package
import os
import json
from typing import Optional
from datetime import datetime

_SEED_MANAGER = None

class SeedManager:
    def __init__(self, base_seed: int = 42):
        self.base_seed = base_seed
        self.current_seed = base_seed
        self.history = []

    def get_seed(self) -> int:
        seed = self.current_seed
        self.current_seed += 1
        self.history.append(seed)
        return seed

    def reset(self, base_seed: int = 42):
        self.base_seed = base_seed
        self.current_seed = base_seed
        self.history = []

def get_seed_manager() -> SeedManager:
    global _SEED_MANAGER
    if _SEED_MANAGER is None:
        _SEED_MANAGER = SeedManager()
    return _SEED_MANAGER

def get_rng(base_seed: Optional[int] = None):
    import numpy as np
    if base_seed is not None:
        return np.random.default_rng(base_seed)
    return np.random.default_rng(get_seed_manager().get_seed())

def set_seed(base_seed: int):
    get_seed_manager().reset(base_seed)
