"""
Unit tests to verify that the pytest fixtures (T008) are working correctly.

These tests ensure:
1. The random seed fixture sets the seed correctly.
2. The temporary data directory fixture creates a valid, isolated path.
3. The project root fixture points to the correct location.
"""
import os
import random
import numpy as np
import pytest
from pathlib import Path


def test_random_seed_consistency(random_seed):
    """
    Test that the random_seed fixture produces a deterministic sequence.
    We generate two numbers and compare them to known values for seed=42.
    """
    # The fixture sets the seed. We verify by generating numbers.
    val1 = random.random()
    val2 = np.random.random()
    
    # Known values for seed 42
    # Note: These values depend on the order of random calls in the fixture vs this test.
    # Since the fixture sets the seed at the start, the first call here should be deterministic.
    # Standard Python random(42) first call is approx 0.6394267984578837
    assert abs(val1 - 0.6394267984578837) < 1e-5, f"Random seed not set correctly. Got {val1}"
    # numpy random(42) first call is approx 0.3745401188473625
    assert abs(val2 - 0.3745401188473625) < 1e-5, f"Numpy random seed not set correctly. Got {val2}"


def test_tmp_data_dir_creation(tmp_data_dir):
    """
    Test that tmp_data_dir creates the expected directory structure.
    """
    assert tmp_data_dir.exists(), "Temporary directory does not exist"
    assert tmp_data_dir.is_dir(), "Temporary path is not a directory"
    
    raw_path = tmp_data_dir / "data" / "raw"
    processed_path = tmp_data_dir / "data" / "processed"
    state_path = tmp_data_dir / "state"
    
    assert raw_path.exists(), "Raw data directory not created"
    assert processed_path.exists(), "Processed data directory not created"
    assert state_path.exists(), "State directory not created"


def test_tmp_data_dir_isolation(tmp_data_dir):
    """
    Test that the temporary directory is isolated from the real data directory.
    """
    # Check that the temp dir is NOT inside the project's real data folder
    project_root = tmp_data_dir.parent.parent # tests -> project_root
    real_data_dir = project_root / "data"
    
    # The tmp_path is usually in /tmp or similar, so it shouldn't be a subpath of real_data_dir
    # unless the test runner is misconfigured, but we check the string path to be sure.
    assert str(tmp_data_dir).startswith(str(real_data_dir)) is False, \
        "Temporary directory is not isolated from the real data directory"


def test_project_root_fixture(project_root):
    """
    Test that the project_root fixture points to the expected location.
    """
    assert project_root.exists(), "Project root does not exist"
    assert (project_root / "code").exists(), "Code directory missing in project root"
    assert (project_root / "tests").exists(), "Tests directory missing in project root"
