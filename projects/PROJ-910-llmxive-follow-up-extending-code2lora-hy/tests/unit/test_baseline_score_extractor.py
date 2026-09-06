"""
Unit tests for the baseline_score_extractor module.

These tests verify that:
1. `calculate_baseline_accuracy` correctly computes the mean from a CSV.
2. `save_baseline_score` writes the correct JSON structure.
3. `extract_baseline_score` orchestrates the process correctly.
4. The output file `baseline_score.json` contains exactly `{"score": <float>}`.
"""

import json
import csv
import os
import tempfile
import pytest
from pathlib import Path

from evaluation.baseline_score_extractor import (
    calculate_baseline_accuracy,
    save_baseline_score,
    extract_baseline_score,
)


class TestCalculateBaselineAccuracy:
    def test_valid_csv(self, tmp_path):
        """Test calculation with a valid CSV containing multiple scores."""
        csv_path = tmp_path / "neural_scores.csv"
        data = [
            {"task_id": "1", "exact_match": "0.8", "latency_ms": "100"},
            {"task_id": "2", "exact_match": "0.9", "latency_ms": "120"},
            {"task_id": "3", "exact_match": "0.7", "latency_ms": "110"},
        ]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        result = calculate_baseline_accuracy(csv_path)
        expected = (0.8 + 0.9 + 0.7) / 3.0
        assert abs(result - expected) < 1e-6

    def test_empty_csv_raises(self, tmp_path):
        """Test that an empty CSV (header only) raises ValueError."""
        csv_path = tmp_path / "neural_scores.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "exact_match"])
            writer.writeheader()

        with pytest.raises(ValueError, match="No valid.*scores found"):
            calculate_baseline_accuracy(csv_path)

    def test_missing_column_raises(self, tmp_path):
        """Test that a CSV missing 'exact_match' raises ValueError."""
        csv_path = tmp_path / "neural_scores.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "latency_ms"])
            writer.writeheader()
            writer.writerow({"task_id": "1", "latency_ms": "100"})

        with pytest.raises(ValueError, match="must contain.*exact_match"):
            calculate_baseline_accuracy(csv_path)

    def test_file_not_found_raises(self, tmp_path):
        """Test that a missing file raises FileNotFoundError."""
        csv_path = tmp_path / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            calculate_baseline_accuracy(csv_path)


class TestSaveBaselineScore:
    def test_save_correct_structure(self, tmp_path):
        """Test that the saved JSON has the correct structure."""
        output_path = tmp_path / "baseline_score.json"
        score = 0.85

        result_path = save_baseline_score(score, output_path)

        assert result_path == output_path
        assert output_path.exists()

        with open(output_path, "r") as f:
            data = json.load(f)

        assert "score" in data
        assert isinstance(data["score"], float)
        assert abs(data["score"] - score) < 1e-6

    def test_creates_directories(self, tmp_path):
        """Test that save_baseline_score creates parent directories."""
        output_path = tmp_path / "subdir" / "baseline_score.json"
        save_baseline_score(0.5, output_path)
        assert output_path.exists()


class TestExtractBaselineScore:
    def test_full_pipeline(self, tmp_path):
        """Test the full extraction and saving pipeline."""
        csv_path = tmp_path / "neural_scores.csv"
        output_path = tmp_path / "baseline_score.json"

        # Create mock data
        data = [
            {"task_id": "1", "exact_match": "0.8", "latency_ms": "100"},
            {"task_id": "2", "exact_match": "0.8", "latency_ms": "120"},
        ]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        score = extract_baseline_score(csv_path, output_path)

        # Verify score
        assert abs(score - 0.8) < 1e-6

        # Verify file content
        with open(output_path, "r") as f:
            data = json.load(f)
        assert data == {"score": 0.8}