"""
Configuration management for the llmXive research pipeline.
Handles random seed pinning and environment configuration.
"""
import os
import random
import numpy as np
from typing import Optional

# Default random seed for reproducibility
DEFAULT_SEED = 42

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Pin the random seed for reproducibility across all relevant libraries.
    
    Args:
        seed: The random seed to use. If None, uses DEFAULT_SEED.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)

    # Note: If using torch or tensorflow, seeds would be set here too,
    # but they are not in requirements.txt for this CPU-only project.

def get_config_value(key: str, default: any = None) -> any:
    """
    Retrieve a configuration value from environment variables.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        
    Returns:
        The value from the environment or the default.
    """
    return os.getenv(key, default)

def is_debug_mode() -> bool:
    """Check if the pipeline is running in debug mode."""
    return get_config_value("DEBUG_MODE", "false").lower() == "true"

def main() -> None:
    """
    Entry point for testing configuration functions directly.
    Verifies that seed pinning and environment checks work as expected.
    """
    print("Testing config module...")
    
    # Test set_random_seed
    set_random_seed(123)
    val1 = random.random()
    val2 = np.random.random()
    
    # Reset and verify reproducibility
    set_random_seed(123)
    val3 = random.random()
    val4 = np.random.random()
    
    assert val1 == val3, "Random seed not pinned correctly for random module"
    assert val2 == val4, "Random seed not pinned correctly for numpy"
    print(f"Seed pinning verified: {val1} == {val3}")
    
    # Test is_debug_mode
    print(f"Debug mode status: {is_debug_mode()}")
    
    # Test get_config_value
    test_val = get_config_value("NON_EXISTENT_VAR", "default_val")
    assert test_val == "default_val", "Default value not returned correctly"
    print(f"Config value retrieval verified: {test_val}")
    
    print("All config tests passed.")

if __name__ == "__main__":
    main()