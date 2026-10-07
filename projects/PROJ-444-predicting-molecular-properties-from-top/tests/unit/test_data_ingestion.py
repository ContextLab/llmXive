"""
Unit tests for T008a: Data Ingestion (Fetch, Validate, Power Analysis).

These tests verify the logic of the data ingestion pipeline without necessarily
fetching the real dataset every time (though the main script does).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from code import data_ingestion

def test_validate_schema_missing_columns():
    """Test that validation fails if required columns are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake CSV with missing columns
        fake_csv = Path(tmpdir) / "fake.csv"
        df_fake = pd.DataFrame({"wrong_col": [1, 2, 3], "logP": [1.0, 2.0, 3.0]})
        df_fake.to_csv(fake_csv, index=False)
        
        # Temporarily override the raw file path
        original_path = data_ingestion.ESOL_RAW_FILE
        data_ingestion.ESOL_RAW_FILE = fake_csv
        
        try:
            is_valid, errors = data_ingestion.validate_schema(MagicMock())
            assert not is_valid
            assert any("Missing required columns" in err for err in errors)
        finally:
            data_ingestion.ESOL_RAW_FILE = original_path

def test_validate_schema_missing_values():
    """Test that validation fails if required columns have NaN."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_csv = Path(tmpdir) / "fake.csv"
        df_fake = pd.DataFrame({"smiles": ["CC", None, "CCC"], "logP": [1.0, 2.0, 3.0]})
        df_fake.to_csv(fake_csv, index=False)
        
        original_path = data_ingestion.ESOL_RAW_FILE
        data_ingestion.ESOL_RAW_FILE = fake_csv
        
        try:
            is_valid, errors = data_ingestion.validate_schema(MagicMock())
            assert not is_valid
            assert any("missing values" in err for err in errors)
        finally:
            data_ingestion.ESOL_RAW_FILE = original_path

def test_validate_schema_success():
    """Test that validation passes with correct data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_csv = Path(tmpdir) / "fake.csv"
        df_fake = pd.DataFrame({"smiles": ["CC", "CCC", "CCCC"], "logP": [1.0, 2.0, 3.0]})
        df_fake.to_csv(fake_csv, index=False)
        
        original_path = data_ingestion.ESOL_RAW_FILE
        data_ingestion.ESOL_RAW_FILE = fake_csv
        
        try:
            is_valid, errors = data_ingestion.validate_schema(MagicMock())
            assert is_valid
            assert len(errors) == 0
        finally:
            data_ingestion.ESOL_RAW_FILE = original_path

def test_perform_power_analysis():
    """Test the power analysis calculation logic."""
    # Create a dummy dataframe
    df = pd.DataFrame({"smiles": ["CC"] * 200, "logP": [1.0] * 200})
    
    logger = MagicMock()
    report = data_ingestion.perform_power_analysis(df, logger)
    
    assert "parameters" in report
    assert "results" in report
    assert report["results"]["actual_sample_size"] == 200
    assert report["results"]["power_check_passed"] is True
    assert report["parameters"]["min_n_required"] >= 128

def test_perform_power_analysis_insufficient():
    """Test power analysis fails with small N."""
    df = pd.DataFrame({"smiles": ["CC"] * 50, "logP": [1.0] * 50})
    
    logger = MagicMock()
    report = data_ingestion.perform_power_analysis(df, logger)
    
    assert report["results"]["power_check_passed"] is False
    assert report["results"]["actual_sample_size"] == 50

def test_fetch_esol_dataset_file_exists():
    """Test fetch logic when file already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_csv = Path(tmpdir) / "dataset_esol.csv"
        fake_csv.touch() # Create empty file
        
        original_path = data_ingestion.ESOL_RAW_FILE
        data_ingestion.ESOL_RAW_FILE = fake_csv
        
        try:
            # Mock requests to ensure we don't actually fetch
            with patch('code.data_ingestion.requests.get') as mock_get:
                result = data_ingestion.fetch_esol_dataset(MagicMock())
                mock_get.assert_not_called()
                assert result is True
        finally:
            data_ingestion.ESOL_RAW_FILE = original_path

def test_main_flow_success():
    """Test the full main flow with mocked dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup paths
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        fake_csv = raw_dir / "dataset_esol.csv"
        df_fake = pd.DataFrame({"smiles": ["CC"] * 200, "logP": [1.0] * 200})
        df_fake.to_csv(fake_csv, index=False)
        
        proc_dir = Path(tmpdir) / "data" / "processed"
        proc_dir.mkdir(parents=True)
        
        logs_dir = Path(tmpdir) / "data" / "logs"
        logs_dir.mkdir(parents=True)
        
        # Patch paths
        original_raw = data_ingestion.ESOL_RAW_FILE
        original_proc = data_ingestion.DATA_PROCESSED_DIR
        original_logs = data_ingestion.DATA_LOGS_DIR
        
        data_ingestion.ESOL_RAW_FILE = fake_csv
        data_ingestion.DATA_PROCESSED_DIR = proc_dir
        data_ingestion.DATA_LOGS_DIR = logs_dir
        
        try:
            # Mock sys.exit to prevent actual exit
            with patch('sys.exit') as mock_exit:
                data_ingestion.main()
                # Verify sys.exit was not called with error code
                mock_exit.assert_not_called()
                
                # Verify report file was created
                report_file = proc_dir / "power_analysis_report.json"
                assert report_file.exists()
                
                with open(report_file) as f:
                    report = json.load(f)
                
                assert report["results"]["power_check_passed"] is True
        finally:
            data_ingestion.ESOL_RAW_FILE = original_raw
            data_ingestion.DATA_PROCESSED_DIR = original_proc
            data_ingestion.DATA_LOGS_DIR = original_logs