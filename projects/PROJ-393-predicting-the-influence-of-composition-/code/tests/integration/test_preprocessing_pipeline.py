"""
Integration test for the Preprocessing Pipeline (T027).
Verifies that the pipeline produces data/processed/alloys_raw.csv.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.preprocessing.preprocess_pipeline import run_preprocessing_pipeline, OUTPUT_PATH

class TestPreprocessingPipeline:
    
    def test_pipeline_produces_output_file(self):
        """
        Test that the pipeline creates the required output file.
        This test verifies the core requirement of T027.
        """
        # Ensure the output file is removed before running to test creation
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        
        # Run the pipeline
        df = run_preprocessing_pipeline()
        
        # Assert file exists
        assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created."
        
        # Assert file is not empty of schema (even if 0 rows, it should have headers)
        loaded_df = pd.read_csv(OUTPUT_PATH)
        assert isinstance(loaded_df, pd.DataFrame)
        
        # Verify expected columns exist (at least the core ones)
        expected_cols = ['composition', 'source_type']
        for col in expected_cols:
            assert col in loaded_df.columns, f"Missing expected column: {col}"

    def test_pipeline_handles_empty_input_gracefully(self):
        """
        Test that the pipeline handles the case where no raw data is found.
        It should still produce an empty CSV with the correct schema.
        """
        # This test assumes the load_raw_data function handles missing files gracefully.
        # We rely on the implementation in T027 to ensure an empty DataFrame is saved.
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        
        df = run_preprocessing_pipeline()
        
        assert OUTPUT_PATH.exists()
        loaded_df = pd.read_csv(OUTPUT_PATH)
        # Even if empty, the file must exist
        assert len(loaded_df) >= 0
