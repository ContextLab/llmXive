"""
Seed management utility for reproducibility across statistical runs.

This module provides a centralized way to set, retrieve, and propagate
random seeds for numpy, random, and other libraries used in the pipeline.
"""
import os
import random
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager

import numpy as np
from config import get_project_root

logger = logging.getLogger(__name__)

# Default seed file path
DEFAULT_SEED_FILE = "artifacts/seed_config.json"

class SeedManager:
    """
    Centralized manager for random seeds across the project.
    
    Ensures reproducibility by setting seeds for numpy, random, and
    any other relevant libraries.
    """
    
    _instance = None
    _seed = None
    _seed_file = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._seed = None
        self._seed_file = None
        logger.debug("SeedManager initialized")
    
    def initialize(self, seed: Optional[int] = None, seed_file: Optional[Union[str, Path]] = None):
        """
        Initialize the seed manager with a specific seed or generate one.
        
        Args:
            seed: Optional integer seed. If None, a random seed is generated.
            seed_file: Optional path to save/load seed configuration.
        """
        if seed_file is None:
            project_root = get_project_root()
            self._seed_file = project_root / DEFAULT_SEED_FILE
        else:
            self._seed_file = Path(seed_file)
        
        # Ensure artifacts directory exists
        self._seed_file.parent.mkdir(parents=True, exist_ok=True)
        
        if seed is not None:
            self._seed = seed
            logger.info(f"SeedManager initialized with provided seed: {seed}")
        else:
            # Check if seed file exists
            if self._seed_file.exists():
                self._seed = load_seed_config(self._seed_file)
                logger.info(f"SeedManager loaded seed from file: {self._seed}")
            else:
                self._seed = generate_seed()
                logger.info(f"SeedManager generated new seed: {self._seed}")
                save_seed_config(self._seed, self._seed_file)
        
        # Set the seed immediately
        set_seed(self._seed)
    
    def get_seed(self) -> int:
        """Get the current seed value."""
        if self._seed is None:
            raise RuntimeError("SeedManager not initialized. Call initialize() first.")
        return self._seed
    
    def set_seed(self, seed: int):
        """
        Set a new seed and update all relevant libraries.
        
        Args:
            seed: Integer seed value.
        """
        self._seed = seed
        set_seed(seed)
        logger.debug(f"Seed updated to: {seed}")
    
    def get_seed_file(self) -> Path:
        """Get the path to the seed configuration file."""
        if self._seed_file is None:
            raise RuntimeError("SeedManager not initialized. Call initialize() first.")
        return self._seed_file
    
    def save_seed_config(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Save the current seed and optional metadata to the configuration file.
        
        Args:
            metadata: Optional dictionary of additional metadata to save.
        """
        if self._seed is None:
            raise RuntimeError("SeedManager not initialized. Call initialize() first.")
        
        save_seed_config(self._seed, self._seed_file, metadata)
    
    @classmethod
    def get_instance(cls) -> 'SeedManager':
        """Get the singleton instance of SeedManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

def set_seed(seed: int):
    """
    Set random seeds for numpy, random, and other libraries.
    
    Args:
        seed: Integer seed value.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)}")
    
    np.random.seed(seed)
    random.seed(seed)
    
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    # If tensorflow is available, set its seed
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass
    
    logger.debug(f"Seeds set for all libraries: {seed}")

def get_seed() -> int:
    """
    Get the current seed from the SeedManager singleton.
    
    Returns:
        Current seed value.
        
    Raises:
        RuntimeError: If SeedManager is not initialized.
    """
    manager = SeedManager.get_instance()
    return manager.get_seed()

def generate_seed() -> int:
    """
    Generate a random seed using os.urandom.
    
    Returns:
        Random integer seed.
    """
    # Use os.urandom to generate a random seed
    random_bytes = os.urandom(4)
    seed = int.from_bytes(random_bytes, byteorder='big')
    return seed

def save_seed_config(seed: int, seed_file: Union[str, Path], metadata: Optional[Dict[str, Any]] = None):
    """
    Save seed configuration to a JSON file.
    
    Args:
        seed: Seed value to save.
        seed_file: Path to the seed configuration file.
        metadata: Optional metadata dictionary.
    """
    seed_file = Path(seed_file)
    
    config = {
        "seed": seed,
        "timestamp": str(Path(seed_file).parent.parent / "artifacts" / "logs" / "seed_manager.log"),  # Placeholder for actual timestamp
    }
    
    if metadata:
        config.update(metadata)
    
    # Add timestamp
    from datetime import datetime
    config["generated_at"] = datetime.now().isoformat()
    
    with open(seed_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Seed configuration saved to {seed_file}")

def load_seed_config(seed_file: Union[str, Path]) -> int:
    """
    Load seed configuration from a JSON file.
    
    Args:
        seed_file: Path to the seed configuration file.
        
    Returns:
        Seed value from the file.
        
    Raises:
        FileNotFoundError: If the seed file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    seed_file = Path(seed_file)
    
    if not seed_file.exists():
        raise FileNotFoundError(f"Seed configuration file not found: {seed_file}")
    
    with open(seed_file, 'r') as f:
        config = json.load(f)
    
    seed = config.get("seed")
    if seed is None:
        raise ValueError(f"Invalid seed configuration in {seed_file}: 'seed' key missing")
    
    logger.info(f"Seed configuration loaded from {seed_file}: {seed}")
    return seed

class SeedContext:
    """
    Context manager for temporarily setting a seed.
    
    Usage:
        with SeedContext(12345):
            # Code that needs reproducibility
            pass
        # Seed is restored to previous value after context
    """
    
    def __init__(self, seed: int):
        self.seed = seed
        self.previous_seed = None
    
    def __enter__(self):
        # Store current seed
        try:
            self.previous_seed = get_seed()
        except RuntimeError:
            self.previous_seed = None
        
        # Set new seed
        set_seed(self.seed)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous seed if it existed
        if self.previous_seed is not None:
            set_seed(self.previous_seed)

def get_random_state(seed: Optional[int] = None):
    """
    Get a numpy RandomState object for reproducible random operations.
    
    Args:
        seed: Optional seed. If None, uses the global seed.
        
    Returns:
        numpy RandomState object.
    """
    if seed is None:
        try:
            seed = get_seed()
        except RuntimeError:
            # If no global seed is set, use a random one
            seed = generate_seed()
    
    return np.random.RandomState(seed)

def main():
    """
    Command-line interface for seed management.
    
    Usage:
        python seed_manager.py --init [--seed SEED] [--output OUTPUT_PATH]
        python seed_manager.py --get
        python seed_manager.py --set SEED
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed management utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize seed manager")
    init_parser.add_argument("--seed", type=int, help="Seed value (optional)")
    init_parser.add_argument("--output", type=str, help="Output file path (optional)")
    
    # Get command
    subparsers.add_parser("get", help="Get current seed")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set a new seed")
    set_parser.add_argument("seed", type=int, help="New seed value")
    
    args = parser.parse_args()
    
    manager = SeedManager.get_instance()
    
    if args.command == "init":
        manager.initialize(seed=args.seed, seed_file=args.output)
        print(f"Seed initialized: {manager.get_seed()}")
        print(f"Seed file: {manager.get_seed_file()}")
    elif args.command == "get":
        try:
            seed = manager.get_seed()
            print(f"Current seed: {seed}")
        except RuntimeError as e:
            print(f"Error: {e}")
            print("Run 'init' first to initialize the seed manager.")
    elif args.command == "set":
        manager.set_seed(args.seed)
        manager.save_seed_config()
        print(f"Seed set to: {args.seed}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
