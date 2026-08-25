"""
Random seed management utility for llmXive project PROJ-039.

This module ensures reproducibility across statistical runs by providing a centralized
mechanism to set, retrieve, and propagate random seeds for numpy, random, and torch (if available).
It also supports context managers for temporary seed scoping and saving/loading seed configurations.
"""
import os
import random
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, Generator, List

# Try to import numpy and torch, but don't fail if they aren't installed
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

from config import get_project_root

# Constants
DEFAULT_SEED = 42
SEED_CONFIG_FILE = "artifacts/seed_config.json"
LOG_MESSAGE = "Seed set to: {seed}"

logger = logging.getLogger(__name__)


class SeedManager:
    """
    Centralized manager for random seed operations.
    Ensures all random number generators are seeded consistently.
    """
    
    _current_seed: Optional[int] = None
    
    @classmethod
    def set_seed(cls, seed: Optional[int] = None, persist: bool = False) -> int:
        """
        Set the random seed for all supported libraries.
        
        Args:
            seed: The seed value. If None, generates a new random seed.
            persist: If True, saves the seed to the project's seed config file.
        
        Returns:
            The seed value that was set.
        """
        if seed is None:
            seed = cls.generate_seed()
        
        cls._current_seed = seed
        
        # Seed Python's random module
        random.seed(seed)
        
        # Seed numpy if available
        if HAS_NUMPY and np is not None:
            np.random.seed(seed)
        
        # Seed torch if available
        if HAS_TORCH and torch is not None:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        
        logger.info(LOG_MESSAGE.format(seed=seed))
        
        if persist:
            cls.save_seed_config(seed)
        
        return seed
    
    @classmethod
    def get_seed(cls) -> Optional[int]:
        """
        Get the currently set seed.
        
        Returns:
            The current seed value, or None if not set.
        """
        return cls._current_seed
    
    @classmethod
    def generate_seed(cls) -> int:
        """
        Generate a new random seed using system entropy.
        
        Returns:
            A new random integer seed.
        """
        # Use system time and random bytes for entropy
        seed_bytes = os.urandom(4)
        seed = int.from_bytes(seed_bytes, byteorder='big')
        return seed
    
    @classmethod
    def save_seed_config(cls, seed: int, filepath: Optional[str] = None) -> None:
        """
        Save the seed configuration to a JSON file.
        
        Args:
            seed: The seed value to save.
            filepath: Optional custom filepath. Defaults to project's seed config file.
        """
        if filepath is None:
            filepath = SEED_CONFIG_FILE
        
        project_root = get_project_root()
        config_path = project_root / filepath
        
        # Ensure artifacts directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            "seed": seed,
            "algorithm": "system_entropy",
            "timestamp": str(random.getstate()[1][0] if hasattr(random.getstate(), '__getitem__') else 0)
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Seed configuration saved to {config_path}")
    
    @classmethod
    def load_seed_config(cls, filepath: Optional[str] = None) -> Optional[int]:
        """
        Load the seed configuration from a JSON file.
        
        Args:
            filepath: Optional custom filepath. Defaults to project's seed config file.
        
        Returns:
            The loaded seed value, or None if file doesn't exist or is invalid.
        """
        if filepath is None:
            filepath = SEED_CONFIG_FILE
        
        project_root = get_project_root()
        config_path = project_root / filepath
        
        if not config_path.exists():
            logger.warning(f"Seed config file not found: {config_path}")
            return None
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            seed = config_data.get("seed")
            if seed is not None:
                logger.info(f"Loaded seed from {config_path}: {seed}")
                return seed
            else:
                logger.warning(f"Invalid seed config format in {config_path}")
                return None
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load seed config: {e}")
            return None
    
    @classmethod
    def get_random_state(cls, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the current random state for reproducibility debugging.
        
        Args:
            seed: Optional seed to set before getting state.
        
        Returns:
            A dictionary containing the random states of all supported libraries.
        """
        if seed is not None:
            cls.set_seed(seed)
        
        state = {
            "python_random": random.getstate(),
            "numpy_random": None,
            "torch_random": None
        }
        
        if HAS_NUMPY and np is not None:
            state["numpy_random"] = np.random.get_state()
        
        if HAS_TORCH and torch is not None:
            state["torch_random"] = torch.get_rng_state()
            if torch.cuda.is_available():
                state["torch_cuda"] = torch.cuda.get_rng_state_all()
        
        return state


def set_seed(seed: Optional[int] = None, persist: bool = False) -> int:
    """
    Convenience function to set the random seed.
    
    Args:
        seed: The seed value. If None, generates a new random seed.
        persist: If True, saves the seed to the project's seed config file.
    
    Returns:
        The seed value that was set.
    """
    return SeedManager.set_seed(seed, persist)


def get_seed() -> Optional[int]:
    """
    Convenience function to get the current seed.
    
    Returns:
        The current seed value, or None if not set.
    """
    return SeedManager.get_seed()


def generate_seed() -> int:
    """
    Convenience function to generate a new random seed.
    
    Returns:
        A new random integer seed.
    """
    return SeedManager.generate_seed()


def save_seed_config(seed: int, filepath: Optional[str] = None) -> None:
    """
    Convenience function to save the seed configuration.
    
    Args:
        seed: The seed value to save.
        filepath: Optional custom filepath.
    """
    SeedManager.save_seed_config(seed, filepath)


def load_seed_config(filepath: Optional[str] = None) -> Optional[int]:
    """
    Convenience function to load the seed configuration.
    
    Args:
        filepath: Optional custom filepath.
    
    Returns:
        The loaded seed value, or None if not found.
    """
    return SeedManager.load_seed_config(filepath)


class SeedContext:
    """
    Context manager for temporary seed scoping.
    Resets the seed to its previous value upon exit.
    """
    
    def __init__(self, seed: int):
        """
        Initialize the context manager.
        
        Args:
            seed: The seed to use within the context.
        """
        self.seed = seed
        self.previous_seed = SeedManager.get_seed()
    
    def __enter__(self) -> int:
        """Set the seed when entering the context."""
        SeedManager.set_seed(self.seed)
        return self.seed
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore the previous seed when exiting the context."""
        if self.previous_seed is not None:
            SeedManager.set_seed(self.previous_seed)
        else:
            SeedManager._current_seed = None


def get_random_state(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to get the current random state.
    
    Args:
        seed: Optional seed to set before getting state.
    
    Returns:
        A dictionary containing the random states of all supported libraries.
    """
    return SeedManager.get_random_state(seed)


def main() -> None:
    """
    Command-line interface for seed management operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed management utility")
    parser.add_argument(
        "--set", 
        type=int, 
        default=None, 
        help="Set a specific seed value"
    )
    parser.add_argument(
        "--generate", 
        action="store_true", 
        help="Generate a new random seed"
    )
    parser.add_argument(
        "--save", 
        action="store_true", 
        help="Save the current seed to config file"
    )
    parser.add_argument(
        "--load", 
        action="store_true", 
        help="Load seed from config file and set it"
    )
    parser.add_argument(
        "--show", 
        action="store_true", 
        help="Show the current seed"
    )
    
    args = parser.parse_args()
    
    if args.set is not None:
        set_seed(args.set, persist=args.save)
    elif args.generate:
        seed = generate_seed()
        print(f"Generated seed: {seed}")
        if args.save:
            save_seed_config(seed)
    elif args.load:
        seed = load_seed_config()
        if seed is not None:
            set_seed(seed)
        else:
            print("No seed config found. Use --set or --generate to create one.")
    elif args.show:
        seed = get_seed()
        if seed is not None:
            print(f"Current seed: {seed}")
        else:
            print("No seed currently set.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
