import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from code.errors import DataLoadError
from code.scripts.generate_segregation_profiles import (
    load_equilibrium_compositions,
    load_dft_energies,
    compute_segregation_profile,
    main,
)

# Fixtures for test data
@pytest.fixture
def mock_equilibrium_csv(tmp_path):
    """Create a mock equilibrium_compositions.csv file."""
    csv_path = tmp_path / "equilibrium_compositions.csv"
    data = {
        "system": ["Fe-Cr-Mo", "Fe-Cr-V"],
        "temperature": [600, 700],
        "bulk_cr": [0.1, 0.2],
        "bulk_mo": [0.05, 0.0],
        "bulk_v": [0.0, 0.05],
        "bulk_w": [0.0, 0.0],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_surrogate_json(tmp_path):
    """Create a mock surrogate_energies.json file."""
    json_path = tmp_path / "surrogate_energies.json"
    data = {
        "source_id": "test_surrogate",
        "energies": {
            "Fe-Cr-Mo": -0.15,
            "Fe-Cr-V": -0.12,
        },
    }
    with open(json_path, "w") as f:
        json.dump(data, f)
    return json_path

@pytest.fixture
def mock_config_paths(tmp_path):
    """Mock the config paths to point to temporary directories."""
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", tmp_path):
        with patch("code.scripts.generate_segregation_profiles.DATA_RAW_PATH", tmp_path):
            yield tmp_path

def test_load_equilibrium_compositions_success(mock_equilibrium_csv, mock_config_paths):
    """Test successful loading of equilibrium compositions."""
    # Update the mock path to the fixture's temp directory
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", mock_equilibrium_csv.parent):
        df = load_equilibrium_compositions()
        assert len(df) == 2
        assert "system" in df.columns
        assert "temperature" in df.columns

def test_load_equilibrium_compositions_missing_file(mock_config_paths, tmp_path):
    """Test error when equilibrium file is missing."""
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", tmp_path):
        with pytest.raises(DataLoadError, match="Equilibrium compositions file not found"):
            load_equilibrium_compositions()

def test_load_dft_energies_success(mock_surrogate_json, mock_config_paths):
    """Test successful loading of surrogate DFT energies."""
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", mock_surrogate_json.parent):
        data = load_dft_energies()
        assert "energies" in data
        assert "Fe-Cr-Mo" in data["energies"]

def test_load_dft_energies_missing_file(mock_config_paths, tmp_path):
    """Test error when surrogate file is missing."""
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", tmp_path):
        with pytest.raises(DataLoadError, match="Surrogate energies file not found"):
            load_dft_energies()

def test_compute_segregation_profile(mock_equilibrium_csv, mock_surrogate_json, mock_config_paths):
    """Test computation of a single segregation profile."""
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", mock_equilibrium_csv.parent):
        eq_comps = load_equilibrium_compositions()
        dft_data = load_dft_energies()
        
        row = eq_comps.iloc[0]
        profile = compute_segregation_profile(row, dft_data)
        
        assert profile is not None
        assert profile["system"] == "Fe-Cr-Mo"
        assert "profiles" in profile
        assert "Cr" in profile["profiles"]
        assert "Mo" in profile["profiles"]

def test_main_integration(mock_equilibrium_csv, mock_surrogate_json, mock_config_paths, caplog):
    """Test the full main pipeline integration."""
    # Ensure the processed path is set correctly
    processed_dir = mock_equilibrium_csv.parent
    
    with patch("code.scripts.generate_segregation_profiles.PROCESSED_PATH", processed_dir):
        with patch("code.scripts.generate_segregation_profiles.DATA_RAW_PATH", processed_dir):
            result = main()
            
            # Check return code
            assert result == 0
            
            # Check output file exists
            output_path = processed_dir / "segregation_profiles.json"
            assert output_path.exists()
            
            # Validate output content
            with open(output_path) as f:
                output_data = json.load(f)
            
            assert "profiles" in output_data
            assert len(output_data["profiles"]) > 0