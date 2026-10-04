"""
Unit tests for acceptance_checker.py
"""
import os
import sys
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validate.acceptance_checker import AcceptanceChecker

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        results_dir = tmpdir / "results"
        derived_dir = tmpdir / "derived"
        raw_dir = tmpdir / "raw"
        
        results_dir.mkdir()
        derived_dir.mkdir()
        raw_dir.mkdir()
        
        yield {
            "results": results_dir,
            "derived": derived_dir,
            "raw": raw_dir
        }

@patch('validate.acceptance_checker.Config')
def test_check_file_exists_pass(mock_config, temp_dirs):
    """Test that check_file_exists returns True for existing file."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    test_file = temp_dirs["results"] / "test.txt"
    test_file.write_text("test content")
    
    result = checker.check_file_exists(test_file, "Test File")
    assert result is True
    assert any("PASS" in detail for detail in checker.checklist["US-1"]["details"])

@patch('validate.acceptance_checker.Config')
def test_check_file_exists_fail(mock_config, temp_dirs):
    """Test that check_file_exists returns False for missing file."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    missing_file = temp_dirs["results"] / "missing.txt"
    
    result = checker.check_file_exists(missing_file, "Missing File")
    assert result is False
    assert any("FAIL" in detail for detail in checker.checklist["US-1"]["details"])

@patch('validate.acceptance_checker.Config')
def test_verify_us1_solver_execution_pass(mock_config, temp_dirs):
    """Test US-1 verification with valid solver outputs."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    # Create valid predictions
    predictions_file = temp_dirs["derived"] / "predictions.jsonl"
    with open(predictions_file, 'w') as f:
        f.write(json.dumps({"scene_id": "1", "prediction": 5, "status": "Success"}) + "\n")
        f.write(json.dumps({"scene_id": "2", "prediction": 3, "status": "Ambiguous"}) + "\n")
    
    # Create valid latency log
    latency_file = temp_dirs["derived"] / "latency_log.jsonl"
    with open(latency_file, 'w') as f:
        f.write(json.dumps({"scene_id": "1", "latency_ms": 100.5, "status": "Success"}) + "\n")
    
    # Create valid solver failures
    failures_file = temp_dirs["derived"] / "solver_failures.json"
    with open(failures_file, 'w') as f:
        json.dump([], f)
    
    checker = AcceptanceChecker()
    result = checker.verify_us1_solver_execution()
    
    assert result is True
    assert checker.checklist["US-1"]["status"] == "PASS"

@patch('validate.acceptance_checker.Config')
def test_verify_us1_solver_execution_fail_missing_files(mock_config, temp_dirs):
    """Test US-1 verification with missing files."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    result = checker.verify_us1_solver_execution()
    
    assert result is False
    assert checker.checklist["US-1"]["status"] == "FAIL"

@patch('validate.acceptance_checker.Config')
def test_verify_us2_benchmark_metrics_pass(mock_config, temp_dirs):
    """Test US-2 verification with valid benchmark results."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    # Create valid benchmark results
    results_file = temp_dirs["results"] / "benchmark_results.csv"
    with open(results_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "symbolic_pred", "vlm_pred", "ground_truth", "exact_match", "f1", "latency_ms"])
        writer.writeheader()
        writer.writerow({"scene_id": "1", "symbolic_pred": 5, "vlm_pred": 5, "ground_truth": 5, "exact_match": "true", "f1": 1.0, "latency_ms": 100.0})
        writer.writerow({"scene_id": "2", "symbolic_pred": 3, "vlm_pred": 3, "ground_truth": 3, "exact_match": "true", "f1": 1.0, "latency_ms": 120.0})
    
    # Create valid sensitivity analysis
    sensitivity_file = temp_dirs["results"] / "sensitivity_analysis.csv"
    with open(sensitivity_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=["threshold", "success_rate", "false_positive_rate"])
        writer.writeheader()
        writer.writerow({"threshold": 0.50, "success_rate": 0.95, "false_positive_rate": 0.05})
    
    checker = AcceptanceChecker()
    result = checker.verify_us2_benchmark_metrics()
    
    assert result is True
    assert checker.checklist["US-2"]["status"] == "PASS"
    assert checker.symbolic_exact_match == 1.0

@patch('validate.acceptance_checker.Config')
def test_verify_us2_benchmark_metrics_fail_missing(mock_config, temp_dirs):
    """Test US-2 verification with missing files."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    result = checker.verify_us2_benchmark_metrics()
    
    assert result is False
    assert checker.checklist["US-2"]["status"] == "FAIL"

@patch('validate.acceptance_checker.Config')
def test_verify_us3_failure_analysis_pass(mock_config, temp_dirs):
    """Test US-3 verification with valid failure analysis."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    # Create valid failure classification
    classification_file = temp_dirs["derived"] / "failure_classification.json"
    with open(classification_file, 'w') as f:
        json.dump([
            {"scene_id": "1", "classification": "Geometric Ambiguity", "reason": "..." , "semantic_gap_proportion": 0.5},
            {"scene_id": "2", "classification": "Semantic Gap", "reason": "..."}
        ], f)
    
    # Create valid failure analysis report
    report_file = temp_dirs["results"] / "failure_analysis_report.md"
    with open(report_file, 'w') as f:
        f.write("# Failure Analysis\n\n## Geometric Ambiguity\n\n## Semantic Gap\n")
    
    checker = AcceptanceChecker()
    result = checker.verify_us3_failure_analysis()
    
    assert result is True
    assert checker.checklist["US-3"]["status"] == "PASS"

@patch('validate.acceptance_checker.Config')
def test_verify_sc005_exact_match_threshold_pass(mock_config, temp_dirs):
    """Test SC-005 verification with passing threshold."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    # Create benchmark results with high exact match
    results_file = temp_dirs["results"] / "benchmark_results.csv"
    with open(results_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "symbolic_pred", "vlm_pred", "ground_truth", "exact_match", "f1", "latency_ms"])
        writer.writeheader()
        # 90% exact match, VLM 100%
        for i in range(10):
            exact = "true" if i < 9 else "false"
            writer.writerow({"scene_id": str(i), "symbolic_pred": 5, "vlm_pred": 5, "ground_truth": 5, "exact_match": exact, "f1": 1.0, "latency_ms": 100.0})
    
    checker = AcceptanceChecker()
    # Manually set metrics to simulate calculation
    checker.symbolic_exact_match = 0.90
    checker.vlm_baseline_accuracy = 1.0
    
    result = checker.verify_sc005_exact_match_threshold()
    
    assert result is True
    assert checker.checklist["SC-005"]["status"] == "PASS"
    assert abs(checker.checklist["SC-005"]["metric_value"] - 0.90) < 0.001

@patch('validate.acceptance_checker.Config')
def test_verify_sc005_exact_match_threshold_fail(mock_config, temp_dirs):
    """Test SC-005 verification with failing threshold."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    # Manually set metrics to simulate calculation
    checker.symbolic_exact_match = 0.70
    checker.vlm_baseline_accuracy = 1.0
    
    result = checker.verify_sc005_exact_match_threshold()
    
    assert result is False
    assert checker.checklist["SC-005"]["status"] == "FAIL"

@patch('validate.acceptance_checker.Config')
def test_generate_checklist_md(mock_config, temp_dirs):
    """Test that generate_checklist_md creates a valid markdown file."""
    mock_config.DATA_RESULTS = str(temp_dirs["results"])
    mock_config.DATA_DERIVED = str(temp_dirs["derived"])
    mock_config.DATA_RAW = str(temp_dirs["raw"])
    
    checker = AcceptanceChecker()
    # Simulate some checks
    checker.checklist["US-1"]["status"] = "PASS"
    checker.checklist["US-1"]["details"] = ["PASS: File exists"]
    checker.checklist["US-2"]["status"] = "FAIL"
    checker.checklist["US-2"]["details"] = ["FAIL: Missing file"]
    checker.checklist["US-3"]["status"] = "PASS"
    checker.checklist["US-3"]["details"] = ["PASS: Valid"]
    checker.checklist["SC-005"]["status"] = "PASS"
    checker.checklist["SC-005"]["details"] = ["PASS: Threshold met"]
    checker.checklist["SC-005"]["metric_value"] = 0.90
    
    output_path = temp_dirs["results"] / "acceptance_checklist.md"
    checker.generate_checklist_md(output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "US-1" in content
    assert "US-2" in content
    assert "US-3" in content
    assert "SC-005" in content
    assert "✅" in content
    assert "❌" in content
    assert "0.9000" in content