import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ingestion import generate_cleaned_data, check_zero_variance_subjects, apply_motion_exclusion

class TestT016CleanedData:
    def test_motion_exclusion_removes_high_fd(self):
        """Test that subjects with Mean_FD > 0.5 are removed."""
        data = pd.DataFrame({
            'Subject_ID': ['A', 'B', 'C'],
            'Global_Signal_SD': [0.1, 0.2, 0.3],
            'MWQ_Score': [10, 11, 12],
            'Age': [20, 21, 22],
            'Sex': ['M', 'F', 'M'],
            'Mean_FD': [0.4, 0.6, 0.3],
            'Mean_DVARS': [0.2, 0.3, 0.4]
        })
        result = apply_motion_exclusion(data, threshold=0.5)
        assert len(result) == 2
        assert 'B' not in result['Subject_ID'].values

    def test_zero_variance_exclusion(self):
        """Test that subjects with Global_Signal_SD == 0 are removed."""
        data = pd.DataFrame({
            'Subject_ID': ['A', 'B', 'C'],
            'Global_Signal_SD': [0.1, 0.0, 0.3],
            'Mean_FD': [0.2, 0.2, 0.2],
            'Mean_DVARS': [0.2, 0.2, 0.2],
            'MWQ_Score': [10, 11, 12],
            'Age': [20, 21, 22],
            'Sex': ['M', 'F', 'M']
        })
        result = check_zero_variance_subjects(data)
        assert len(result) == 2
        assert 'B' not in result['Subject_ID'].values

    def test_pipeline_generates_output_file(self, tmp_path):
        """Test the full pipeline generates the CSV."""
        # Setup temporary raw directory with test data
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        output_file = tmp_path / "processed" / "cleaned_data.csv"
        
        # Write test raw files
        fmri_data = pd.DataFrame({
            'Subject_ID': ['1', '2'],
            'Global_Signal_SD': [0.1, 0.2],
            'Mean_FD': [0.3, 0.6],
            'Mean_DVARS': [0.2, 0.3]
        })
        fmri_data.to_csv(raw_dir / "hcp_fmri_metrics.csv", index=False)
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['1', '2'],
            'MWQ_Score': [10, 11],
            'Age': [20, 21],
            'Sex': ['M', 'F']
        })
        mwq_data.to_csv(raw_dir / "mwq_scores.csv", index=False)
        
        # Run pipeline
        generate_cleaned_data(raw_dir, output_file)
        
        # Verify output
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == 1  # Subject 2 should be excluded due to FD > 0.5
        assert list(df.columns) == ['Subject_ID', 'Global_Signal_SD', 'MWQ_Score', 'Age', 'Sex', 'Mean_FD', 'Mean_DVARS']