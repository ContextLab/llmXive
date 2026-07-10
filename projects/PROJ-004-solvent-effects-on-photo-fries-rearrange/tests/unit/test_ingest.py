"""
Unit tests for the Real Data Ingestion module (code/data/ingest.py).

These tests verify the strict constraints of T015b:
1. Failing loudly if real data is missing.
2. Successfully loading and validating real data.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.ingest import ingest_real_transient_absorption_data
from code.config import get_raw_data_path, get_processed_data_path

class TestRealDataIngestion:
    
    def test_missing_file_raises_file_not_found(self):
        """
        T015b Constraint: MUST fail the pipeline with a clear error if the real data file is missing.
        """
        # Create a temporary directory to simulate a missing file in a clean path
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the raw data path to point to an empty temp dir
            # We do this by patching the function or using a mock path if possible.
            # Since the function uses config paths, we will test the error message logic
            # by ensuring the file doesn't exist where expected.
            
            # Note: To test this robustly without changing global config state,
            # we rely on the fact that 'real_traces.csv' won't exist in the default path
            # if we are in a clean test environment. However, to be safe, we create a
            # specific test scenario where we know the file is missing.
            
            # Since the function hardcodes the filename 'real_traces.csv' in the config path,
            # and we cannot easily mock the config path without side effects,
            # we will assert that if we create a temp dir and point the logic there, it fails.
            # But the function uses `get_raw_data_path()`.
            
            # Alternative: We assume the test environment does not have the file.
            # If it does, we skip.
            # Better: We mock the `os.path.exists` check inside the module.
            
            with pytest.raises(FileNotFoundError) as exc_info:
                # We pass a filename that definitely doesn't exist in the raw path
                # The function looks for `input_filename` in `get_raw_data_path()`
                ingest_real_transient_absorption_data(input_filename="non_existent_fake_file.csv")
            
            assert "Real data file not found" in str(exc_info.value)
            assert "CRITICAL ERROR" in str(exc_info.value)

    def test_empty_file_raises_value_error(self):
        """
        T015b Constraint: Must fail if the data file is empty.
        """
        raw_path = get_raw_data_path()
        os.makedirs(raw_path, exist_ok=True)
        
        empty_file = os.path.join(raw_path, "empty_test.csv")
        
        # Create empty file
        with open(empty_file, 'w') as f:
            pass # Create empty file
        
        try:
            with pytest.raises(ValueError) as exc_info:
                ingest_real_transient_absorption_data(input_filename="empty_test.csv")
            
            assert "empty" in str(exc_info.value).lower()
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)

    def test_missing_required_columns_raises_value_error(self):
        """
        T015b Constraint: Must fail if required columns are missing.
        """
        raw_path = get_raw_data_path()
        os.makedirs(raw_path, exist_ok=True)
        
        bad_file = os.path.join(raw_path, "bad_cols.csv")
        
        # Create file with wrong columns
        df_bad = pd.DataFrame({"wrong_col": [1, 2, 3]})
        df_bad.to_csv(bad_file, index=False)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                ingest_real_transient_absorption_data(input_filename="bad_cols.csv")
            
            assert "Missing required columns" in str(exc_info.value)
        finally:
            if os.path.exists(bad_file):
                os.remove(bad_file)

    def test_valid_data_loads_and_writes_output(self):
        """
        T015b Constraint: Successfully ingests real data and writes to processed.
        """
        raw_path = get_raw_data_path()
        proc_path = get_processed_data_path()
        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(proc_path, exist_ok=True)
        
        valid_file = os.path.join(raw_path, "valid_test.csv")
        output_file = os.path.join(proc_path, "valid_test_out.csv")
        
        # Create valid data
        df_valid = pd.DataFrame({
            "time_ns": [0.0, 1.0, 2.0, 3.0],
            "absorbance": [0.1, 0.2, 0.15, 0.1],
            "wavelength_nm": [350.0, 350.0, 350.0, 350.0],
            "solvent": ["acetonitrile"] * 4
        })
        df_valid.to_csv(valid_file, index=False)
        
        try:
            # Run ingestion
            result_df = ingest_real_transient_absorption_data(
                input_filename="valid_test.csv",
                output_filename="valid_test_out.csv"
            )
            
            # Verify returned dataframe
            assert result_df.equals(df_valid)
            assert len(result_df) == 4
            assert "time_ns" in result_df.columns
            
            # Verify output file was written
            assert os.path.exists(output_file)
            df_written = pd.read_csv(output_file)
            assert df_written.equals(df_valid)
            
        finally:
            if os.path.exists(valid_file):
                os.remove(valid_file)
            if os.path.exists(output_file):
                os.remove(output_file)
