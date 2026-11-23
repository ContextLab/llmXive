"""
Seed management utility for reproducible experiments.

This module provides functions to pin all random states across
Python's random, numpy, and other libraries to ensure reproducibility.
"""

import os
import random
from typing import Optional, Dict, Any
import numpy as np

# Default seed value for reproducibility
DEFAULT_SEED = 42

# Global seed configuration
_seed_config: Dict[str, Any] = {
    'global_seed': DEFAULT_SEED,
    'python_random': DEFAULT_SEED,
    'numpy_random': DEFAULT_SEED,
    'torch_seed': DEFAULT_SEED,  # For PyTorch if used
}

def get_seed(component: Optional[str] = None) -> int:
    """
    Get the seed value for a specific component or the global seed.
    
    Args:
        component: The component name ('python_random', 'numpy_random', 
                 'torch_seed', or None for global)
    
    Returns:
        The seed value as an integer
    """
    if component is None:
        return _seed_config['global_seed']
    return _seed_config.get(component, _seed_config['global_seed'])

def set_seed(seed: int, component: Optional[str] = None) -> None:
    """
    Set the seed value for a specific component or globally.
    
    Args:
        seed: The seed value to set
        component: The component name. If None, sets global seed and
                 propagates to all components
    """
    if component is None:
        # Set global seed
        _seed_config['global_seed'] = seed
        _seed_config['python_random'] = seed
        _seed_config['numpy_random'] = seed
        _seed_config['torch_seed'] = seed
        
        # Apply to Python's random
        random.seed(seed)
        
        # Apply to NumPy
        np.random.seed(seed)
        
        # Apply to PyTorch if available
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass  # PyTorch not installed
    else:
        # Set seed for specific component
        _seed_config[component] = seed
        
        # Apply to the specific library
        if component == 'python_random':
            random.seed(seed)
        elif component == 'numpy_random':
            np.random.seed(seed)
        elif component == 'torch_seed':
            try:
                import torch
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
                    torch.cuda.manual_seed_all(seed)
            except ImportError:
                pass

def get_random_state(component: str = 'numpy_random') -> Any:
    """
    Get the current random state for a specific component.
    
    Args:
        component: The component name ('python_random' or 'numpy_random')
    
    Returns:
        The random state object for the specified component
    """
    if component == 'python_random':
        return random.getstate()
    elif component == 'numpy_random':
        return np.random.get_state()
    else:
        raise ValueError(f"Unknown component: {component}")

def set_random_state(state: Any, component: str = 'numpy_random') -> None:
    """
    Set the random state for a specific component.
    
    Args:
        state: The random state object to set
        component: The component name ('python_random' or 'numpy_random')
    """
    if component == 'python_random':
        random.setstate(state)
    elif component == 'numpy_random':
        np.random.set_state(state)
    else:
        raise ValueError(f"Unknown component: {component}")

def get_seed_config() -> Dict[str, Any]:
    """
    Get the current seed configuration for all components.
    
    Returns:
        Dictionary containing all seed values
    """
    return _seed_config.copy()

def init_seed(seed: Optional[int] = None) -> int:
    """
    Initialize all random seeds to a consistent value.
    
    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED
    
    Returns:
        The seed value that was set
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    # Set all seeds
    set_seed(seed)
    
    # Also check for environment variable override
    env_seed = os.getenv('PROJECT_SEED')
    if env_seed is not None:
        try:
            env_seed = int(env_seed)
            set_seed(env_seed)
            seed = env_seed
        except ValueError:
            pass  # Invalid environment variable, ignore
    
    return seed