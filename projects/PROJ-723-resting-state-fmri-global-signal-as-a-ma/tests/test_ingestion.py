import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function under test
from ingestion import check_zero_variance_subjects, generate_cleaned_data

class TestZeroVarianceCheck:
    """
    Unit tests for T015: Zero-variance check implementation.
    """

    def test_no_zero_variance_subjects(self):
        """
        Test that subjects with non-zero Global_Signal_SD are kept.
        """
        data = {
            "Subject_ID": ["sub-01", "sub-02", "sub-03"],
            "Global_Signal_SD": [0.5, 0.8, 1.2],
            "MWQ_Score": [10, 15, 20]
        }
        df = pd.DataFrame(data)
        
        result = check_zero_variance_subjects(df, column="Global_Signal_SD")
        
        # All subjects should be kept
        assert len(result) == 3
        assert list(result["Subject_ID"]) == ["sub-01", "sub-02", "sub-03"]

    def test_with_zero_variance_subjects(self):
        """
        Test that subjects with Global_Signal_SD == 0 are excluded.
        """
        data = {
            "Subject_ID": ["sub-01", "sub-02", "sub-03", "sub-04"],
            "Global_Signal_SD": [0.5, 0.0, 1.2, 0.0],
            "MWQ_Score": [10, 15, 20, 25]
        }
        df = pd.DataFrame(data)
        
        result = check_zero_variance_subjects(df, column="Global_Signal_SD")
        
        # Only sub-01 and sub-03 should remain
        assert len(result) == 2
        assert list(result["Subject_ID"]) == ["sub-01", "sub-03"]
        assert all(result["Global_Signal_SD"] > 0)

    def test_column_not_found(self):
        """
        Test that a ValueError is raised if the column does not exist.
        """
        data = {
            "Subject_ID": ["sub-01"],
            "Wrong_Column": [0.5]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError) as excinfo:
            check_zero_variance_subjects(df, column="Global_Signal_SD")
        
        assert "Column 'Global_Signal_SD' not found" in str(excinfo.value)

    def test_all_zero_variance(self):
        """
        Test that all subjects are excluded if all have zero variance.
        """
        data = {
            "Subject_ID": ["sub-01", "sub-02"],
            "Global_Signal_SD": [0.0, 0.0],
            "MWQ_Score": [10, 15]
        }
        df = pd.DataFrame(data)
        
        result = check_zero_variance_subjects(df, column="Global_Signal_SD")
        
        # All subjects should be excluded
        assert len(result) == 0
        assert list(result.columns) == ["Subject_ID", "Global_Signal_SD", "MWQ_Score"]

    def test_integration_with_csv_io(self):
        """
        Test the full pipeline: write CSV, run check, read back.
        This verifies that the function works with real file I/O.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create input data with some zero-variance subjects
            data = {
                "Subject_ID": ["sub-01", "sub-02", "sub-03", "sub-04"],
                "Global_Signal_SD": [0.5, 0.0, 1.2, 0.0],
                "MWQ_Score": [10, 15, 20, 25],
                "Age": [25, 30, 22, 28],
                "Sex": ["M", "F", "M", "F"]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)
            
            # Run the pipeline
            from utils import read_csv, write_csv
            from ingestion import check_zero_variance_subjects
            
            df_loaded = read_csv(input_path)
            df_cleaned = check_zero_variance_subjects(df_loaded, column="Global_Signal_SD")
            write_csv(df_cleaned, output_path)
            
            # Verify output
            df_output = read_csv(output_path)
            
            assert len(df_output) == 2
            assert set(df_output["Subject_ID"]) == {"sub-01", "sub-03"}
            assert all(df_output["Global_Signal_SD"] > 0)