"""
Seed management for reproducible generation.
"""
import os
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class SeedManager:
    """Manages random seeds for generation groups."""
    def __init__(self, base_seed: int):
        self.base_seed = base_seed

    def get_seed(self, scene_id: str, group: str) -> int:
        """Get a deterministic seed for a scene and group."""
        data = f"{self.base_seed}:{scene_id}:{group}"
        hash_val = int(hashlib.sha256(data.encode()).hexdigest(), 16)
        return hash_val % (2**32)

def get_generation_seed(scene_id: str, group: str, base_seed: int) -> int:
    """Get a generation seed for a specific scene and group."""
    manager = SeedManager(base_seed)
    return manager.get_seed(scene_id, group)

def get_baseline_experimental_seeds(scene_id: str, base_seed: int) -> Tuple[int, int]:
    """Get seeds for Baseline and Experimental groups (must match)."""
    # Baseline and Experimental should use the SAME seed for fair comparison
    seed = get_generation_seed(scene_id, "Baseline", base_seed)
    return seed, seed

def main():
    """Entry point for seed manager."""
    pass