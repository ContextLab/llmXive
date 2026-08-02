"""
Pytest configuration and shared fixtures for the llmXive project.
Ensures consistent test environment setup and provides reusable data fixtures.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Add project root to path to allow imports from code/
# Assuming tests/ is at repository root level
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import load_simulation_params, get_random_seed
from code.utils import set_seed
from code.models import StatusLevel, ObservedBehavior


@pytest.fixture(scope="session")
def project_root_path():
    """Return the path to the project root directory."""
    return project_root


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test outputs. Cleans up after the test."""
    tmp_path = tempfile.mkdtemp()
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_config_params():
    """
    Provide a dictionary of simulation parameters mimicking the real config.
    Used for tests that need to mock simulation inputs without hitting disk.
    """
    return {
        "effect_size_high_low": 0.5,
        "effect_size_interaction": 0.3,
        "sample_size": 100,
        "random_seed": 42,
        "design_type": "between-subjects"
    }


@pytest.fixture(scope="function")
def mock_data_between_subjects(sample_config_params):
    """
    Generate a mock DataFrame for between-subjects design.
    Each participant_id appears exactly once.
    """
    set_seed(sample_config_params["random_seed"])
    n = sample_config_params["sample_size"]
    
    data = {
        "participant_id": [f"P{i}" for i in range(n)],
        "status_level": np.random.choice(["High", "Low"], n),
        "observed_behavior": np.random.choice(["Risky", "Conservative"], n),
        "risk_taking_score": np.random.normal(loc=50, scale=10, size=n)
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def mock_data_within_subjects(sample_config_params):
    """
    Generate a mock DataFrame for within-subjects design.
    Each participant_id appears 4 times (2 status levels x 2 behaviors).
    """
    set_seed(sample_config_params["random_seed"])
    n_subjects = sample_config_params["sample_size"] // 4  # Approximate
    
    participant_ids = []
    status_levels = []
    observed_behaviors = []
    risk_scores = []
    
    statuses = ["High", "Low"]
    behaviors = ["Risky", "Conservative"]
    
    for i in range(n_subjects):
        for s in statuses:
            for b in behaviors:
                participant_ids.append(f"P{i}")
                status_levels.append(s)
                observed_behaviors.append(b)
                risk_scores.append(np.random.normal(loc=50, scale=10))
    
    data = {
        "participant_id": participant_ids,
        "status_level": status_levels,
        "observed_behavior": observed_behaviors,
        "risk_taking_score": risk_scores
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def valid_structure_config(tmp_dir):
    """
    Create a valid structure_config.json file in the temp directory.
    Returns the path to the file.
    """
    config_path = os.path.join(tmp_dir, "structure_config.json")
    config_data = {
        "type": "between-subjects",
        "n_subjects": 100,
        "model_type": "fixed-effects"
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_dir):
    """
    Automatically set environment variables and paths for tests.
    Ensures code modules look for data in the temp directory if needed.
    """
    monkeypatch.setenv("DATA_DIR", tmp_dir)
    monkeypatch.setenv("OUTPUT_DIR", tmp_dir)
    yield
