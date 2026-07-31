"""
Pytest configuration and shared fixtures for the project.

This file configures the test environment, sets up logging,
and provides reusable fixtures for data generation and model
testing across the test suite.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add the project root to the path for imports
# Assumes tests/ is at the root, code/ is sibling
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils import set_seed
from generate_data import generate_synthetic_data
from preprocess import load_raw_data, map_to_categorical, save_processed_data
from logger import setup_logger, get_logger

# Configure logger for tests (suppress file output to avoid clutter, keep console)
@pytest.fixture(scope="session", autouse=True)
def test_logger():
    """Initialize the logger for the test session."""
    logger = setup_logger(
        name="test_logger",
        log_file=None,  # No file output for tests
        level="INFO",
        json_format=False
    )
    return logger

@pytest.fixture(scope="session")
def raw_data_path(tmp_path_factory):
    """
    Generate a synthetic raw dataset and return its path.
    Uses a fixed seed for reproducibility.
    """
    set_seed(42)
    output_dir = tmp_path_factory.mktemp("data")
    output_file = output_dir / "raw_synthetic_data.csv"
    
    # Generate data using the project's generator
    df = generate_synthetic_data(
        n_participants=100,
        status_effect_size=0.5,
        behavior_effect_size=0.3,
        interaction_effect_size=0.2,
        random_seed=42
    )
    
    # Ensure the directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    return str(output_file)

@pytest.fixture(scope="session")
def processed_data_path(raw_data_path, tmp_path_factory):
    """
    Load raw data, preprocess it, and return the path to the processed CSV.
    """
    output_dir = tmp_path_factory.mktemp("processed")
    output_file = output_dir / "processed_data.csv"
    
    # Load and preprocess
    df_raw = load_raw_data(raw_data_path)
    df_mapped = map_to_categorical(df_raw)
    
    # Save processed data
    save_processed_data(df_mapped, str(output_file))
    
    return str(output_file)

@pytest.fixture
def sample_dataframe():
    """
    Provide a small, valid sample dataframe for unit tests that don't need
    the full generation pipeline.
    """
    set_seed(123)
    data = {
        "participant_id": [f"P{i}" for i in range(10)],
        "status_level": np.random.choice(["High", "Low"], 10),
        "observed_behavior": np.random.choice(["Risky", "Conservative"], 10),
        "risk_taking_score": np.random.normal(50, 10, 10)
    }
    return pd.DataFrame(data)
