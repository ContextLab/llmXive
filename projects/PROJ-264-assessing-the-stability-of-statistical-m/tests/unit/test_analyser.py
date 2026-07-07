"""
Unit tests for the analyser module.
"""
import math
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from code.analyser import (
    calculate_cv,
    aggregate_metrics,
    load_raw_evaluations,
    run_aggregation
)

class TestCalculateCV:
    """Tests for the calculate_cv function."""

    def test_normal_case(self):
        """Test CV calculation with normal values."""
        mean = 10.0
        std = 2.0
        expected = 0.2
        result = calculate_cv(mean, std)
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_zero_mean(self):
        """Test CV calculation when mean is zero (should return 0.0)."""
        mean = 0.0
        std = 2.0
        result = calculate_cv(mean, std)
        assert result == 0.0

    def test_negative_mean(self):
        """Test CV calculation with negative mean (uses absolute value)."""
        mean = -10.0
        std = 2.0
        expected = 0.2
        result = calculate_cv(mean, std)
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_zero_std(self):
        """Test CV calculation when std is zero (perfect stability)."""
        mean = 10.0
        std = 0.0
        result = calculate_cv(mean, std)
        assert result == 0.0

class TestAggregateMetrics:
    """Tests for the aggregate_metrics function."""

    def test_empty_dataframe(self):
        """Test aggregation with empty DataFrame."""
        df = pd.DataFrame(columns=["dataset_id", "model_name", "fold_id", "repeat_id", "accuracy", "f1_score"])
        result = aggregate_metrics(df)
        assert result.empty
        assert list(result.columns) == ["dataset_id", "model_name", "mean_accuracy", "cv_accuracy", 
                                       "mean_f1", "cv_f1", "n_folds", "n_repeats"]

    def test_single_group(self):
        """Test aggregation with a single (dataset, model) group."""
        df = pd.DataFrame({
            "dataset_id": [1, 1, 1],
            "model_name": ["LR", "LR", "LR"],
            "fold_id": [1, 2, 3],
            "repeat_id": [1, 1, 1],
            "accuracy": [0.8, 0.9, 0.7],
            "f1_score": [0.8, 0.9, 0.7]
        })
        
        result = aggregate_metrics(df)
        
        assert len(result) == 1
        assert result["dataset_id"].iloc[0] == 1
        assert result["model_name"].iloc[0] == "LR"
        assert math.isclose(result["mean_accuracy"].iloc[0], 0.8, rel_tol=1e-10)
        assert math.isclose(result["mean_f1"].iloc[0], 0.8, rel_tol=1e-10)
        assert result["n_folds"].iloc[0] == 3
        assert result["n_repeats"].iloc[0] == 1

    def test_multiple_groups(self):
        """Test aggregation with multiple (dataset, model) groups."""
        df = pd.DataFrame({
            "dataset_id": [1, 1, 2, 2],
            "model_name": ["LR", "RF", "LR", "RF"],
            "fold_id": [1, 1, 1, 1],
            "repeat_id": [1, 1, 1, 1],
            "accuracy": [0.8, 0.85, 0.75, 0.8],
            "f1_score": [0.8, 0.85, 0.75, 0.8]
        })
        
        result = aggregate_metrics(df)
        
        assert len(result) == 4
        assert set(result["dataset_id"]) == {1, 2}
        assert set(result["model_name"]) == {"LR", "RF"}

    def test_zero_variance_handling(self):
        """Test that zero variance results in CV of 0.0."""
        df = pd.DataFrame({
            "dataset_id": [1, 1, 1],
            "model_name": ["LR", "LR", "LR"],
            "fold_id": [1, 2, 3],
            "repeat_id": [1, 1, 1],
            "accuracy": [0.9, 0.9, 0.9],  # Zero variance
            "f1_score": [0.9, 0.9, 0.9]
        })
        
        result = aggregate_metrics(df)
        
        assert result["cv_accuracy"].iloc[0] == 0.0
        assert result["cv_f1"].iloc[0] == 0.0

    def test_column_order(self):
        """Test that output columns are in the correct order."""
        df = pd.DataFrame({
            "dataset_id": [1],
            "model_name": ["LR"],
            "fold_id": [1],
            "repeat_id": [1],
            "accuracy": [0.8],
            "f1_score": [0.8]
        })
        
        result = aggregate_metrics(df)
        
        expected_columns = ["dataset_id", "model_name", "mean_accuracy", "cv_accuracy", 
                          "mean_f1", "cv_f1", "n_folds", "n_repeats"]
        assert list(result.columns) == expected_columns

class TestLoadRawEvaluations:
    """Tests for the load_raw_evaluations function."""

    def test_load_valid_file(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("dataset_id,model_name,fold_id,repeat_id,accuracy,f1_score\n")
            f.write("1,LR,1,1,0.8,0.8\n")
            temp_path = f.name
        
        try:
            df = load_raw_evaluations(temp_path)
            assert len(df) == 1
            assert df["dataset_id"].iloc[0] == 1
        finally:
            Path(temp_path).unlink()

    def test_missing_columns(self):
        """Test that missing columns raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("dataset_id,model_name,fold_id\n")
            f.write("1,LR,1\n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                load_raw_evaluations(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_raw_evaluations("non_existent_file.csv")

class TestRunAggregation:
    """Tests for the run_aggregation function."""

    def test_full_pipeline(self):
        """Test the full aggregation pipeline with file I/O."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "raw_evaluations.csv"
            output_path = Path(tmpdir) / "stability_metrics.csv"
            
            # Create input file
            df_input = pd.DataFrame({
                "dataset_id": [1, 1, 1],
                "model_name": ["LR", "LR", "LR"],
                "fold_id": [1, 2, 3],
                "repeat_id": [1, 1, 1],
                "accuracy": [0.8, 0.9, 0.7],
                "f1_score": [0.8, 0.9, 0.7]
            })
            df_input.to_csv(input_path, index=False)
            
            # Run aggregation
            result = run_aggregation(str(input_path), str(output_path))
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify result
            assert len(result) == 1
            assert math.isclose(result["mean_accuracy"].iloc[0], 0.8, rel_tol=1e-10)
            
            # Verify output file content
            df_output = pd.read_csv(output_path)
            assert len(df_output) == 1
            assert list(df_output.columns) == ["dataset_id", "model_name", "mean_accuracy", "cv_accuracy", 
                                              "mean_f1", "cv_f1", "n_folds", "n_repeats"]