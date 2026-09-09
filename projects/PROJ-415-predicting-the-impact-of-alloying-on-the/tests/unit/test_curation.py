import os
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.curation import (
    exclude_missing_concentration,
    validate_atomic_radii,
    log_exclusions,
    run_curation
)
from code.utils.constants import ElementData

@pytest.fixture
def mock_data_dir(tmp_path):
    """Setup temporary directories for data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "curated").mkdir()
    (data_dir / "logs").mkdir()
    return data_dir

@pytest.fixture
def sample_df():
    """Create a sample dataframe with mixed valid/invalid data."""
    data = {
        'host_id': ['Cu', 'Cu', 'Ni', 'Al', 'Cu'],
        'solute_id': ['Zn', 'Ni', 'Cu', 'Zn', 'Zn'],
        'concentration': [0.1, None, 0.2, 0.3, 0.1], # One missing
        'activation_energy': [1.2, 1.3, 1.4, 1.5, 1.6],
        'crystal_structure': ['FCC', 'FCC', 'FCC', 'FCC', 'FCC'],
        'diffusion_mode': ['self', 'self', 'self', 'self', 'self']
    }
    return pd.DataFrame(data)

def test_exclude_missing_concentration(sample_df):
    """Test that rows with missing concentration are excluded."""
    cleaned_df, exclusions = exclude_missing_concentration(sample_df)
    
    assert len(cleaned_df) == 4
    assert len(exclusions) == 1
    assert exclusions[0]['reason_code'] == 'MISSING_CONCENTRATION'
    assert 'concentration' not in cleaned_df.columns or not cleaned_df['concentration'].isna().any()

def test_validate_atomic_radii(sample_df):
    """Test validation of atomic radii against constants."""
    # All elements in sample_df are valid in constants.py
    cleaned_df, missing = validate_atomic_radii(sample_df)
    
    assert len(cleaned_df) == len(sample_df)
    assert len(missing) == 0

def test_validate_atomic_radii_missing():
    """Test handling of missing atomic radii."""
    data = {
        'host_id': ['Cu', 'FakeElement'],
        'solute_id': ['Zn', 'Zn'],
        'concentration': [0.1, 0.2],
        'activation_energy': [1.2, 1.3],
        'crystal_structure': ['FCC', 'FCC'],
        'diffusion_mode': ['self', 'self']
    }
    df = pd.DataFrame(data)
    
    cleaned_df, missing = validate_atomic_radii(df)
    
    assert len(cleaned_df) == 1
    assert len(missing) == 1
    assert missing[0]['solute_symbol'] == 'FakeElement'

def test_log_exclusions(tmp_path, sample_df):
    """Test that exclusion logs are written correctly."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    error_dir = tmp_path / "errors"
    error_dir.mkdir()

    # Mock paths
    with patch('code.data.curation.LOG_DIR', log_dir), \
         patch('code.data.curation.ERRORS_DIR', error_dir), \
         patch('code.data.curation.EXCLUSIONS_LOG_PATH', log_dir / "exclusions.log"), \
         patch('code.data.curation.MISSING_DATA_PATH', error_dir / "missing_atomic_data.csv"):
        
        conc_exclusions = [{'row_id': 1, 'reason_code': 'MISSING_CONCENTRATION', 'row_content': 'test'}]
        radius_missing = [{'row_id': 2, 'solute_symbol': 'X', 'missing_attribute': 'radius'}]
        
        count = log_exclusions(conc_exclusions, radius_missing)
        
        assert count == 2
        assert (log_dir / "exclusions.log").exists()
        assert (error_dir / "missing_atomic_data.csv").exists()

def test_run_curation_integration(mock_data_dir, sample_df):
    """Integration test for the full curation pipeline."""
    # Setup input file
    input_path = mock_data_dir / "curated" / "filtered.csv"
    sample_df.to_csv(input_path, index=False)
    
    # Setup source metadata
    metadata_path = mock_data_dir / "raw" / "source_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({'url': 'test_url', 'source_type': 'real'}, f)

    # Mock config paths
    with patch('code.data.curation.DATA_DIR', mock_data_dir), \
         patch('code.data.curation.LOG_DIR', mock_data_dir / "logs"), \
         patch('code.data.curation.ERRORS_DIR', mock_data_dir / "errors"):
        
        result_df = run_curation()
        
        # Check output file exists
        output_path = mock_data_dir / "curated" / "filtered.csv"
        assert output_path.exists()
        
        # Check counts (1 row excluded for missing concentration)
        assert len(result_df) == len(sample_df) - 1
        
        # Check provenance
        provenance_path = mock_data_dir / "curated" / "data_provenance.json"
        assert provenance_path.exists()
        with open(provenance_path) as f:
            prov = json.load(f)
            assert prov['rows_before_curation'] == len(sample_df)
            assert prov['rows_after_curation'] == len(sample_df) - 1