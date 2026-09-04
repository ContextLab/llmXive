"""
Integration test for proxy_saver.py service.

Tests the full pipeline from proxy extraction to saving results.
Verifies T026: data/processed/proxy_results.csv is created with correct format.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
import json

from code.services.proxy_saver import run_proxy_saver_pipeline, save_proxy_results
from code.config import CONFIG

@pytest.fixture
def mock_proxy_extractor(monkeypatch):
    """Mock the proxy extractor to return predictable data."""
    mock_data = [
        {
            'post_id': 'test_post_1',
            'user_id': 'test_user_1',
            'control_proxy': 0.75,
            'timestamp_regularity': 0.88
        },
        {
            'post_id': 'test_post_2',
            'user_id': 'test_user_1',
            'control_proxy': 0.65,
            'timestamp_regularity': 0.92
        },
        {
            'post_id': 'test_post_3',
            'user_id': 'test_user_2',
            'control_proxy': 0.85,
            'timestamp_regularity': 0.78
        }
    ]
    
    def mock_run_proxy_extraction_pipeline():
        return mock_data
    
    monkeypatch.setattr(
        'code.services.proxy_saver.run_proxy_extraction_pipeline',
        mock_run_proxy_extraction_pipeline
    )

def test_run_proxy_saver_pipeline_creates_file(mock_proxy_extractor, tmp_path):
    """Test that the full pipeline creates the output file."""
    # Override output path
    test_output_path = tmp_path / "proxy_results.csv"
    original_path = CONFIG.PROXY_RESULTS_PATH
    CONFIG.PROXY_RESULTS_PATH = test_output_path
    
    try:
        result_path = run_proxy_saver_pipeline()
        
        assert result_path.exists()
        assert result_path == test_output_path
    finally:
        CONFIG.PROXY_RESULTS_PATH = original_path

def test_run_proxy_saver_pipeline_correct_format(mock_proxy_extractor, tmp_path):
    """Test that the output file has correct format and content."""
    test_output_path = tmp_path / "proxy_results.csv"
    original_path = CONFIG.PROXY_RESULTS_PATH
    CONFIG.PROXY_RESULTS_PATH = test_output_path
    
    try:
        run_proxy_saver_pipeline()
        
        df = pd.read_csv(test_output_path)
        
        # Check columns
        expected_columns = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
        assert list(df.columns) == expected_columns
        
        # Check data types
        assert df['control_proxy'].dtype in ['float64', 'float32']
        assert df['timestamp_regularity'].dtype in ['float64', 'float32']
        
        # Check values
        assert len(df) == 3
        assert df.iloc[0]['post_id'] == 'test_post_1'
        assert df.iloc[0]['control_proxy'] == 0.75
    finally:
        CONFIG.PROXY_RESULTS_PATH = original_path

def test_run_proxy_saver_pipeline_integration_with_real_data(tmp_path):
    """
    Integration test with real proxy extraction data (if available).
    This test verifies the end-to-end flow when real data is present.
    """
    # This test is skipped if raw data is not available
    raw_data_path = CONFIG.RAW_DATA_PATH
    if not raw_data_path.exists():
        pytest.skip("Raw data file not available for integration test")
    
    # Override output path
    test_output_path = tmp_path / "proxy_results.csv"
    original_path = CONFIG.PROXY_RESULTS_PATH
    CONFIG.PROXY_RESULTS_PATH = test_output_path
    
    try:
        # Run the pipeline
        result_path = run_proxy_saver_pipeline()
        
        # Verify output
        assert result_path.exists()
        
        df = pd.read_csv(result_path)
        
        # Verify minimum requirements
        assert len(df) > 0
        assert 'post_id' in df.columns
        assert 'user_id' in df.columns
        assert 'control_proxy' in df.columns
        assert 'timestamp_regularity' in df.columns
        
        # Verify no null values in required columns
        assert not df['control_proxy'].isnull().any()
        assert not df['timestamp_regularity'].isnull().any()
    except Exception as e:
        # If proxy extraction fails due to missing dependencies, skip
        if "langdetect" in str(e) or "transformers" in str(e):
            pytest.skip(f"Dependency not available: {e}")
        raise
    finally:
        CONFIG.PROXY_RESULTS_PATH = original_path
