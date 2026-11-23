"""
Unit tests for T033: Sensitivity Summary Generator.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from evaluation.sensitivity_summary_generator import (
    load_sensitivity_results,
    generate_summary_csv,
    save_summary_csv,
    run_summary_generation
)
from evaluation.sensitivity_minimal_set import load_baseline_score, calculate_dynamic_threshold


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_sensitivity_results_dict_format(temp_dir):
    """Test loading results from dict format."""
    data = {
        "results": [
            {"feature_set": "full", "accuracy": 0.85},
            {"feature_set": "tokens_only", "accuracy": 0.70}
        ]
    }
    filepath = temp_dir / "results.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    results = load_sensitivity_results(filepath)
    assert len(results) == 2
    assert results[0]["feature_set"] == "full"


def test_load_sensitivity_results_list_format(temp_dir):
    """Test loading results from list format."""
    data = [
        {"feature_set": "full", "accuracy": 0.85},
        {"feature_set": "tokens_only", "accuracy": 0.70}
    ]
    filepath = temp_dir / "results.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    results = load_sensitivity_results(filepath)
    assert len(results) == 2


def test_load_sensitivity_results_missing_file(temp_dir):
    """Test error when file is missing."""
    filepath = temp_dir / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        load_sensitivity_results(filepath)


def test_generate_summary_csv():
    """Test summary generation with threshold logic."""
    results = [
        {"feature_set": "full", "accuracy": 0.90},
        {"feature_set": "partial", "accuracy": 0.75},
        {"feature_set": "minimal", "accuracy": 0.60}
    ]
    threshold = 0.80
    
    summary = generate_summary_csv(results, threshold)
    
    assert len(summary) == 3
    assert summary[0]["feature_set"] == "full"
    assert summary[0]["meets_threshold"] is True
    assert summary[1]["feature_set"] == "partial"
    assert summary[1]["meets_threshold"] is False
    assert summary[2]["meets_threshold"] is False


def test_save_summary_csv(temp_dir):
    """Test saving summary to CSV."""
    rows = [
        {"feature_set": "full", "accuracy": 0.90, "meets_threshold": True},
        {"feature_set": "partial", "accuracy": 0.75, "meets_threshold": False}
    ]
    filepath = temp_dir / "summary.csv"
    
    save_summary_csv(rows, filepath)
    
    assert filepath.exists()
    assert filepath.stat().st_size > 0
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows_read = list(reader)
    
    assert len(rows_read) == 2
    assert reader.fieldnames == ["feature_set", "accuracy", "meets_threshold"]


def test_end_to_end_generation(temp_dir):
    """Test full pipeline from JSON to CSV."""
    # Prepare input files
    sens_data = {
        "results": [
            {"feature_set": "all", "accuracy": 0.88},
            {"feature_set": "cyclomatic", "accuracy": 0.82},
            {"feature_set": "depth", "accuracy": 0.65}
        ]
    }
    sens_file = temp_dir / "sensitivity_results.json"
    with open(sens_file, 'w') as f:
        json.dump(sens_data, f)
    
    baseline_data = {"baseline_accuracy": 0.90}
    base_file = temp_dir / "baseline_score.json"
    with open(base_file, 'w') as f:
        json.dump(baseline_data, f)
    
    output_file = temp_dir / "summary.csv"
    
    # Run generation
    run_summary_generation(
        sensitivity_results_path=sens_file,
        baseline_score_path=base_file,
        output_path=output_file
    )
    
    # Verify output
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    # Threshold is 80% of 0.90 = 0.72
    assert rows[0]["meets_threshold"] == "True"  # 0.88 >= 0.72
    assert rows[1]["meets_threshold"] == "True"  # 0.82 >= 0.72
    assert rows[2]["meets_threshold"] == "False" # 0.65 < 0.72