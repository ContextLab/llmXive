"""
Unit tests for the download module, specifically focusing on subject exclusion logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import create_subject_list


class TestSubjectExclusion:
    """Tests for the subject exclusion logic in T016."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock phenotypic DataFrame
        data = {
            'Subject': ['1001', '1002', '1003', '1004', '1005'],
            'MeanFD': [0.1, 0.2, np.nan, 0.15, 0.3],
            'age': [20, 22, 21, np.nan, 24],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'full_2_iq': [100, 110, 105, 95, np.nan]
        }
        self.df = pd.DataFrame(data)

    def test_excludes_missing_mean_fd(self):
        """Test that subjects with missing MeanFD are excluded."""
        valid_ids = create_subject_list(self.df, required_columns=['MeanFD'])
        # 1003 has NaN MeanFD
        assert '1003' not in valid_ids
        assert len(valid_ids) == 4

    def test_excludes_missing_multiple_columns(self):
        """Test exclusion when multiple required columns have missing data."""
        valid_ids = create_subject_list(self.df, required_columns=['MeanFD', 'age', 'full_2_iq'])
        # 1003 missing MeanFD
        # 1004 missing age
        # 1005 missing full_2_iq
        # Only 1001 and 1002 should remain
        assert len(valid_ids) == 2
        assert '1001' in valid_ids
        assert '1002' in valid_ids

    def test_all_valid(self):
        """Test that all subjects are kept if no required columns are missing."""
        clean_df = self.df.dropna(subset=['MeanFD', 'age', 'full_2_iq'])
        valid_ids = create_subject_list(clean_df, required_columns=['MeanFD', 'age', 'full_2_iq'])
        assert len(valid_ids) == len(clean_df)

    def test_missing_required_column_name(self):
        """Test behavior when a required column name does not exist in the DataFrame."""
        # Should return empty list or handle gracefully
        valid_ids = create_subject_list(self.df, required_columns=['NonExistentColumn'])
        assert len(valid_ids) == 0

    def test_default_columns(self):
        """Test that default columns are used if not specified."""
        # Defaults: ['MeanFD', 'age', 'sex', 'full_2_iq']
        # 1003 missing MeanFD, 1004 missing age, 1005 missing full_2_iq
        valid_ids = create_subject_list(self.df)
        assert len(valid_ids) == 2