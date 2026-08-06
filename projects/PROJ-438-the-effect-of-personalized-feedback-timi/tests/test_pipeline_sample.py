import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from bin_feedback_groups import assign_feedback_group, bin_feedback_groups, save_binned_data

class TestPipelineSample:
    """
    Integration test for T026 on a small sample (N=100).
    Verifies the full flow from intervals to binned output.
    """

    def test_full_binning_pipeline_sample(self):
        """Simulate T024 output and run T026 binning logic."""
        # Create a synthetic sample of 100 learners with varied intervals
        np.random.seed(42)
        n_samples = 100
        
        # Generate random intervals: mostly normal, some outliers
        intervals = np.random.exponential(scale=12.0, size=n_samples)
        # Ensure some are < 2, some 2-48, some > 48
        intervals[0] = 0.5   # Immediate
        intervals[1] = 1.9   # Immediate
        intervals[2] = 2.0   # Delayed (boundary)
        intervals[3] = 24.0  # Delayed
        intervals[4] = 48.0  # Delayed (boundary)
        intervals[5] = 48.1  # Variable
        intervals[6] = 100.0 # Variable
        
        df_input = pd.DataFrame({
            'learner_id': range(n_samples),
            'median_interval_hours': intervals,
            'course_id': np.random.choice(['A', 'B', 'C'], n_samples)
        })
        
        # Run the logic from T026
        df_binned = assign_feedback_group(df_input)
        df_binned = bin_feedback_groups(df_binned)
        
        # Verify counts
        assert len(df_binned) == n_samples
        assert 'feedback_group' in df_binned.columns
        
        # Verify specific boundary cases
        assert df_binned.loc[df_binned['learner_id'] == 0, 'feedback_group'].values[0] == "Immediate"
        assert df_binned.loc[df_binned['learner_id'] == 2, 'feedback_group'].values[0] == "Delayed"
        assert df_binned.loc[df_binned['learner_id'] == 5, 'feedback_group'].values[0] == "Variable"
        
        # Verify group distribution makes sense (at least one in each)
        counts = df_binned['feedback_group'].value_counts()
        assert counts.get("Immediate", 0) > 0
        assert counts.get("Delayed", 0) > 0
        assert counts.get("Variable", 0) > 0

    def test_pipeline_with_missing_values(self):
        """Test pipeline handles NaN intervals gracefully."""
        data = {
            'learner_id': [1, 2, 3, 4],
            'median_interval_hours': [1.0, np.nan, 24.0, np.nan],
            'course_id': ['A', 'A', 'B', 'B']
        }
        df = pd.DataFrame(data)
        
        df_binned = assign_feedback_group(df)
        df_binned = bin_feedback_groups(df_binned)
        
        # Check that valid rows are binned
        assert df_binned.loc[df_binned['learner_id'] == 1, 'feedback_group'].values[0] == "Immediate"
        assert df_binned.loc[df_binned['learner_id'] == 3, 'feedback_group'].values[0] == "Delayed"
        
        # Check that NaN rows result in NaN group
        assert pd.isna(df_binned.loc[df_binned['learner_id'] == 2, 'feedback_group'].values[0])
        assert pd.isna(df_binned.loc[df_binned['learner_id'] == 4, 'feedback_group'].values[0])

    def test_output_file_integrity(self, tmp_path):
        """Verify the generated CSV file is readable and contains expected columns."""
        # Create sample data
        df_input = pd.DataFrame({
            'learner_id': [100, 101, 102],
            'median_interval_hours': [1.5, 10.0, 60.0],
            'course_id': ['X', 'Y', 'Z']
        })
        
        df_binned = assign_feedback_group(df_input)
        df_binned = bin_feedback_groups(df_binned)
        
        output_path = tmp_path / "learners_binned_sample.csv"
        save_binned_data(df_binned, str(output_path))
        
        # Read back
        df_result = pd.read_csv(output_path)
        
        # Validate columns
        expected_cols = ['learner_id', 'median_interval_hours', 'course_id', 'feedback_group']
        for col in expected_cols:
            assert col in df_result.columns, f"Missing column: {col}"
        
        # Validate content
        assert len(df_result) == 3
        assert df_result['feedback_group'].iloc[0] == "Immediate"
        assert df_result['feedback_group'].iloc[1] == "Delayed"
        assert df_result['feedback_group'].iloc[2] == "Variable"