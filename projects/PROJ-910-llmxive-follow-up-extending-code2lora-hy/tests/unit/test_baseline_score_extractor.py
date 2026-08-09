"""
Unit tests for baseline_score_extractor module.

These tests verify that the baseline accuracy extraction logic works correctly.
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
    """Tests for calculate_baseline_accuracy function."""

    def test_calculate_accuracy_from_valid_csv(self, tmp_path):
        """Test calculating accuracy from a valid neural scores CSV."""
        # Create a mock neural scores CSV
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'exact_match': '0.8'})
            writer.writerow({'task_id': 'task2', 'exact_match': '0.6'})
            writer.writerow({'task_id': 'task3', 'exact_match': '0.9'})

        accuracy = calculate_baseline_accuracy(str(scores_file))

        # Expected: (0.8 + 0.6 + 0.9) / 3 = 0.7666...
        assert abs(accuracy - 0.7666666666666667) < 1e-9

    def test_calculate_accuracy_single_score(self, tmp_path):
        """Test with a single score entry."""
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'exact_match': '1.0'})

        accuracy = calculate_baseline_accuracy(str(scores_file))
        assert accuracy == 1.0

    def test_calculate_accuracy_all_zeros(self, tmp_path):
        """Test with all zero scores."""
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'exact_match': '0.0'})
            writer.writerow({'task_id': 'task2', 'exact_match': '0.0'})

        accuracy = calculate_baseline_accuracy(str(scores_file))
        assert accuracy == 0.0

    def test_calculate_accuracy_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            calculate_baseline_accuracy(str(non_existent))

    def test_calculate_accuracy_empty_file(self, tmp_path):
        """Test that ValueError is raised for empty file."""
        scores_file = tmp_path / "empty.csv"
        scores_file.write_text("task_id,exact_match\n")  # Header only, no data

        with pytest.raises(ValueError, match="No valid scores found"):
            calculate_baseline_accuracy(str(scores_file))

    def test_calculate_accuracy_missing_column(self, tmp_path):
        """Test that ValueError is raised for missing exact_match column."""
        scores_file = tmp_path / "wrong_format.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'score'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'score': '0.8'})

        with pytest.raises(ValueError, match="Expected 'exact_match' column"):
            calculate_baseline_accuracy(str(scores_file))

    def test_calculate_accuracy_invalid_score_value(self, tmp_path):
        """Test that ValueError is raised for invalid score values."""
        scores_file = tmp_path / "invalid_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'exact_match': 'not_a_number'})

        with pytest.raises(ValueError, match="Invalid score value"):
            calculate_baseline_accuracy(str(scores_file))


class TestSaveBaselineScore:
    """Tests for save_baseline_score function."""

    def test_save_creates_json_file(self, tmp_path):
        """Test that save_baseline_score creates a valid JSON file."""
        output_file = tmp_path / "baseline_score.json"
        result_path = save_baseline_score(0.75, str(output_file))

        assert result_path.exists()
        assert result_path.suffix == '.json'

        with open(result_file, 'r') as f:
            data = json.load(f)

        assert data['baseline_accuracy'] == 0.75
        assert data['source'] == 'neural_adapter_evaluation'
        assert 'description' in data

    def test_save_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        output_file = tmp_path / "nested" / "dir" / "baseline_score.json"
        result_path = save_baseline_score(0.5, str(output_file))

        assert result_path.exists()

    def test_save_default_path(self, tmp_path):
        """Test saving with default output path."""
        # Change to tmp_path to avoid writing to actual project directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result_path = save_baseline_score(0.8)
            assert result_path.name == "baseline_score.json"
            assert result_path.exists()
        finally:
            os.chdir(original_cwd)


class TestExtractBaselineScore:
    """Tests for extract_baseline_score function."""

    def test_extract_and_save(self, tmp_path):
        """Test the full extraction and save workflow."""
        # Create mock neural scores
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task_id', 'exact_match'])
            writer.writeheader()
            writer.writerow({'task_id': 'task1', 'exact_match': '0.9'})
            writer.writerow({'task_id': 'task2', 'exact_match': '0.7'})

        output_file = tmp_path / "baseline_score.json"

        accuracy = extract_baseline_score(
            neural_scores_path=str(scores_file),
            output_path=str(output_file)
        )

        # Verify accuracy calculation
        assert abs(accuracy - 0.8) < 1e-9

        # Verify JSON file was created
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data['baseline_accuracy'] == 0.8

    def test_extract_missing_input_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            extract_baseline_score(
                neural_scores_path=str(tmp_path / "nonexistent.csv"),
                output_path=str(tmp_path / "output.json")
            )