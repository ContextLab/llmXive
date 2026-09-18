"""
Seed Manager: Centralized random seed management for reproducibility.

Implements Principle I: Reproducibility.
Provides deterministic seeding for numpy, random, torch, and optional CUDA backends.
"""
import os
import random
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import torch for reproducibility settings
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def set_seed(seed: int) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.
    
    Args:
        seed (int): The integer seed to use.
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed)}")

    # Python's built-in random module
    random.seed(seed)

    # NumPy
    import numpy as np
    np.random.seed(seed)

    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['PYTHONHASHSEED'] = str(seed)


def load_seed_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load seed configuration from a JSON file.
    
    Args:
        config_path (str, optional): Path to the config file. 
                                     Defaults to 'config/seed_config.json'.
    
    Returns:
        Dict[str, Any]: Configuration dictionary containing 'seed' and metadata.
    """
    if config_path is None:
        # Resolve relative to project root logic handled by caller or default
        config_path = "config/seed_config.json"
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed configuration file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_seed_config(seed: int, config_path: Optional[str] = None) -> str:
    """
    Save the current seed configuration to a JSON file.
    
    Args:
        seed (int): The seed value to save.
        config_path (str, optional): Path to save the config file.
                                     Defaults to 'config/seed_config.json'.
    
    Returns:
        str: The path where the config was saved.
    """
    if config_path is None:
        config_path = "config/seed_config.json"
    
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": "Base configuration for random seed management to ensure reproducibility per Principle I"
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    return str(path)


def main() -> None:
    """
    CLI entry point to initialize seed configuration.
    Usage: python -m code.utils.seed_manager --seed 42
    """
    import argparse

    parser = argparse.ArgumentParser(description="Initialize random seed configuration.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed value (default: 42)")
    parser.add_argument("--output", type=str, default=None, help="Output path for config file")
    
    args = parser.parse_args()
    
    try:
        # Set the seed immediately for any subsequent operations in this script
        set_seed(args.seed)
        
        # Save the configuration
        saved_path = save_seed_config(args.seed, args.output)
        print(f"Seed configuration saved to: {saved_path}")
        print(f"Seed value set to: {args.seed}")
        print("Reproducibility Principle I enforced.")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
