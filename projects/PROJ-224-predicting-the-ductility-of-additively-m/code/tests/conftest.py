"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import logging
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def sample_curated_data():
    """
    Create a minimal valid dataset matching the schema of data/curated_builds.csv.
    Used for testing acquisition, cleaning, and modeling logic without external dependencies.
    """
    data = {
        "laser_power": [200.0, 250.0, 300.0, 220.0],
        "scan_speed": [800.0, 1000.0, 600.0, 900.0],
        "hatch_spacing": [100.0, 120.0, 100.0, 110.0],
        "layer_thickness": [30.0, 40.0, 30.0, 35.0],
        "ductility": [12.5, 10.2, 8.5, 11.0],
        "alloy_family": ["Inconel 718", "Inconel 718", "CMSX-4", "Inconel 625"],
        "energy_density": [83.33, 52.08, 166.67, 56.41],
        "Cr": [0, 1, 0, 1],
        "Al": [1, 1, 1, 0],
        "Ti": [1, 1, 1, 0],
        "Co": [0, 0, 1, 0],
        "Mo": [1, 1, 1, 1],
        "W": [0, 0, 1, 0],
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def logging_config():
    """Configure logging for tests to avoid clutter but allow capture."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    yield
    # Reset logging if necessary
    logging.shutdown()
