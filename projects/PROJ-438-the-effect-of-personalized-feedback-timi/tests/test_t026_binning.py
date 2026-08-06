import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from bin_feedback_groups import assign_feedback_group, bin_feedback_groups, save_binned_data

class TestT026Binning:
    """
    Tests for T026: Generate data/processed/learners_binned.csv with interval and group columns.
    
    Validates the binning logic defined in FR-004:
    - Immediate: < 2h
    - Delayed: 2h - 48h
    - Variable: > 48h
    """

    def test_assign_immediate_group(self):
        """Test that intervals < 2h are assigned 'Immediate'."""
        data = {
            'learner_id': [1, 2, 3],
            'median_interval_hours': [0.5, 1.9, 0.0]
        }
        df = pd.DataFrame(data)
        result = assign_feedback_group(df)
        
        assert all(result['feedback_group'] == "Immediate")

    def test_assign_delayed_group(self):
        """Test that intervals between 2h and 48h are assigned 'Delayed'."""
        data = {
            'learner_id': [4, 5, 6],
            'median_interval_hours': [2.0, 24.0, 48.0]
        }
        df = pd.DataFrame(data)
        result = assign_feedback_group(df)
        
        assert all(result['feedback_group'] == "Delayed")

    def test_assign_variable_group(self):
        """Test that intervals > 48h are assigned 'Variable'."""
        data = {
            'learner_id': [7, 8, 9],
            'median_interval_hours': [48.1, 100.0, 720.0]
        }
        df = pd.DataFrame(data)
        result = assign_feedback_group(df)
        
        assert all(result['feedback_group'] == "Variable")

    def test_boundary_conditions(self):
        """Test exact boundary values."""
        data = {
            'learner_id': [10, 11],
            'median_interval_hours': [2.0, 48.0]
        }
        df = pd.DataFrame(data)
        result = assign_feedback_group(df)
        
        # 2.0 is the start of Delayed (>= 2)
        assert result.loc[result['learner_id'] == 10, 'feedback_group'].values[0] == "Delayed"
        # 48.0 is the end of Delayed (<= 48)
        assert result.loc[result['learner_id'] == 11, 'feedback_group'].values[0] == "Delayed"

    def test_nan_handling(self):
        """Test that NaN intervals result in NaN group."""
        data = {
            'learner_id': [12],
            'median_interval_hours': [np.nan]
        }
        df = pd.DataFrame(data)
        result = assign_feedback_group(df)
        
        assert pd.isna(result['feedback_group'].values[0])

    def test_binning_categorical_type(self):
        """Test that bin_feedback_groups converts to categorical."""
        data = {
            'learner_id': [13, 14],
            'median_interval_hours': [1.0, 50.0]
        }
        df = pd.DataFrame(data)
        df = assign_feedback_group(df)
        df_binned = bin_feedback_groups(df)
        
        assert isinstance(df_binned['feedback_group'].dtype, pd.CategoricalDtype)
        assert "Immediate" in df_binned['feedback_group'].cat.categories
        assert "Delayed" in df_binned['feedback_group'].cat.categories
        assert "Variable" in df_binned['feedback_group'].cat.categories

    def test_save_binned_data_creates_file(self, tmp_path):
        """Test that save_binned_data writes a valid CSV."""
        data = {
            'learner_id': [15],
            'median_interval_hours': [1.0],
            'feedback_group': ['Immediate']
        }
        df = pd.DataFrame(data)
        
        output_file = tmp_path / "test_binned.csv"
        save_binned_data(df, str(output_file))
        
        assert output_file.exists()
        
        # Read back and verify
        loaded_df = pd.read_csv(output_file)
        assert len(loaded_df) == 1
        assert loaded_df['feedback_group'].iloc[0] == "Immediate"
        assert 'learner_id' in loaded_df.columns
        assert 'median_interval_hours' in loaded_df.columns
