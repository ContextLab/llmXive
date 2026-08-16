import pytest
import os
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

# Import the function to test
from retrieval_output import process_retrieval_results
from retrieval import run_single_spectrum_retrieval, calculate_mdc, detect_low_snr_spectrum
from data_models import RetrievalResult, CensorshipStatus

@pytest.fixture
def temp_dirs():
    """Create temporary directories for raw and processed data."""
    temp_root = tempfile.mkdtemp()
    raw_dir = Path(temp_root) / 'raw'
    processed_dir = Path(temp_root) / 'processed'
    raw_dir.mkdir()
    processed_dir.mkdir()
    
    # Create a mock metadata file
    metadata_df = pd.DataFrame({
        'planet_name': ['HD_209458_b', 'WASP_121_b', 'K2_18_b'],
        'temperature': [1300, 2500, 300],
        'metallicity': [0.0, 0.5, -0.2],
        'snr': [50.0, 10.0, 2.0],  # 10 and 2 are low SNR
        'resolution': [1000, 100, 50],
        'planet_category': ['Hot Jupiter', 'Hot Jupiter', 'Super-Earth'],
        'instrument': ['HST', 'JWST', 'Spitzer'],
        'wavelength_range': ['0.5-2.5', '0.6-5.0', '1.0-5.0']
    })
    metadata_path = processed_dir / 'metadata.csv'
    metadata_df.to_csv(metadata_path, index=False)
    
    # Create mock spectrum files (empty files are enough for existence check in this test)
    for planet in ['HD_209458_b', 'WASP_121_b', 'K2_18_b']:
        (raw_dir / f"{planet}.fits").touch()
        
    yield {
        'raw_dir': str(raw_dir),
        'processed_dir': str(processed_dir),
        'metadata_path': str(metadata_path),
        'output_path': str(processed_dir / 'retrieval_results.csv')
    }
    
    shutil.rmtree(temp_root)

@patch('retrieval_output.get_config')
@patch('retrieval_output.run_single_spectrum_retrieval')
@patch('retrieval_output.calculate_mdc')
@patch('retrieval_output.detect_low_snr_spectrum')
def test_retrieval_output_generation(mock_detect, mock_mdc, mock_retrieval, mock_config, temp_dirs):
    """
    Test that process_retrieval_results correctly generates the output CSV
    with the required columns and handles upper limits.
    """
    # Setup mocks
    mock_config.return_value = {
        'paths': {
            'raw_data': temp_dirs['raw_dir'],
            'processed_data': temp_dirs['processed_dir']
        }
    }
    
    # Mock detection logic:
    # HD_209458_b (SNR 50) -> Normal
    # WASP_121_b (SNR 10) -> Low SNR (Upper Limit)
    # K2_18_b (SNR 2) -> Low SNR (Upper Limit)
    def side_effect_detect(snr, res):
        return snr < 15 # Threshold for test
    
    mock_detect.side_effect = side_effect_detect
    mock_mdc.return_value = 1e-6
    
    # Mock retrieval result for normal case
    mock_result = RetrievalResult(
        planet_name='HD_209458_b',
        water_mixing_ratio=-4.0,
        uncertainty=0.5,
        censorship_status=CensorshipStatus.RESOLVED
    )
    mock_retrieval.return_value = mock_result

    # Execute
    process_retrieval_results(temp_dirs['metadata_path'], temp_dirs['output_path'])

    # Verify output file exists
    assert os.path.exists(temp_dirs['output_path']), "Output CSV was not created"

    # Verify content
    df_out = pd.read_csv(temp_dirs['output_path'])
    
    # Check columns
    expected_cols = [
        'planet_name', 'water_mixing_ratio', 'uncertainty', 
        'is_upper_limit', 'detection_limit', 'min_detectable_concentration'
    ]
    assert list(df_out.columns) == expected_cols, f"Columns mismatch: {list(df_out.columns)}"
    
    # Check row count
    assert len(df_out) == 3, "Expected 3 rows in output"

    # Check specific logic for HD_209458_b (Normal)
    row_0 = df_out.iloc[0]
    assert row_0['planet_name'] == 'HD_209458_b'
    assert row_0['water_mixing_ratio'] == -4.0
    assert row_0['uncertainty'] == 0.5
    assert row_0['is_upper_limit'] == False
    assert pd.notna(row_0['detection_limit'])
    assert pd.notna(row_0['min_detectable_concentration'])

    # Check specific logic for WASP_121_b (Upper Limit)
    row_1 = df_out.iloc[1]
    assert row_1['planet_name'] == 'WASP_121_b'
    assert row_1['is_upper_limit'] == True
    # For upper limits, water_mixing_ratio should be the detection limit
    assert pd.notna(row_1['water_mixing_ratio'])
    assert pd.notna(row_1['detection_limit'])
    
    # Check specific logic for K2_18_b (Upper Limit)
    row_2 = df_out.iloc[2]
    assert row_2['planet_name'] == 'K2_18_b'
    assert row_2['is_upper_limit'] == True

@patch('retrieval_output.get_config')
def test_empty_metadata_handling(mock_config, temp_dirs):
    """Test behavior when metadata has no valid entries or is empty."""
    mock_config.return_value = {
        'paths': {
            'raw_data': temp_dirs['raw_dir'],
            'processed_data': temp_dirs['processed_dir']
        }
    }
    
    # Create empty metadata
    empty_meta_path = Path(temp_dirs['processed_dir']) / 'empty_metadata.csv'
    pd.DataFrame(columns=['planet_name', 'snr', 'resolution']).to_csv(empty_meta_path, index=False)
    
    output_path = Path(temp_dirs['processed_dir']) / 'empty_results.csv'
    
    process_retrieval_results(str(empty_meta_path), str(output_path))
    
    assert os.path.exists(output_path)
    df_out = pd.read_csv(output_path)
    assert len(df_out) == 0
    # Verify headers are present even if empty
    expected_cols = [
        'planet_name', 'water_mixing_ratio', 'uncertainty', 
        'is_upper_limit', 'detection_limit', 'min_detectable_concentration'
    ]
    assert list(df_out.columns) == expected_cols