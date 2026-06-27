"""
Unit tests for metrics_joiner.py module.

Tests verify:
- Loading of clone metrics, perplexity scores, and bug detection results
- Joining logic and column preservation
- Validation of joined metrics
- Error handling for missing files
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects/PROJ-261-evaluating-the-impact-of-code-duplication/code"))

from metrics_joiner import (
    load_clone_metrics,
    load_perplexity_scores,
    load_bug_detection_results,
    join_metrics,
    validate_joined_metrics,
    save_joined_metrics,
)


class TestLoadCloneMetrics:
    """Tests for load_clone_metrics function."""

    def test_load_clone_metrics_success(self, tmp_path):
        """Test successful loading of clone metrics."""
        # Create test data
        test_data = {
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
            "file_path": ["file1.py", "file2.py", "file3.py"],
            "line_start": [10, 20, 30],
            "line_end": [50, 60, 70],
        }
        test_df = pd.DataFrame(test_data)
        test_path = tmp_path / "clone_metrics.csv"
        test_df.to_csv(test_path, index=False)

        # Load and verify
        loaded_df = load_clone_metrics(test_path)
        assert len(loaded_df) == 3
        assert "segment_id" in loaded_df.columns
        assert "clone_density" in loaded_df.columns

    def test_load_clone_metrics_file_not_found(self, tmp_path):
        """Test FileNotFoundError for missing file."""
        non_existent_path = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_clone_metrics(non_existent_path)


class TestLoadPerplexityScores:
    """Tests for load_perplexity_scores function."""

    def test_load_perplexity_scores_success(self, tmp_path):
        """Test successful loading of perplexity scores."""
        # Create test data
        test_data = {
            "segment_id": [1, 2, 3],
            "perplexity": [2.5, 3.2, 4.1],
            "token_count": [100, 200, 300],
            "model_id": ["codegen-350M-mono"] * 3,
        }
        test_df = pd.DataFrame(test_data)
        test_path = tmp_path / "perplexity_scores.csv"
        test_df.to_csv(test_path, index=False)

        # Load and verify
        loaded_df = load_perplexity_scores(test_path)
        assert len(loaded_df) == 3
        assert "segment_id" in loaded_df.columns
        assert "perplexity" in loaded_df.columns

    def test_load_perplexity_scores_file_not_found(self, tmp_path):
        """Test FileNotFoundError for missing file."""
        non_existent_path = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_perplexity_scores(non_existent_path)


class TestLoadBugDetectionResults:
    """Tests for load_bug_detection_results function."""

    def test_load_bug_detection_results_success(self, tmp_path):
        """Test successful loading of bug detection results."""
        # Create test data
        test_data = {
            "problem_id": [0, 1, 2],
            "pass_at_1": [0.8, 0.6, 0.9],
            "num_test_cases": [5, 4, 6],
            "solution_code": ["def func1(): pass", "def func2(): pass", "def func3(): pass"],
        }
        test_df = pd.DataFrame(test_data)
        test_path = tmp_path / "bug_detection_results.csv"
        test_df.to_csv(test_path, index=False)

        # Load and verify
        loaded_df = load_bug_detection_results(test_path)
        assert len(loaded_df) == 3
        assert "problem_id" in loaded_df.columns
        assert "pass_at_1" in loaded_df.columns

    def test_load_bug_detection_results_file_not_found(self, tmp_path):
        """Test FileNotFoundError for missing file."""
        non_existent_path = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_bug_detection_results(non_existent_path)


class TestJoinMetrics:
    """Tests for join_metrics function."""

    def test_join_metrics_basic(self):
        """Test basic joining of clone and perplexity metrics."""
        # Create test DataFrames
        clone_df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
        })
        perplexity_df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "perplexity": [2.5, 3.2, 4.1],
        })
        bug_df = pd.DataFrame({
            "problem_id": [0, 1, 2],
            "pass_at_1": [0.8, 0.6, 0.9],
        })

        # Join
        result = join_metrics(clone_df, perplexity_df, bug_df)

        # Verify
        assert len(result) == 3
        assert "segment_id" in result.columns
        assert "clone_density" in result.columns
        assert "perplexity" in result.columns
        assert "pass_at_1" in result.columns

    def test_join_metrics_inner_join(self):
        """Test that join uses inner join (only matching segment_ids)."""
        clone_df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
        })
        perplexity_df = pd.DataFrame({
            "segment_id": [2, 3, 4],  # segment 1 missing
            "perplexity": [3.2, 4.1, 5.0],
        })
        bug_df = pd.DataFrame({
            "problem_id": [0, 1, 2],
            "pass_at_1": [0.8, 0.6, 0.9],
        })

        result = join_metrics(clone_df, perplexity_df, bug_df)

        # Should only have segments 2 and 3 (inner join)
        assert len(result) == 2
        assert 1 not in result["segment_id"].values

    def test_join_metrics_empty_clone(self):
        """Test joining with empty clone metrics."""
        clone_df = pd.DataFrame(columns=["segment_id", "clone_density"])
        perplexity_df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "perplexity": [2.5, 3.2, 4.1],
        })
        bug_df = pd.DataFrame({
            "problem_id": [0, 1, 2],
            "pass_at_1": [0.8, 0.6, 0.9],
        })

        result = join_metrics(clone_df, perplexity_df, bug_df)

        # Should be empty after inner join
        assert len(result) == 0


class TestValidateJoinedMetrics:
    """Tests for validate_joined_metrics function."""

    def test_validate_success(self):
        """Test validation passes for valid metrics."""
        df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
            "perplexity": [2.5, 3.2, 4.1],
            "pass_at_1": [0.8, 0.6, 0.9],
        })

        assert validate_joined_metrics(df) is True

    def test_validate_missing_columns(self):
        """Test validation fails for missing required columns."""
        df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
            # Missing perplexity and pass_at_1
        })

        assert validate_joined_metrics(df) is False

    def test_validate_with_nan(self):
        """Test validation warns but passes with NaN values."""
        df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, np.nan, 0.8],
            "perplexity": [2.5, 3.2, 4.1],
            "pass_at_1": [0.8, 0.6, 0.9],
        })

        # Should pass validation (NaN is warned but not fatal)
        assert validate_joined_metrics(df) is True


class TestSaveJoinedMetrics:
    """Tests for save_joined_metrics function."""

    def test_save_joined_metrics_success(self, tmp_path):
        """Test successful saving of joined metrics."""
        df = pd.DataFrame({
            "segment_id": [1, 2, 3],
            "clone_density": [0.1, 0.5, 0.8],
            "perplexity": [2.5, 3.2, 4.1],
            "pass_at_1": [0.8, 0.6, 0.9],
        })
        output_path = tmp_path / "joined_metrics.csv"

        save_joined_metrics(df, output_path)

        # Verify file exists and can be loaded
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3
        assert "segment_id" in loaded_df.columns