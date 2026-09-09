import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Mock the config to avoid dependency on actual project structure during unit test
# In a real integration, we would rely on the actual config module
import sys
from unittest.mock import patch, MagicMock

# We need to import the function we are testing
# Since it relies on config, we mock the config calls
from code.models.feature_shift_analyzer import identify_shifted_features, load_importance_data

@pytest.fixture
def mock_importance_data():
    """Creates a mock DataFrame representing model_run.json content."""
    data = {
        "low_potential": [
            "bond_length_C_O", "angle_O_C_O", "homo_energy", "lumo_energy", "dihedral_C_O_C"
        ],
        "high_potential": [
            "homo_energy", "band_gap", "bond_length_C_O", "charge_Li", "dipole_moment"
        ]
    }
    return pd.DataFrame([data])

@pytest.fixture
def temp_model_run_file(mock_importance_data, tmp_path):
    """Creates a temporary model_run.json file for testing load_importance_data."""
    model_run_path = tmp_path / "model_run.json"
    with open(model_run_path, "w") as f:
        json.dump(mock_importance_data.to_dict(orient='records')[0], f)
    return model_run_path

def test_identify_shifted_features_logic(mock_importance_data):
    """Tests the core logic of identifying features unique to high potential top 3."""
    result = identify_shifted_features(mock_importance_data, top_n=3)

    # Expected Top 3 Low: bond_length_C_O, angle_O_C_O, homo_energy
    # Expected Top 3 High: homo_energy, band_gap, bond_length_C_O

    # Unique to High (in High Top 3, not in Low Top 3): 'band_gap'
    # Unique to Low (in Low Top 3, not in High Top 3): 'angle_O_C_O'
    # Common: 'bond_length_C_O', 'homo_energy'

    assert "band_gap" in result["shifted_features"]["in_high_not_low"]
    assert "angle_O_C_O" in result["shifted_features"]["in_low_not_high"]
    assert "bond_length_C_O" in result["shifted_features"]["common"]
    assert "homo_energy" in result["shifted_features"]["common"]

    # Verify the deviation note exists
    assert "deviation_note" in result["analysis_metadata"]
    assert "3-5V" in result["analysis_metadata"]["deviation_note"]
    assert "4V" in result["analysis_metadata"]["deviation_note"]

def test_identify_shifted_features_no_shift(mock_importance_data):
    """Tests logic when top 3 are identical."""
    # Modify data so top 3 are identical
    data = {
        "low_potential": ["A", "B", "C", "D"],
        "high_potential": ["A", "B", "C", "E"]
    }
    df = pd.DataFrame([data])
    result = identify_shifted_features(df, top_n=3)

    assert len(result["shifted_features"]["in_high_not_low"]) == 0
    assert len(result["shifted_features"]["in_low_not_high"]) == 0
    assert len(result["shifted_features"]["common"]) == 3

def test_load_importance_data_missing_file(tmp_path):
    """Tests that load_importance_data raises FileNotFoundError for missing file."""
    # We need to patch the path resolution inside the function
    # Since the function uses get_project_root(), we mock that
    with patch("code.models.feature_shift_analyzer.get_project_root") as mock_root:
        mock_root.return_value = tmp_path
        with pytest.raises(FileNotFoundError):
            load_importance_data()

def test_load_importance_data_invalid_structure(tmp_path):
    """Tests that load_importance_data raises ValueError for missing keys."""
    invalid_data = {"wrong_key": []}
    model_run_path = tmp_path / "model_run.json"
    with open(model_run_path, "w") as f:
        json.dump(invalid_data, f)

    with patch("code.models.feature_shift_analyzer.get_project_root") as mock_root:
        mock_root.return_value = tmp_path
        with pytest.raises(ValueError):
            load_importance_data()
