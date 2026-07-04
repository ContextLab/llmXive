"""
Unit tests for power_analysis.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result
)
from code.src.config import set_rng_seed

@pytest.fixture
def temp_audit_json():
    """Creates a temporary audit_report.json with mock data."""
    mock_data = [
        {"id": 1, "consistent": True},
        {"id": 2, "consistent": False},
        {"id": 3, "consistent": True},
        {"id": 4, "consistent": True},
        {"id": 5, "consistent": False}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_data, f)
        return f.name

@pytest.fixture
def temp_audit_json_large():
    """Creates a temporary audit_report.json with > 300 records."""
    mock_data = [{"id": i, "consistent": i % 2 == 0} for i in range(350)]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_data, f)
        return f.name

def test_calculate_sample_size_binary():
    """Test binary sample size calculation."""
    # Standard case: p0=0.1, p1=0.15, alpha=0.05, power=0.8
    # Expected n per group is roughly 393 (standard approximation)
    n = calculate_sample_size_binary(0.1, 0.15, 0.05, 0.8)
    assert n > 0
    assert isinstance(n, int)
    
    # Zero effect should raise
    with pytest.raises(ValueError):
        calculate_sample_size_binary(0.1, 0.1, 0.05, 0.8)

def test_calculate_sample_size_continuous():
    """Test continuous sample size calculation."""
    # Cohen's d = 0.5 (medium effect)
    n = calculate_sample_size_continuous(0.5, 0.05, 0.8)
    assert n > 0
    assert isinstance(n, int)

def test_count_corpus_size_from_json(temp_audit_json):
    """Test counting records from JSON."""
    count = count_corpus_size(Path(temp_audit_json))
    assert count == 5
    os.unlink(temp_audit_json)

def test_count_corpus_size_from_large_json(temp_audit_json_large):
    """Test counting records from large JSON."""
    count = count_corpus_size(Path(temp_audit_json_large))
    assert count == 350
    os.unlink(temp_audit_json_large)

def test_run_power_analysis_valid_corpus(temp_audit_json_large):
    """Test power analysis with a corpus that meets the N >= 300 requirement."""
    result = run_power_analysis(
        audit_report_path=Path(temp_audit_json_large),
        baseline_rate=0.1,
        detectable_effect=0.05,
        alpha=0.05,
        power=0.8,
        is_binary=True
    )
    
    assert result["actual_corpus_n"] == 350
    assert result["meets_minimum_threshold_300"] is True
    assert result["is_valid"] is True
    
    os.unlink(temp_audit_json_large)

def test_run_power_analysis_invalid_corpus(temp_audit_json):
    """Test power analysis with a corpus that is too small (< 300)."""
    # Note: The requirement is N >= 300 OR N >= calculated_minimum.
    # If calculated_minimum is very small (e.g., huge effect), it might pass.
    # But with default effect 0.05, calculated_minimum will be > 300.
    # So 5 records should fail.
    
    result = run_power_analysis(
        audit_report_path=Path(temp_audit_json),
        baseline_rate=0.1,
        detectable_effect=0.05,
        alpha=0.05,
        power=0.8,
        is_binary=True
    )
    
    assert result["actual_corpus_n"] == 5
    assert result["meets_minimum_threshold_300"] is False
    # The calculated minimum for 5% effect is likely > 5, so meets_calculated_minimum should be False
    assert result["is_valid"] is False
    
    os.unlink(temp_audit_json)

def test_write_power_analysis_result():
    """Test writing results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.json"
        result = {
            "test": "value",
            "number": 123
        }
        write_power_analysis_result(result, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert data["test"] == "value"
            assert data["number"] == 123