"""
Integration test for the Proxy Saver pipeline (T026).

This test verifies that the full pipeline (Extraction + Saving) works
end-to-end and produces the expected artifact.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from code.services.proxy_saver import run_proxy_saver_pipeline
from code.config import CONFIG

@pytest.fixture
def mock_extracted_data():
    """Mock data that simulates the output of run_proxy_extraction_pipeline."""
    return pd.DataFrame({
        'post_id': [1001, 1002, 1003, 1004, 1005],
        'user_id': ['user_A', 'user_B', 'user_A', 'user_C', 'user_B'],
        'control_proxy': [1.2, 0.5, 1.8, 0.0, 0.9],
        'timestamp_regularity': [0.85, 0.12, 0.91, 0.05, 0.45]
    })

def test_full_proxy_saver_pipeline(mock_extracted_data, tmp_path):
    """
    Integration test: Runs the proxy saver pipeline with mocked extraction.
    
    Verifies:
    1. The pipeline executes without error.
    2. The file `proxy_results.csv` is created in the expected location.
    3. The content matches the input data.
    """
    # Create a temporary directory to act as the project root for this test
    # We patch CONFIG.PROCESSED_DIR to point to this temp dir
    original_processed_dir = CONFIG.PROCESSED_DIR
    
    # We need to mock the config path or the function to use a temp path
    # Since CONFIG is a module-level object, we patch the attribute used in the function
    # The function uses CONFIG.PROCESSED_DIR directly.
    
    temp_processed_dir = tmp_path / "processed"
    temp_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch the CONFIG.PROCESSED_DIR temporarily
    with patch.object(CONFIG, 'PROCESSED_DIR', temp_processed_dir):
        # Also need to mock the extraction function to return our mock data
        # instead of running the real heavy extraction logic
        with patch('code.services.proxy_saver.run_proxy_extraction_pipeline', return_value=mock_extracted_data):
            # Run the pipeline
            run_proxy_saver_pipeline()
    
    # Verify output file exists
    output_file = temp_processed_dir / "proxy_results.csv"
    assert output_file.exists(), "proxy_results.csv was not created."
    
    # Verify content
    loaded_df = pd.read_csv(output_file)
    pd.testing.assert_frame_equal(loaded_df, mock_extracted_data)
    
    # Verify columns match T026 spec exactly
    expected_cols = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    assert list(loaded_df.columns) == expected_cols, "Columns do not match T026 specification."

def test_pipeline_handles_extraction_failure():
    """
    Integration test: Verifies the pipeline fails loudly if extraction returns None.
    """
    with patch('code.services.proxy_saver.run_proxy_extraction_pipeline', return_value=None):
        with pytest.raises(RuntimeError, match="Proxy extraction failed"):
            run_proxy_saver_pipeline()
