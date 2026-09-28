import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import check_zero_variance_subjects, apply_motion_exclusion, validate_schema

class TestZeroVarianceCheck:
    """Tests for T015: Zero-variance check implementation."""

    def test_no_zero_variance(self, caplog):
        """Test that subjects with non-zero variance are kept."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3'],
            'global_signal_sd': [0.5, 1.2, 0.8]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        assert len(filtered_df) == 3
        assert "No subjects with zero variance found" in log_msg

    def test_with_zero_variance(self, caplog):
        """Test that subjects with zero variance are excluded and logged."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3', 'S4'],
            'global_signal_sd': [0.5, 0.0, 1.2, 0.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        # S2 and S4 should be excluded
        assert len(filtered_df) == 2
        assert filtered_df['Subject_ID'].tolist() == ['S1', 'S3']
        
        # Check logging
        assert "Excluded 2 subjects with global_signal_sd == 0" in log_msg
        assert "Excluded Subject IDs: ['S2', 'S4']" in log_msg

    def test_missing_column(self, caplog):
        """Test behavior when the specified column is missing."""
        data = {
            'Subject_ID': ['S1', 'S2'],
            'other_col': [1.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        assert len(filtered_df) == 2 # No filtering happened
        assert "Column 'global_signal_sd' not found" in log_msg

class TestMotionExclusion:
    """Tests for T014: Motion exclusion implementation."""

    def test_motion_exclusion_threshold(self, caplog):
        """Test that subjects with high FD are excluded."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3'],
            'Mean_FD': [0.2, 0.6, 0.4]
        }
        df = pd.DataFrame(data)
        
        filtered_df = apply_motion_exclusion(df, threshold=0.5)
        
        assert len(filtered_df) == 2
        assert filtered_df['Subject_ID'].tolist() == ['S1', 'S3']
        assert "Excluded 1 subjects (FD > 0.5mm)" in caplog.text

class TestSchemaValidation:
    """Tests for T010: Schema validation."""

    def test_valid_schema(self):
        """Test that valid data passes validation."""
        data = {
            'Subject_ID': ['S1'],
            'global_signal': [1.0],
            'global_signal_sd': [0.5],
            'MWQ_Score': [10],
            'Age': [25],
            'Sex': ['M'],
            'Mean_FD': [0.2],
            'Mean_DVARS': [0.1]
        }
        df = pd.DataFrame(data)
        # Should not raise
        validate_schema(df)

    def test_invalid_schema(self):
        """Test that missing columns raise an error."""
        data = {
            'Subject_ID': ['S1'],
            'global_signal': [1.0]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="FATAL: Dataset Mismatch"):
            validate_schema(df)
