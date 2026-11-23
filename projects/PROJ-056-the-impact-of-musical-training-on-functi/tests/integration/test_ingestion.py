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

from data.preprocess import preprocess_subjects

class TestFullIngestion:
    """Test the full ingestion pipeline end-to-end."""

    def test_full_ingestion(self, tmp_path):
        """
        Implements T013 requirements:
        - Run the pipeline on synthetic data.
        - Assert output file exists at 'data/processed/subjects_cleaned.csv'.
        - Assert the file contains exactly 10 rows (as per task description example).
        """
        # Ensure the target directory exists
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = processed_dir / "subjects_cleaned.csv"
        
        # Remove existing file if present to ensure fresh run
        if output_file.exists():
            output_file.unlink()

        # Run the pipeline
        # We call the main preprocessing function which handles generation and cleaning
        # The function signature expects mode and potentially a count for synthetic
        preprocess_subjects(
            mode='verification',
            synthetic_count=10,
            output_path=str(output_file)
        )

        # Assert 1: File exists at the EXACT required path
        assert os.path.exists(str(output_file)), "Output file 'data/processed/subjects_cleaned.csv' does not exist."

        # Assert 2: Correct number of rows
        df = pd.read_csv(str(output_file))
        assert len(df) == 10, f"Expected 10 subjects, found {len(df)}."

        # Additional sanity checks based on T019 requirements
        required_cols = ['subject_id', 'group', 'years_of_training', 'age', 'sex', 'motion_score', 'ses_score']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

        # Verify filtering logic: All subjects should have years_of_training >= 1
        # The preprocessing step should have filtered out any < 1
        if 'years_of_training' in df.columns:
            assert (df['years_of_training'] >= 1).all(), "Filtering logic failed: found subjects with < 1 year training."

    def test_analysis_mode_missing_data(self, tmp_path):
        """
        Test that analysis mode raises an error if real data is missing.
        """
        output_file = tmp_path / "subjects_cleaned.csv"
        
        from data.download import DataAccessError
        
        with pytest.raises(DataAccessError) as excinfo:
            preprocess_subjects(
                mode='analysis',
                output_path=str(output_file)
            )
        
        assert "Real data required" in str(excinfo.value)