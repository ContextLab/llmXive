"""
Unit tests for code/data/curation.py
"""

import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil
import os

# Mock the config and utils to avoid full project setup in tests
# We will use monkeypatch to set up the necessary directories and return values

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    data_dir = tmp_path / "data" / "curated"
    data_dir.mkdir(parents=True)
    log_dir = tmp_path / "data" / "logs"
    log_dir.mkdir(parents=True)
    errors_dir = tmp_path / "errors"
    errors_dir.mkdir(parents=True)
    
    return tmp_path

@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing curation logic."""
    data = {
        'host_element': ['Cu', 'Cu', 'Cu', 'Ag', 'Cu'],
        'solute_element': ['Ni', 'Zn', 'Au', 'Cu', 'Ni'],
        'concentration_at_percent': [10.0, None, 5.0, 0.0, 15.0],
        'diffusion_coefficient': [1e-10, 1e-11, 1e-12, 1e-13, 1e-14],
        'activation_energy': [1.5, 1.6, 1.7, 1.8, 1.9]
    }
    return pd.DataFrame(data)

def test_exclude_missing_concentration(sample_data):
    """Test that rows with missing concentration are excluded."""
    from code.data.curation import exclude_missing_concentration
    
    valid_df, invalid_df = exclude_missing_concentration(sample_data)
    
    # Row with index 1 has None concentration
    assert len(valid_df) == 4
    assert len(invalid_df) == 1
    assert invalid_df.iloc[0]['reason_code'] == 'MISSING_CONCENTRATION'
    assert invalid_df.iloc[0]['row_id'] == 1

def test_validate_atomic_radii(temp_project_root, sample_data, monkeypatch):
    """Test that rows with missing atomic radii are excluded."""
    # Mock get_metallic_radius to return None for a specific element
    from code.data import curation
    from code.utils import constants
    
    original_get_radius = constants.get_metallic_radius
    
    def mock_get_radius(element):
        if element == "Zn":
            return None
        return original_get_radius(element)
    
    monkeypatch.setattr(constants, "get_metallic_radius", mock_get_radius)
    monkeypatch.setattr(curation, "get_metallic_radius", mock_get_radius)
    
    # Also need to mock get_logger to avoid file writing issues in test
    import logging
    mock_logger = logging.getLogger("test_logger")
    monkeypatch.setattr(curation, "logger", mock_logger)
    
    valid_df, invalid_df = curation.validate_atomic_radii(sample_data)
    
    # Row with index 1 has Zn which we mocked as missing radius
    # But wait, row 1 was already excluded by concentration test? 
    # In this test, we use the original sample_data which has Zn at index 1.
    # Row 0: Cu, Ni -> Valid
    # Row 1: Cu, Zn -> Invalid (Zn missing radius)
    # Row 2: Cu, Au -> Valid
    # Row 3: Ag, Cu -> Valid
    # Row 4: Cu, Ni -> Valid
    
    assert len(valid_df) == 4
    assert len(invalid_df) == 1
    assert invalid_df.iloc[0]['reason_code'] == 'MISSING_SOLUTE_RADIUS'
    assert invalid_df.iloc[0]['row_id'] == 1

def test_log_exclusions(temp_project_root, sample_data, monkeypatch):
    """Test that exclusions are logged correctly."""
    from code.data import curation
    from code import config
    from code.utils import logging as utils_logging
    
    # Setup paths
    monkeypatch.setattr(config, "LOG_DIR", str(temp_project_root / "data" / "logs"))
    monkeypatch.setattr(config, "DATA_DIR", temp_project_root / "data")
    monkeypatch.setattr(curation, "LOG_DIR", temp_project_root / "data" / "logs")
    monkeypatch.setattr(curation, "DATA_DIR", temp_project_root / "data")
    monkeypatch.setattr(curation, "PROJECT_ROOT", temp_project_root)
    
    # Mock logger
    import logging
    mock_logger = logging.getLogger("test_logger")
    monkeypatch.setattr(curation, "logger", mock_logger)
    
    # Create dummy invalid dataframes
    conc_invalid = pd.DataFrame({'row_id': [1], 'reason_code': ['MISSING_CONCENTRATION']})
    radii_invalid = pd.DataFrame({'row_id': [2], 'reason_code': ['MISSING_SOLUTE_RADIUS']})
    
    curation.log_exclusions(2, conc_invalid, radii_invalid)
    
    # Check log file
    log_path = temp_project_root / "data" / "logs" / "exclusions.log"
    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    assert lines[0].strip() == "# EXCLUSION_COUNT: 2"
    # Check if both exclusions are present (order might vary)
    content = "".join(lines[1:])
    assert "MISSING_CONCENTRATION" in content
    assert "MISSING_SOLUTE_RADIUS" in content
    
    # Check atomic errors file
    errors_path = temp_project_root / "errors" / "missing_atomic_data.csv"
    assert errors_path.exists()
    
    error_df = pd.read_csv(errors_path)
    assert len(error_df) == 1
    assert error_df.iloc[0]['reason_code'] == 'MISSING_SOLUTE_RADIUS'

def test_run_curation_integration(temp_project_root, sample_data, monkeypatch):
    """Integration test for the full curation pipeline."""
    from code.data import curation
    from code import config
    from code.utils import constants
    
    # Setup paths
    monkeypatch.setattr(config, "LOG_DIR", str(temp_project_root / "data" / "logs"))
    monkeypatch.setattr(config, "DATA_DIR", temp_project_root / "data")
    monkeypatch.setattr(config, "PROJECT_ROOT", temp_project_root)
    monkeypatch.setattr(curation, "LOG_DIR", temp_project_root / "data" / "logs")
    monkeypatch.setattr(curation, "DATA_DIR", temp_project_root / "data")
    monkeypatch.setattr(curation, "PROJECT_ROOT", temp_project_root)
    
    # Mock logger
    import logging
    mock_logger = logging.getLogger("test_logger")
    monkeypatch.setattr(curation, "logger", mock_logger)
    
    # Mock get_metallic_radius to fail for Zn
    original_get_radius = constants.get_metallic_radius
    def mock_get_radius(element):
        if element == "Zn":
            return None
        return original_get_radius(element)
    monkeypatch.setattr(constants, "get_metallic_radius", mock_get_radius)
    monkeypatch.setattr(curation, "get_metallic_radius", mock_get_radius)
    
    # Write sample data to file
    input_path = temp_project_root / "data" / "curated" / "filtered.csv"
    sample_data.to_csv(input_path, index=False)
    
    # Run curation
    result_df = curation.run_curation()
    
    # Should exclude row 1 (missing concentration) and row 1 (missing radius Zn)
    # Note: In the sample data, row 1 has both missing concentration AND Zn (missing radius).
    # The pipeline first excludes missing concentration, so row 1 is gone before radius check.
    # So we expect row 1 excluded for concentration.
    # Row 2 is valid.
    # Row 3 is valid.
    # Row 4 is valid.
    # Row 0 is valid.
    # Wait, sample data:
    # 0: Cu, Ni, 10.0 -> Valid
    # 1: Cu, Zn, None -> Excluded (Concentration)
    # 2: Cu, Au, 5.0 -> Valid
    # 3: Ag, Cu, 0.0 -> Valid
    # 4: Cu, Ni, 15.0 -> Valid
    
    # So result should have 4 rows.
    assert len(result_df) == 4
    
    # Check that row 1 is not in result
    assert 1 not in result_df.index
    
    # Check log file
    log_path = temp_project_root / "data" / "logs" / "exclusions.log"
    assert log_path.exists()
    with open(log_path, 'r') as f:
        lines = f.readlines()
    assert lines[0].strip() == "# EXCLUSION_COUNT: 1"
    assert "MISSING_CONCENTRATION" in "".join(lines[1:])
    
    # Check atomic errors file (should be empty or have 0 rows if no radius errors after concentration filter)
    errors_path = temp_project_root / "errors" / "missing_atomic_data.csv"
    assert errors_path.exists()
    error_df = pd.read_csv(errors_path)
    assert len(error_df) == 0
