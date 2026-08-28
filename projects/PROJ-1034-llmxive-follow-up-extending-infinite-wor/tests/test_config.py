"""
Unit tests for project configuration and seed initialization.
"""
import random
import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import set_deterministic_seeds, PROJECT_ROOT, DATA_DIR, SEED

def test_seed_initialization():
    """Verify that setting the seed produces deterministic results."""
    # Set seed
    set_deterministic_seeds(SEED)
    
    # Generate values
    val1_random = random.random()
    val1_numpy = np.random.random()
    
    # Reset seed
    set_deterministic_seeds(SEED)
    
    # Generate values again
    val2_random = random.random()
    val2_numpy = np.random.random()
    
    # Assert equality
    assert val1_random == val2_random, "Random seed not deterministic"
    assert val1_numpy == val2_numpy, "Numpy seed not deterministic"

def test_directories_exist():
    """Verify that project directories are created on import."""
    assert PROJECT_ROOT.exists(), "Project root does not exist"
    assert DATA_DIR.exists(), "Data directory does not exist"
    
    # Check subdirectories
    assert (DATA_DIR / "raw").exists(), "Raw data directory missing"
    assert (DATA_DIR / "processed").exists(), "Processed data directory missing"

def test_seed_constant():
    """Verify the default seed is an integer."""
    assert isinstance(SEED, int), "SEED must be an integer"
    assert SEED >= 0, "SEED must be non-negative"
