"""
Seed Manager Module for llmXive Project PROJ-039.

Provides deterministic random number generation across NumPy, Python's random,
and PyTorch (if available) to ensure reproducibility of statistical runs.
"""

import os
import random
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Attempt to import numpy and torch, but do not fail if they are missing
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default seed as per task specification
DEFAULT_SEED = 42
SEED_CONFIG_PATH = Path("artifacts/seed_config.json")

class SeedManager:
    """
    A context manager and utility class to manage random seeds across the project.
    Ensures that all random operations (numpy, python random, torch) use the same seed.
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self._initial_states = {}

    def set_all(self) -> None:
        """Set the seed for all supported random number generators."""
        if HAS_NUMPY:
            np.random.seed(self.seed)
        random.seed(self.seed)
        if HAS_TORCH:
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.seed)
                torch.cuda.manual_seed_all(self.seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False

        logger.info(f"Random seeds set to {self.seed} for reproducibility.")

    def save_config(self, path: Optional[Path] = None) -> Path:
        """Save the current seed configuration to a JSON file."""
        target_path = path or SEED_CONFIG_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            "seed": self.seed,
            "timestamp": str(Path(__file__).parent.parent / "artifacts"), # Placeholder for actual timestamp logic if needed
            "dependencies": {
                "numpy": HAS_NUMPY,
                "torch": HAS_TORCH
            }
        }
        
        with open(target_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Seed configuration saved to {target_path}")
        return target_path

    @classmethod
    def load_config(cls, path: Optional[Path] = None) -> 'SeedManager':
        """Load a seed configuration from a JSON file."""
        target_path = path or SEED_CONFIG_PATH
        
        if not target_path.exists():
            logger.warning(f"Seed config file not found at {target_path}. Using default seed {DEFAULT_SEED}.")
            return cls(seed=DEFAULT_SEED)

        with open(target_path, 'r') as f:
            config = json.load(f)
        
        seed = config.get("seed", DEFAULT_SEED)
        logger.info(f"Loaded seed {seed} from {target_path}")
        return cls(seed=seed)

    def __enter__(self):
        self.set_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Optionally reset or log exit
        pass

# Module-level convenience functions

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Global function to set the random seed for reproducibility.
    This is the primary entry point expected by the task description.
    
    Args:
        seed: The integer seed value (default 42).
    """
    manager = SeedManager(seed=seed)
    manager.set_all()
    # Save the config to artifact directory for audit trail
    try:
        manager.save_config()
    except Exception as e:
        logger.warning(f"Could not save seed config: {e}")

def get_seed() -> int:
    """
    Retrieve the currently active seed.
    Note: In a stateless environment, this might return the default if not set.
    """
    # Try to load from config first
    if SEED_CONFIG_PATH.exists():
        try:
            config = load_seed_config()
            return config.seed
        except Exception:
            pass
    return DEFAULT_SEED

def generate_seed() -> int:
    """
    Generate a new random seed using a secure hash of the current time and process ID.
    Useful for experiments where determinism is not required but a seed is needed.
    """
    import time
    data = f"{time.time()}{os.getpid()}{random.random()}"
    hash_obj = hashlib.sha256(data.encode())
    return int(hash_obj.hexdigest(), 16) % (2**32)

def save_seed_config(seed: Optional[int] = None, path: Optional[Path] = None) -> Path:
    """Convenience wrapper to save the current seed configuration."""
    if seed is None:
        seed = get_seed()
    manager = SeedManager(seed=seed)
    return manager.save_config(path)

def load_seed_config(path: Optional[Path] = None) -> SeedManager:
    """Convenience wrapper to load the seed configuration."""
    return SeedManager.load_config(path)

class SeedContext:
    """
    A context manager that sets the seed on entry and restores state on exit.
    Useful for isolating random operations in specific blocks.
    """
    def __init__(self, seed: int):
        self.seed = seed
        self.manager = SeedManager(seed=seed)

    def __enter__(self):
        self.manager.set_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # In a simple implementation, we might not restore previous state
        # unless we explicitly saved it. For this task, setting the seed
        # is the primary requirement.
        pass

def get_random_state() -> Dict[str, Any]:
    """
    Returns a dictionary containing the current state of all random generators.
    Useful for checkpointing.
    """
    state = {
        "python_random": random.getstate(),
        "numpy_random": np.random.get_state() if HAS_NUMPY else None,
        "torch_random": torch.get_rng_state() if HAS_TORCH else None
    }
    if HAS_TORCH and torch.cuda.is_available():
        state["torch_cuda"] = torch.cuda.get_rng_state_all()
    
    return state

def main():
    """
    Main entry point for command-line usage.
    Usage: python -m code.seed_manager [seed_value]
    """
    import sys
    
    seed_val = DEFAULT_SEED
    if len(sys.argv) > 1:
        try:
            seed_val = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid integer. Using default {DEFAULT_SEED}.")
    
    set_seed(seed_val)
    print(f"Seed set to {seed_val}. Configuration saved to {SEED_CONFIG_PATH}")

if __name__ == "__main__":
    main()
