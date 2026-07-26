"""
Unit tests for T031a: Baseline Score Extractor.
"""

import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from evaluation.baseline_score_extractor import (
    calculate_baseline_accuracy,
    save_baseline_score,
    extract_baseline_score
)


class TestCalculateBaselineAccuracy:
    """Tests for the calculate_baseline_accuracy function."""

    def test_calculate_mean_accuracy(self, tmp_path):
        """Test calculating mean accuracy from a valid CSV."""
        scores_file = tmp_path / "neural_scores.csv"
        scores = [0.8, 0.9, 0.7, 0.85]
        expected_mean = sum(scores) / len(scores)

        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match"])
            writer.writeheader()
            for i, score in enumerate(scores):
                writer.writerow({"task_id": f"task_{i}", "exact_match": score})

        result = calculate_baseline_accuracy(str(scores_file))
        assert abs(result - expected_mean) < 1e-6

    def test_missing_file_raises_error(self, tmp_path):
        """Test that FileNotFoundError is raised when file is missing."""
        with pytest.raises(FileNotFoundError):
            calculate_baseline_accuracy(str(tmp_path / "nonexistent.csv"))

    def test_missing_column_raises_error(self, tmp_path):
        """Test that ValueError is raised when score column is missing."""
        scores_file = tmp_path / "scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "other_score"])
            writer.writeheader()
            writer.writerow({"task_id": "t1", "other_score": 0.5})

        with pytest.raises(ValueError, match="Column 'exact_match' not found"):
            calculate_baseline_accuracy(str(scores_file))

    def test_invalid_score_raises_error(self, tmp_path):
        """Test that ValueError is raised for non-numeric scores."""
        scores_file = tmp_path / "scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match"])
            writer.writeheader()
            writer.writerow({"task_id": "t1", "exact_match": "invalid"})

        with pytest.raises(ValueError, match="Invalid score value"):
            calculate_baseline_accuracy(str(scores_file))

    def test_empty_file_raises_error(self, tmp_path):
        """Test that ValueError is raised if no valid scores are found."""
        scores_file = tmp_path / "scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match"])
            writer.writeheader()
            # No data rows

        with pytest.raises(ValueError, match="No valid scores found"):
            calculate_baseline_accuracy(str(scores_file))


class TestSaveBaselineScore:
    """Tests for the save_baseline_score function."""

    def test_save_creates_json(self, tmp_path):
        """Test that the function creates a valid JSON file."""
        output_file = tmp_path / "baseline.json"
        accuracy = 0.85
        metadata = {"source": "test_run"}

        save_baseline_score(accuracy, str(output_file), metadata)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["baseline_accuracy"] == accuracy
        assert data["metadata"] == metadata
        assert data["source"] == "neural_scores.csv"

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if missing."""
        output_file = tmp_path / "subdir" / "baseline.json"
        accuracy = 0.85

        save_baseline_score(accuracy, str(output_file))

        assert output_file.exists()


class TestExtractBaselineScore:
    """Tests for the main orchestration function."""

    def test_full_workflow(self, tmp_path):
        """Test the full workflow: calculate and save."""
        scores_file = tmp_path / "neural_scores.csv"
        output_file = tmp_path / "baseline.json"
        scores = [0.9, 0.95, 0.88]
        expected_mean = sum(scores) / len(scores)

        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match"])
            writer.writeheader()
            for i, score in enumerate(scores):
                writer.writerow({"task_id": f"t{i}", "exact_match": score})

        result = extract_baseline_score(
            scores_path=str(scores_file),
            output_path=str(output_file)
        )

        assert abs(result - expected_mean) < 1e-6
        assert output_file.exists()

        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data["baseline_accuracy"] == result