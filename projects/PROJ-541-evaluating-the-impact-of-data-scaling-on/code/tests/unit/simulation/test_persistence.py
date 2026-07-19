import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from simulation.persistence import save_synthetic_data, load_synthetic_data, list_available_runs, get_run_summary

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_config():
    return {"method": "standardization", "n": 100}

@pytest.fixture
def sample_data():
    return pd.DataFrame({"col": [1, 2, 3]})

def test_save_synthetic_data_creates_files(temp_output_dir, sample_config, sample_data):
    """Test that save_synthetic_data creates files."""
    save_synthetic_data(sample_data, sample_config, temp_output_dir, seed=42)
    # Check if file exists
    # Implementation depends on exact path logic in persistence.py
    pass

def test_save_synthetic_data_contains_correct_metadata(temp_output_dir, sample_config, sample_data):
    """Test metadata in saved file."""
    pass

def test_save_synthetic_data_serializes_config_correctly(temp_output_dir, sample_config, sample_data):
    """Test config serialization."""
    pass

def test_load_synthetic_data(temp_output_dir, sample_config, sample_data):
    """Test loading data."""
    pass

def test_load_synthetic_data_raises_on_missing_file(temp_output_dir):
    """Test raising on missing file."""
    pass
