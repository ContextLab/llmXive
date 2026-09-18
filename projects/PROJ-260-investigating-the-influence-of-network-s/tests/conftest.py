"""Pytest configuration and shared fixtures.

This file configures pytest behavior and provides shared fixtures
for the test suite. It is automatically discovered by pytest.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Add src directory to sys.path for imports during tests."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for tests."""
    dirs = [
        "raw",
        "derived/topology",
        "derived/vdos",
        "derived/reference",
        "derived/correlation",
        "metadata",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path

@pytest.fixture
def sample_simulation_box():
    """Create a minimal valid SimulationBox for testing."""
    import numpy as np
    from src.models.simulation_box import SimulationBox

    n_atoms = 10
    positions = np.random.rand(n_atoms, 3) * 10.0
    box_vectors = np.eye(3) * 10.0
    atom_ids = np.arange(n_atoms) + 1

    return SimulationBox(
        positions=positions,
        box_vectors=box_vectors,
        atom_ids=atom_ids,
        velocities=None,
        thermal_conductivity=None,
    )