"""
Unit tests for T026: Generate binned learners dataset.

Tests verify that the pipeline correctly loads intervals, assigns groups,
and saves the output file with the expected schema.
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups, save_binned_data

class TestBinningLogic:
    """Test the core binning logic without file I/O."""

    def test_assign_feedback_group_immediate(self):
        """Test assignment for interval < 2 hours."""
        assert assign_feedback_group(1.5) == "Immediate"
        assert assign_feedback_group(0.1) == "Immediate"
        assert assign_feedback_group(1.99) == "Immediate"

    def test_assign_feedback_group_delayed(self):
        """Test assignment for interval 2h <= x <= 48h."""
        assert assign_feedback_group(2.0) == "Delayed"
        assert assign_feedback_group(24.0) == "Delayed"
        assert assign_feedback_group(48.0) == "Delayed"

    def test_assign_feedback_group_variable(self):
        """Test assignment for interval > 48 hours."""
        assert assign_feedback_group(48.01) == "Variable"
        assert assign_feedback_group(100.0) == "Variable"

    def test_bin_feedback_groups_dataframe(self):
        """Test binning on a sample dataframe."""
        data = {
            'learner_id': ['L1', 'L2', 'L3', 'L4'],
            'median_interval': [1.0, 2.0, 25.0, 50.0]
        }
        df = pd.DataFrame(data)
        result = bin_feedback_groups(df)
        
        assert 'feedback_group' in result.columns
        assert len(result) == 4
        assert result.iloc[0]['feedback_group'] == "Immediate"
        assert result.iloc[1]['feedback_group'] == "Delayed"
        assert result.iloc[2]['feedback_group'] == "Delayed"
        assert result.iloc[3]['feedback_group'] == "Variable"

class TestSaveBinnedData:
    """Test file saving functionality."""

    def test_save_binned_data_creates_file(self):
        """Verify that save_binned_data creates the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            data = {
                'learner_id': ['L1', 'L2'],
                'median_interval': [1.5, 25.0],
                'feedback_group': ['Immediate', 'Delayed']
            }
            df = pd.DataFrame(data)
            
            save_binned_data(df, str(output_path))
            
            assert output_path.exists()
            
            # Verify contents
            loaded = pd.read_csv(output_path)
            assert len(loaded) == 2
            assert list(loaded.columns) == ['learner_id', 'median_interval', 'feedback_group']

    def test_save_binned_data_index_handling(self):
        """Verify that the index is not saved as a column."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            data = {
                'learner_id': ['L1'],
                'median_interval': [1.0],
                'feedback_group': ['Immediate']
            }
            df = pd.DataFrame(data)
            
            save_binned_data(df, str(output_path))
            
            loaded = pd.read_csv(output_path)
            # Check that 'Unnamed: 0' or similar index column is not present
            assert 'Unnamed: 0' not in loaded.columns
            assert 'index' not in loaded.columns

class TestLoadLearnerIntervals:
    """Test loading logic (mocked data scenario)."""

    def test_load_learner_intervals_schema(self):
        """Verify that the loader expects the correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            # Create a valid input file
            data = {
                'learner_id': ['L1', 'L2'],
                'median_interval': [1.5, 25.0]
            }
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            df = load_learner_intervals(str(input_path))
            assert df is not None
            assert 'learner_id' in df.columns
            assert 'median_interval' in df.columns
            assert len(df) == 2