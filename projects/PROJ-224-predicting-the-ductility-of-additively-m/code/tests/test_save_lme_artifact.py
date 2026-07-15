"""
Tests for save_lme_artifact.py
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from models.save_lme_artifact import save_lme_artifact

@pytest.fixture
def sample_results():
    """Generate a sample results dictionary mimicking extract_results output."""
    return {
        "metrics": {
            "r_squared": 0.65,
            "aic": 123.45,
            "bic": 130.10,
            "convergence": True,
            "p_values": {"laser_power": 0.01, "scan_speed": 0.05},
            "confidence_intervals": {
                "laser_power": [0.1, 0.5],
                "scan_speed": [-0.1, 0.2]
            }
        },
        "random_effects": {
            "Inconel 718": 0.5,
            "Hastelloy X": -0.2
        },
        "model_spec": {
            "formula": "ductility ~ laser_power + scan_speed + (1 | alloy_family)",
            "predictors": ["laser_power", "scan_speed"]
        },
        "convergence_status": "converged",
        "artifact_version": "1.0.0"
    }

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output."""
    return tmp_path

def test_save_lme_artifact_creates_file(sample_results, temp_output_dir):
    """Test that save_lme_artifact creates a valid JSON file."""
    output_path = temp_output_dir / "test_result.json"
    result_path = save_lme_artifact(sample_results, str(output_path))

    assert Path(result_path).exists()
    assert Path(result_path).suffix == ".json"

    with open(result_path, 'r') as f:
        loaded = json.load(f)

    assert loaded["metrics"]["r_squared"] == 0.65
    assert loaded["convergence_status"] == "converged"
    assert "Inconel 718" in loaded["random_effects"]

def test_save_lme_artifact_handles_numpy_types(sample_results, temp_output_dir):
    """Test that numpy types are converted to native Python types."""
    # Modify sample to include numpy types
    sample_results["metrics"]["r_squared"] = np.float64(0.88)
    sample_results["random_effects"]["TestAlloy"] = np.int32(1)
    
    output_path = temp_output_dir / "numpy_test.json"
    result_path = save_lme_artifact(sample_results, str(output_path))

    with open(result_path, 'r') as f:
        loaded = json.load(f)

    # Verify types are native Python
    assert isinstance(loaded["metrics"]["r_squared"], float)
    assert isinstance(loaded["random_effects"]["TestAlloy"], int)

def test_save_lme_artifact_creates_directories(sample_results, temp_output_dir):
    """Test that save_lme_artifact creates parent directories if they don't exist."""
    nested_path = temp_output_dir / "subdir" / "nested" / "result.json"
    result_path = save_lme_artifact(sample_results, str(nested_path))

    assert Path(result_path).exists()

def test_save_lme_artifact_overwrites_existing(sample_results, temp_output_dir):
    """Test that save_lme_artifact overwrites an existing file."""
    output_path = temp_output_dir / "overwrite.json"
    
    # Create initial file
    with open(output_path, 'w') as f:
        json.dump({"old": "data"}, f)

    # Save new data
    save_lme_artifact(sample_results, str(output_path))

    with open(output_path, 'r') as f:
        loaded = json.load(f)

    assert "metrics" in loaded
    assert loaded["metrics"]["r_squared"] == 0.65