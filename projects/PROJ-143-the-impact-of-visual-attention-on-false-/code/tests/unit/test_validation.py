"""
Unit tests for validation logic (T005).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.validation import (
    load_verification_results,
    calculate_failure_rate,
    calculate_inconclusive_flag,
    generate_validation_status,
    run_validation_workflow
)


@pytest.fixture
def sample_results():
    """Sample human verification results data."""
    return [
        {"id": "img_001", "verified": True, "confidence": 0.95},
        {"id": "img_002", "verified": False, "confidence": 0.45},
        {"id": "img_003", "verified": True, "confidence": 0.88},
        {"id": "img_004", "verified": False, "confidence": 0.32},
        {"id": "img_005", "verified": True, "confidence": 0.91},
    ]


@pytest.fixture
def temp_input_file(sample_results):
    """Create a temporary input file with sample results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_results, f)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


def test_load_verification_results_from_list(temp_input_file):
    """Test loading results from a list format."""
    results = load_verification_results(temp_input_file)
    assert isinstance(results, list)
    assert len(results) == 5
    assert results[0]['id'] == 'img_001'


def test_load_verification_results_from_dict():
    """Test loading results from a dict with 'results' key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"results": [{"id": "test", "verified": True}]}, f)
        temp_path = Path(f.name)
    
    try:
        results = load_verification_results(temp_path)
        assert isinstance(results, list)
        assert len(results) == 1
    finally:
        temp_path.unlink()


def test_load_verification_results_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_verification_results(Path("/nonexistent/path/file.json"))


def test_calculate_failure_rate():
    """Test failure rate calculation."""
    # 2 failures out of 5 = 0.4
    results = [
        {"verified": True},
        {"verified": False},
        {"verified": True},
        {"verified": False},
        {"verified": True},
    ]
    rate = calculate_failure_rate(results)
    assert rate == 0.4


def test_calculate_failure_rate_empty():
    """Test failure rate with empty list."""
    rate = calculate_failure_rate([])
    assert rate == 0.0


def test_calculate_failure_rate_all_fail():
    """Test failure rate when all items fail."""
    results = [{"verified": False} for _ in range(10)]
    rate = calculate_failure_rate(results)
    assert rate == 1.0


def test_calculate_inconclusive_flag_above_threshold():
    """Test inconclusive flag when failure rate > 10%."""
    assert calculate_inconclusive_flag(0.15) is True
    assert calculate_inconclusive_flag(0.20) is True
    assert calculate_inconclusive_flag(0.11) is True


def test_calculate_inconclusive_flag_at_threshold():
    """Test inconclusive flag when failure rate = 10%."""
    # Should be False (not > 10%)
    assert calculate_inconclusive_flag(0.10) is False


def test_calculate_inconclusive_flag_below_threshold():
    """Test inconclusive flag when failure rate < 10%."""
    assert calculate_inconclusive_flag(0.05) is False
    assert calculate_inconclusive_flag(0.00) is False


def test_generate_validation_status():
    """Test validation status generation."""
    status = generate_validation_status(
        failure_rate=0.25,
        inconclusive=True,
        total_items=100,
        failed_items=25
    )
    
    assert status["status"]["inconclusive"] is True
    assert status["metrics"]["failure_rate"] == 0.25
    assert status["metrics"]["total_items"] == 100
    assert "inconclusive" in status["status"]["reason"]


def test_run_validation_workflow(temp_input_file):
    """Test end-to-end validation workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "validation_status.json"
        
        status = run_validation_workflow(
            input_path=temp_input_file,
            output_path=output_path,
            threshold=0.10
        )
        
        # Check output file exists
        assert output_path.exists()
        
        # Check status content
        assert "validation_timestamp" in status
        assert "metrics" in status
        assert "status" in status
        
        # 2 failures out of 5 = 40% > 10%, so should be inconclusive
        assert status["status"]["inconclusive"] is True
        assert status["metrics"]["failure_rate"] == 0.4


def test_run_validation_workflow_below_threshold():
    """Test workflow when failure rate is below threshold."""
    # Create low failure rate data (1 failure out of 20 = 5%)
    low_failure_results = [{"verified": True} for _ in range(19)] + [{"verified": False}]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(low_failure_results, f)
        input_path = Path(f.name)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_status.json"
            
            status = run_validation_workflow(
                input_path=input_path,
                output_path=output_path,
                threshold=0.10
            )
            
            assert status["status"]["inconclusive"] is False
            assert status["metrics"]["failure_rate"] == 0.05
    finally:
        input_path.unlink()