import os
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class SeedManager:
    """
    Manages random seeds for the image generation pipeline.
    Ensures reproducibility by deriving seeds from scene IDs and group types.
    """
    
    def __init__(self, base_seed: int = 42):
        self.base_seed = base_seed
        self._control_seeds: Dict[str, int] = {}
        self._be_seeds: Dict[str, Tuple[int, int]] = {} # (seed, step_seed)

    def _derive_seed(self, scene_id: str, group: str, salt: str = "") -> int:
        """Derives a deterministic seed from a scene ID and group."""
        payload = f"{self.base_seed}:{scene_id}:{group}:{salt}"
        hash_obj = hashlib.sha256(payload.encode('utf-8'))
        # Convert first 8 hex chars to int
        seed_int = int(hash_obj.hexdigest()[:16], 16)
        return seed_int

    def get_baseline_experimental_seeds(self, scene_id: str) -> Tuple[int, int]:
        """
        Returns the seed pair for Baseline and Experimental groups.
        They share the same primary seed for the same scene_id to ensure comparability.
        Returns: (primary_seed, step_seed)
        """
        if scene_id in self._be_seeds:
            return self._be_seeds[scene_id]
        
        # Derive a primary seed for the scene
        primary_seed = self._derive_seed(scene_id, "baseline_exp")
        # Derive a secondary seed for step scheduler variation if needed
        step_seed = self._derive_seed(scene_id, "baseline_exp", salt="step")
        
        self._be_seeds[scene_id] = (primary_seed, step_seed)
        return (primary_seed, step_seed)

    def get_control_seed(self, scene_id: str) -> int:
        """
        Returns the seed for the Control group.
        It is distinct from Baseline/Experimental but consistent for the same scene_id.
        """
        if scene_id in self._control_seeds:
            return self._control_seeds[scene_id]
        
        # Use a distinct salt to ensure it differs from BE seeds
        control_seed = self._derive_seed(scene_id, "control")
        self._control_seeds[scene_id] = control_seed
        return control_seed

def get_generation_seed(scene_id: str, group: str, base_seed: int = 42) -> int:
    """
    Convenience wrapper to get a seed for a specific scene and group.
    
    Args:
        scene_id: Unique identifier for the scene.
        group: One of 'baseline', 'experimental', 'control'.
        base_seed: Global base seed for reproducibility.
    
    Returns:
        An integer seed.
    """
    manager = SeedManager(base_seed=base_seed)
    
    if group.lower() in ['baseline', 'experimental']:
        # For BE, we return the primary seed. The step seed can be used internally 
        # by the diffusion runner if needed for scheduler noise.
        return manager.get_baseline_experimental_seeds(scene_id)[0]
    elif group.lower() == 'control':
        return manager.get_control_seed(scene_id)
    else:
        raise ValueError(f"Unknown group: {group}. Must be 'baseline', 'experimental', or 'control'.")

def get_baseline_experimental_seeds(scene_id: str, base_seed: int = 42) -> Tuple[int, int]:
    """
    Returns the (primary_seed, step_seed) tuple for Baseline/Experimental groups.
    """
    manager = SeedManager(base_seed=base_seed)
    return manager.get_baseline_experimental_seeds(scene_id)

def main():
    """
    CLI entry point to test seed generation logic.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m generation.seed_manager <scene_id> [group]")
        sys.exit(1)
    
    scene_id = sys.argv[1]
    group = sys.argv[2] if len(sys.argv) > 2 else "baseline"
    
    base_seed = 42
    
    if group.lower() in ['baseline', 'experimental']:
        primary, step = get_baseline_experimental_seeds(scene_id, base_seed)
        print(f"Scene: {scene_id}, Group: {group}")
        print(f"  Primary Seed: {primary}")
        print(f"  Step Seed: {step}")
    elif group.lower() == 'control':
        seed = get_control_seed(scene_id, base_seed)
        print(f"Scene: {scene_id}, Group: {control}")
        print(f"  Control Seed: {seed}")
    else:
        print(f"Error: Invalid group '{group}'")
        sys.exit(1)

if __name__ == "__main__":
    main()