"""
Unit tests for code/config.py to verify initialization, paths, and constraints.
"""
import os
import sys
import torch
import numpy as np
import random
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import config

def test_seed_consistency():
    """Verify that setting seeds produces deterministic results."""
    config.set_all_seeds(12345)
    
    # Test random
    r1 = random.random()
    config.set_all_seeds(12345)
    r2 = random.random()
    assert r1 == r2, "Random seed not consistent"

    # Test numpy
    config.set_all_seeds(12345)
    n1 = np.random.rand(5)
    config.set_all_seeds(12345)
    n2 = np.random.rand(5)
    np.testing.assert_array_equal(n1, n2, err_msg="Numpy seed not consistent")

    # Test torch
    config.set_all_seeds(12345)
    t1 = torch.rand(5)
    config.set_all_seeds(12345)
    t2 = torch.rand(5)
    torch.testing.assert_close(t1, t2, err_msg="Torch seed not consistent")

def test_cpu_constraint():
    """Verify that CPU-only constraints are enforced."""
    # Check environment variables
    assert os.environ.get("OPENBLAS_NUM_THREADS") == "1", "OpenBLAS threads not constrained"
    assert os.environ.get("MKL_NUM_THREADS") == "1", "MKL threads not constrained"
    assert os.environ.get("OMP_NUM_THREADS") == "1", "OMP threads not constrained"
    
    # Check CUDA visibility if available (should be empty string)
    if torch.cuda.is_available():
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CUDA should be disabled"

def test_directory_structure():
    """Verify that required directories exist."""
    assert config.DATA_DIR.exists(), "Data directory missing"
    assert config.FIGURES_DIR.exists(), "Figures directory missing"
    assert config.LOGS_DIR.exists(), "Logs directory missing"
    assert config.PREPROCESSED_DIR.exists(), "Processed directory missing"
    assert config.RESULTS_DIR.exists(), "Results directory missing"

def test_openneuro_config():
    """Verify OpenNeuro configuration defaults."""
    assert config.OPENNEURO_DATASET_ID == "ds000234", "Default dataset ID incorrect"
    assert config.OPENNEURO_VERSION == "1.1.0", "Default version incorrect"
    assert config.FMRIPREP_OMP_NUM_THREADS == 2, "Default OMP threads incorrect"
    assert config.MOTION_THRESHOLD_MM == 3.0, "Motion threshold incorrect"

def test_project_root():
    """Verify project root is correctly identified."""
    assert config.PROJECT_ROOT.exists(), "Project root path invalid"
    assert (config.PROJECT_ROOT / "code").exists(), "Code directory missing from root"
    assert (config.PROJECT_ROOT / "data").exists(), "Data directory missing from root"
