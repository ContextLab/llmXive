"""
Tests to verify the pytest configuration and fixtures.
"""

import os
import random
import numpy as np
import pytest
from pathlib import Path


def test_random_seed_fixture(random_seed: int):
    """Verify that the random_seed fixture returns an integer."""
    assert isinstance(random_seed, int)
    assert random_seed >= 0


def test_seed_reproducibility(random_seed: int):
    """Verify that seeding produces deterministic results."""
    random.seed(random_seed)
    val1 = random.random()
    np.random.seed(random_seed)
    val2 = np.random.random()

    # Reset and check
    random.seed(random_seed)
    val1_check = random.random()
    np.random.seed(random_seed)
    val2_check = np.random.random()

    assert val1 == val1_check
    assert val2 == val2_check


def test_temp_data_dir_structure(temp_data_dir: Path):
    """Verify that the temp_data_dir fixture creates the expected subdirectories."""
    assert temp_data_dir.exists()
    assert (temp_data_dir / "data" / "raw").exists()
    assert (temp_data_dir / "data" / "processed").exists()
    assert (temp_data_dir / "state").exists()


def test_temp_data_dir_isolation(temp_data_dir: Path, tmp_path: Path):
    """Verify that temp_data_dir is distinct from other tmp paths."""
    # They should be different paths
    assert temp_data_dir != tmp_path
    # But both should exist
    assert temp_data_dir.exists()
    assert tmp_path.exists()


def test_mock_trajectory_file_creation(mock_trajectory_file: Path):
    """Verify that the mock_trajectory_file fixture creates a valid file."""
    assert mock_trajectory_file.exists()
    assert mock_trajectory_file.suffix == ".csv"
    assert mock_trajectory_file.stat().st_size > 0