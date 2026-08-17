"""
Integration tests for the ingestion pipeline.
Implements T013: Integration test for full ingestion pipeline on synthetic data.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.output_cleaned_subjects import write_cleaned_subjects
from data.download import DataAccessError

class TestFullIngestion:
    """Test the full ingestion pipeline end-to-end."""

    def test_full_ingestion(self, tmp_path):
        """
        Implements T013 requirements:
        - Run the pipeline on synthetic data.
        - Assert output file exists at 'data/processed/subjects_cleaned.csv'.
        - Assert the file contains exactly 10 rows (as per task description example).
        """
        # Set output path to a temporary directory to avoid side effects
        output_file = tmp_path / "subjects_cleaned.csv"
        
        # Run the pipeline
        # We pass the tmp_path as output to keep the test isolated
        result_path = write_cleaned_subjects(
            mode='verification',
            synthetic_count=10,
            output_path=str(output_file)
        )

        # Assert 1: File exists
        assert os.path.exists(str(output_file)), "Output file 'data/processed/subjects_cleaned.csv' does not exist."

        # Assert 2: Correct number of rows
        df = pd.read_csv(str(output_file))
        assert len(df) == 10, f"Expected 10 subjects, found {len(df)}."

        # Additional sanity checks based on T019 requirements
        required_cols = ['subject_id', 'group', 'years_of_training', 'age', 'sex', 'motion_score', 'ses_score']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

        # Verify filtering logic (T015): All subjects should have years_of_training >= 1
        # Note: The synthetic generator might produce some < 1, but the filter should remove them.
        # If the synthetic generator is configured to only produce >= 1, then all should pass.
        # The task T015 says "filter subjects by years_of_training (>=1)".
        # If the synthetic data has < 1, they should be gone.
        if 'years_of_training' in df.columns:
            assert (df['years_of_training'] >= 1).all(), "Filtering logic failed: found subjects with < 1 year training."

    def test_analysis_mode_missing_data(self, tmp_path):
        """
        Test that analysis mode raises an error if real data is missing.
        """
        output_file = tmp_path / "subjects_cleaned.csv"
        
        with pytest.raises(DataAccessError) as excinfo:
            write_cleaned_subjects(
                mode='analysis',
                output_path=str(output_file)
            )
        
        assert "Real data required" in str(excinfo.value)
