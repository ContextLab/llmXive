import json
import os
import tempfile
import pytest
from dataclasses import dataclass

from experiment_time_validator import (
    BudgetResult,
    load_profiling_report,
    calculate_experiment_budget,
    save_validation_report
)

@pytest.fixture
def temp_profiling_report():
    """Create a temporary profiling report for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "mean_step_time_ms": 5000.0,  # 5 seconds per step
            "p95_step_time_ms": 8000.0
        }, f)
        return f.name

@pytest.fixture
def cleanup_temp_files():
    """Cleanup temporary files after test."""
    yield
    # Clean up any temp files created during test
    for f in [temp_profiling_report] if 'temp_profiling_report' in locals() else []:
        try:
            if os.path.exists(f):
                os.unlink(f)
        except:
            pass

def test_load_profiling_report_success(temp_profiling_report):
    """Test successful loading of profiling report."""
    report = load_profiling_report(temp_profiling_report)
    assert "mean_step_time_ms" in report
    assert report["mean_step_time_ms"] == 5000.0

def test_load_profiling_report_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_profiling_report("nonexistent_file.json")

def test_calculate_experiment_budget_basic(temp_profiling_report):
    """Test basic budget calculation."""
    report = load_profiling_report(temp_profiling_report)
    result = calculate_experiment_budget(report, trial_count=50)
    
    # 50 trials * 100 steps * 5000ms = 25,000,000ms = 6.94 hours
    assert result.mean_step_time_ms == 5000.0
    assert result.total_steps == 5000  # 50 * 100
    assert result.estimated_total_time_ms == 25000000.0
    assert result.ci_limit_hours == 6.0
    assert not result.passes_budget  # 6.94 > 6.0
    assert result.status == "FAIL"

def test_calculate_experiment_budget_passes(temp_profiling_report):
    """Test budget calculation when it passes."""
    report = load_profiling_report(temp_profiling_report)
    # Use a faster step time: 1000ms
    report["mean_step_time_ms"] = 1000.0
    
    result = calculate_experiment_budget(report, trial_count=50)
    
    # 50 * 100 * 1000ms = 5,000,000ms = 1.39 hours
    assert result.estimated_total_time_hours < 6.0
    assert result.passes_budget
    assert result.status in ["PASS", "WARNING"]

def test_calculate_experiment_budget_missing_field(temp_profiling_report):
    """Test error handling for missing required field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"other_field": 123}, f)
        bad_file = f.name
    
    try:
        report = load_profiling_report(bad_file)
        with pytest.raises(ValueError):
            calculate_experiment_budget(report, trial_count=50)
    finally:
        if os.path.exists(bad_file):
            os.unlink(bad_file)

def test_save_validation_report(temp_profiling_report):
    """Test saving validation report to file."""
    report = load_profiling_report(temp_profiling_report)
    result = calculate_experiment_budget(report, trial_count=50)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        save_validation_report(result, output_path)
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["status"] == result.status
        assert saved_data["passes_budget"] == result.passes_budget
        assert "validation_message" in saved_data
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_budget_result_dataclass():
    """Test BudgetResult dataclass initialization."""
    result = BudgetResult(
        mean_step_time_ms=1000.0,
        total_steps=1000,
        estimated_total_time_ms=1000000.0,
        estimated_total_time_hours=0.28,
        ci_limit_hours=6.0,
        passes_budget=True,
        margin_hours=5.72,
        status="PASS"
    )
    
    assert result.mean_step_time_ms == 1000.0
    assert result.passes_budget is True
    assert result.status == "PASS"
