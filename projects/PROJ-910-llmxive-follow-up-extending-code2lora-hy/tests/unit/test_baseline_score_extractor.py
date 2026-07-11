"""
Unit tests for baseline_score_extractor module (T031a).

Tests the extraction of baseline accuracy scores from neural evaluation results.
"""
import json
import csv
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
    
    def test_calculate_accuracy_single_task(self, tmp_path):
        """Test accuracy calculation with a single task."""
        scores_file = tmp_path / "neural_scores.csv"
        
        # Write a single score
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '1.0'])
        
        accuracy = calculate_baseline_accuracy(scores_file)
        assert accuracy == 1.0
    
    def test_calculate_accuracy_multiple_tasks(self, tmp_path):
        """Test accuracy calculation with multiple tasks."""
        scores_file = tmp_path / "neural_scores.csv"
        
        # Write multiple scores
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '1.0'])
            writer.writerow(['task_2', '0.5'])
            writer.writerow(['task_3', '0.0'])
        
        accuracy = calculate_baseline_accuracy(scores_file)
        assert accuracy == pytest.approx(0.5, rel=1e-6)
    
    def test_calculate_accuracy_all_zero(self, tmp_path):
        """Test accuracy calculation when all scores are zero."""
        scores_file = tmp_path / "neural_scores.csv"
        
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '0.0'])
            writer.writerow(['task_2', '0.0'])
        
        accuracy = calculate_baseline_accuracy(scores_file)
        assert accuracy == 0.0
    
    def test_calculate_accuracy_all_full(self, tmp_path):
        """Test accuracy calculation when all scores are perfect."""
        scores_file = tmp_path / "neural_scores.csv"
        
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '1.0'])
            writer.writerow(['task_2', '1.0'])
            writer.writerow(['task_3', '1.0'])
        
        accuracy = calculate_baseline_accuracy(scores_file)
        assert accuracy == 1.0
    
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        non_existent = tmp_path / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            calculate_baseline_accuracy(non_existent)
    
    def test_empty_file_raises_error(self, tmp_path):
        """Test that ValueError is raised for empty file."""
        scores_file = tmp_path / "empty_scores.csv"
        
        # Write only header
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
        
        with pytest.raises(ValueError, match="Neural scores file is empty"):
            calculate_baseline_accuracy(scores_file)

class TestSaveBaselineScore:
    """Tests for save_baseline_score function."""
    
    def test_save_creates_file(self, tmp_path):
        """Test that the function creates the output file."""
        output_file = tmp_path / "baseline_score.json"
        accuracy = 0.85
        
        save_baseline_score(accuracy, output_file)
        
        assert output_file.exists()
    
    def test_save_correct_format(self, tmp_path):
        """Test that the saved file has correct JSON structure."""
        output_file = tmp_path / "baseline_score.json"
        accuracy = 0.75
        
        save_baseline_score(accuracy, output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["accuracy"] == accuracy
        assert data["source"] == "neural_evaluation"
        assert data["metric"] == "exact_match"
        assert "description" in data
    
    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        output_file = tmp_path / "subdir" / "nested" / "baseline_score.json"
        accuracy = 0.90
        
        save_baseline_score(accuracy, output_file)
        
        assert output_file.exists()

class TestExtractBaselineScore:
    """Tests for the main extract_baseline_score function."""
    
    def test_full_extraction(self, tmp_path):
        """Test complete extraction workflow."""
        # Create input scores file
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '1.0'])
            writer.writerow(['task_2', '0.5'])
        
        output_file = tmp_path / "baseline_score.json"
        
        result = extract_baseline_score(
            neural_scores_path=scores_file,
            output_path=output_file
        )
        
        assert result["accuracy"] == pytest.approx(0.75, rel=1e-6)
        assert result["output_path"] == str(output_file)
        assert result["source_path"] == str(scores_file)
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data["accuracy"] == pytest.approx(0.75, rel=1e-6)
    
    def test_creates_output_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        scores_file = tmp_path / "neural_scores.csv"
        with open(scores_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'exact_match'])
            writer.writerow(['task_1', '1.0'])
        
        output_file = tmp_path / "results" / "baseline_score.json"
        
        result = extract_baseline_score(
            neural_scores_path=scores_file,
            output_path=output_file
        )
        
        assert output_file.exists()
        assert result["accuracy"] == 1.0
