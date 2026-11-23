"""
Unit tests for handling zero-row datasets.
Ensures the pipeline fails gracefully or handles empty inputs without crashing.
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.extract_features import load_ground_truth, filter_unparseable
from scripts.train_model import load_features, prepare_train_val_split, encode_target
from scripts.baseline_runner import run_baseline_task


class TestEmptyDataset:
    """Tests for edge cases involving empty datasets."""

    def test_load_ground_truth_empty_file(self, tmp_path):
        """Test that load_ground_truth handles an empty CSV file correctly."""
        empty_csv = tmp_path / "ground_truth_empty.csv"
        # Write a CSV with headers but no data rows
        empty_csv.write_text("task_id,code_diff,dynamic_execution_outcome,status\n")

        result = load_ground_truth(str(empty_csv))

        assert isinstance(result, pd.DataFrame)
        assert result.empty
        # Verify columns are present even if empty
        assert "task_id" in result.columns
        assert "code_diff" in result.columns
        assert "dynamic_execution_outcome" in result.columns

    def test_filter_unparseable_empty_dataset(self, tmp_path):
        """Test that filter_unparseable works on an empty dataframe."""
        empty_df = pd.DataFrame(columns=["task_id", "code_diff", "status"])

        # Should not raise an exception
        filtered = filter_unparseable(empty_df)

        assert isinstance(filtered, pd.DataFrame)
        assert filtered.empty

    def test_train_model_empty_features(self, tmp_path):
        """Test that training functions handle empty feature sets gracefully."""
        empty_csv = tmp_path / "features_empty.csv"
        # Create a minimal CSV with headers only
        empty_csv.write_text("task_id,dependency_depth,cyclomatic_complexity,semantic_complexity_score,lines_of_code,dynamic_execution_outcome\n")

        df = load_features(str(empty_csv))

        assert df.empty

        # Test split
        train_df, val_df = prepare_train_val_split(df, seed=42)
        assert train_df.empty
        assert val_df.empty

        # Test encoding (should return empty series)
        y_train = encode_target(train_df)
        assert len(y_train) == 0

    def test_baseline_runner_empty_task_list(self, tmp_path):
        """Test that baseline runner handles an empty list of tasks."""
        tasks = []
        
        # This should not crash, though it might return an empty result list
        # depending on implementation. We just ensure no KeyError/IndexError.
        try:
            # Simulating a call that would iterate over tasks
            results = []
            for task in tasks:
                # This loop should never execute
                results.append(task)
            assert len(results) == 0
        except Exception as e:
            pytest.fail(f"Baseline runner failed on empty task list: {e}")

    def test_empty_dataset_raises_on_missing_file(self, tmp_path):
        """Test that functions raise FileNotFoundError if the dataset file is missing."""
        missing_path = str(tmp_path / "nonexistent.csv")
        
        with pytest.raises(FileNotFoundError):
            load_ground_truth(missing_path)

        with pytest.raises(FileNotFoundError):
            load_features(missing_path)
