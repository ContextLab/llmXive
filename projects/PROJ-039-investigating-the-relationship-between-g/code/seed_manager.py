"""
Random seed management utility for llmXive project.

Provides a centralized, reproducible random seed management system.
All analysis scripts must import and use this module to ensure
reproducibility across statistical runs.
"""
import os
import random
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union
import json

# Try to import numpy if available (common dependency)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try to import torch if available
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Try to import tensorflow if available
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

# Try to import scikit-learn
try:
    import sklearn
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class SeedManager:
    """
    Centralized random seed manager for reproducible experiments.
    
    This class provides:
    - Global seed setting across all major libraries (numpy, random, torch, tf, sklearn)
    - Seed generation from project root hash for reproducibility
    - Context manager support for temporary seed changes
    - Seed logging and tracking
    """

    _instance = None
    _current_seed: Optional[int] = None
    _seed_history: list = []
    _config_path: Optional[Path] = None

    def __new__(cls):
        """Singleton pattern to ensure consistent seed management."""
        if cls._instance is None:
            cls._instance = super(SeedManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the seed manager if not already initialized."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._config_path = None
        self._seed_history = []
        self._current_seed = None

    @classmethod
    def get_project_root(cls) -> Path:
        """Get the project root directory."""
        # Look for .git directory or assume current working directory
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return Path.cwd()

    @classmethod
    def generate_seed_from_project(cls, salt: str = "") -> int:
        """
        Generate a deterministic seed based on the project structure.
        
        This ensures that the same project always uses the same base seed,
        unless the project structure changes.
        
        Args:
            salt: Optional string to add variation to the seed
            
        Returns:
            A deterministic integer seed
        """
        project_root = cls.get_project_root()
        
        # Hash the project root path and any salt
        seed_string = f"{project_root}:{salt}"
        hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
        
        # Convert first 8 hex chars to integer
        seed_value = int(hash_obj.hexdigest()[:8], 16)
        
        return seed_value

    def set_seed(self, seed: Union[int, str, None] = None, 
                apply_to_all: bool = True) -> int:
        """
        Set the random seed for all supported libraries.
        
        Args:
            seed: Integer seed, string (will be hashed), or None (auto-generate)
            apply_to_all: If True, apply to numpy, torch, tensorflow, etc.
            
        Returns:
            The seed value that was set
        """
        # Determine the seed value
        if seed is None:
            seed = self.generate_seed_from_project()
        elif isinstance(seed, str):
            # Hash the string to get an integer seed
            hash_obj = hashlib.sha256(seed.encode('utf-8'))
            seed = int(hash_obj.hexdigest()[:8], 16)
        else:
            seed = int(seed)

        self._current_seed = seed
        self._seed_history.append({
            'seed': seed,
            'timestamp': str(self._get_timestamp()),
            'apply_to_all': apply_to_all
        })

        # Set seed for Python's random module
        random.seed(seed)

        # Set seed for numpy
        if apply_to_all and HAS_NUMPY:
            np.random.seed(seed)

        # Set seed for PyTorch
        if apply_to_all and HAS_TORCH:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        # Set seed for TensorFlow
        if apply_to_all and HAS_TENSORFLOW:
            tf.random.set_seed(seed)

        # Set seed for scikit-learn (affects random_state in estimators)
        # Note: sklearn doesn't have a global seed, but we set it for any
        # estimators that accept random_state
        if apply_to_all and HAS_SKLEARN:
            # sklearn uses numpy's random state, which we already set
            pass

        return seed

    def get_seed(self) -> Optional[int]:
        """Get the current seed value."""
        return self._current_seed

    def get_seed_history(self) -> list:
        """Get the history of all seeds set."""
        return self._seed_history.copy()

    def save_seed_config(self, path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save the current seed configuration to a file.
        
        Args:
            path: Optional path to save to. If None, saves to artifacts/seed_config.json
                
        Returns:
            Path to the saved configuration file
        """
        if path is None:
            artifacts_dir = self.get_project_root() / 'artifacts'
            artifacts_dir.mkdir(exist_ok=True)
            path = artifacts_dir / 'seed_config.json'
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            'current_seed': self._current_seed,
            'seed_history': self._seed_history,
            'libraries_available': {
                'numpy': HAS_NUMPY,
                'torch': HAS_TORCH,
                'tensorflow': HAS_TENSORFLOW,
                'sklearn': HAS_SKLEARN
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)

        return path

    @classmethod
    def load_seed_config(cls, path: Union[str, Path]) -> int:
        """
        Load a seed configuration from a file and set it.
        
        Args:
            path: Path to the seed configuration file
                
        Returns:
            The loaded seed value
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Seed config file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        seed = config_data.get('current_seed')
        if seed is not None:
            instance = cls()
            instance.set_seed(seed)
            return seed

        raise ValueError("No valid seed found in configuration file")

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global seed manager instance
_seed_manager = SeedManager()


def set_seed(seed: Union[int, str, None] = None, 
            apply_to_all: bool = True) -> int:
    """
    Convenience function to set the random seed globally.
    
    Args:
        seed: Integer seed, string (will be hashed), or None (auto-generate)
        apply_to_all: If True, apply to numpy, torch, tensorflow, etc.
        
    Returns:
        The seed value that was set
    """
    return _seed_manager.set_seed(seed, apply_to_all)


def get_seed() -> Optional[int]:
    """
    Get the current global seed value.
    
    Returns:
        The current seed value or None if not set
    """
    return _seed_manager.get_seed()


def generate_seed(salt: str = "") -> int:
    """
    Generate a deterministic seed based on the project structure.
    
    Args:
        salt: Optional string to add variation to the seed
            
    Returns:
        A deterministic integer seed
    """
    return _seed_manager.generate_seed_from_project(salt)


def save_seed_config(path: Optional[Union[str, Path]] = None) -> Path:
    """
    Save the current seed configuration to a file.
    
    Args:
        path: Optional path to save to. If None, saves to artifacts/seed_config.json
            
    Returns:
        Path to the saved configuration file
    """
    return _seed_manager.save_seed_config(path)


def load_seed_config(path: Union[str, Path]) -> int:
    """
    Load a seed configuration from a file and set it.
    
    Args:
        path: Path to the seed configuration file
            
    Returns:
        The loaded seed value
    """
    return _seed_manager.load_seed_config(path)


class SeedContext:
    """
    Context manager for temporary seed changes.
    
    Usage:
        with SeedContext(42):
            # code that needs specific seed
            pass
        # seed is restored to previous value
    """

    def __init__(self, seed: Union[int, str, None]):
        """
        Initialize the context manager.
        
        Args:
            seed: The seed to use within the context
        """
        self.seed = seed
        self.previous_seed = _seed_manager.get_seed()

    def __enter__(self):
        """Set the seed when entering the context."""
        _seed_manager.set_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore the previous seed when exiting the context."""
        if self.previous_seed is not None:
            _seed_manager.set_seed(self.previous_seed)
        return False


def get_random_state(seed: Optional[int] = None):
    """
    Get a random state object for libraries that support it.
    
    Args:
        seed: Optional seed to initialize the state. If None, uses current global seed.
        
    Returns:
        A random state object compatible with numpy/scikit-learn
    """
    if seed is None:
        seed = get_seed()
    
    if seed is None:
        seed = generate_seed()
    
    if HAS_NUMPY:
        return np.random.RandomState(seed)
    else:
        # Fallback to Python's random if numpy not available
        random.seed(seed)
        return random


# Initialize with a default seed from project structure
# This ensures reproducibility even if no explicit seed is set
try:
    _default_seed = generate_seed()
    set_seed(_default_seed, apply_to_all=True)
except Exception:
    # If initialization fails, set a default seed
    set_seed(42, apply_to_all=True)
