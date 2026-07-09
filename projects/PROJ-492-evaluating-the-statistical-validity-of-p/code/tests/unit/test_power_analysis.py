import json
import pytest
from pathlib import Path
import tempfile
import os

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    CLAIM_CORPUS_THRESHOLD
)
from code.src.config import SEED

def test_calculate_sample_size_binary():
    """Test binary sample size calculation with known values."""
    # Standard example: p1=0.1, p2=0.11 (10% relative increase), alpha=0.05, power=0.8
    # Expected N is roughly 14,000-15,000 per group for small effects.
    n = calculate_sample_size_binary(
        baseline_rate=0.10,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80
    )
    assert n > 0
    assert isinstance(n, int)
    # Rough check: for small effect sizes, N should be large
    assert n > 1000

def test_calculate_sample_size_continuous():
    """Test continuous sample size calculation."""
    # Cohen's d = 0.5 (medium effect)
    n = calculate_sample_size_continuous(
        baseline_mean=100,
        detectable_effect=5,
        std_dev=10,
        alpha=0.05,
        power=0.80
    )
    # For d=0.5, n per group should be around 64
    assert n > 50
    assert n < 100

def test_count_corpus_size_empty():
    """Test counting records in an empty or missing file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_path = Path(f.name)

    try:
        count = count_corpus_size(temp_path)
        assert count == 0
    finally:
        temp_path.unlink()

def test_count_corpus_size_with_data():
    """Test counting records in a valid audit report."""
    mock_data = [
        {"id": 1, "inconsistent": True},
        {"id": 2, "inconsistent": False},
        {"id": 3, "inconsistent": True}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_data, f)
        temp_path = Path(f.name)

    try:
        count = count_corpus_size(temp_path)
        assert count == 3
    finally:
        temp_path.unlink()

def test_run_power_analysis_writes_json():
    """Test that run_power_analysis creates the output file."""
    mock_data = [{"id": i} for i in range(3000)] # Ensure > threshold
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        input_path = tmp_path / "audit_report.json"
        output_path = tmp_path / "power_analysis.json"

        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        result = run_power_analysis(
            audit_report_path=input_path,
            output_path=output_path,
            baseline_rate=0.10,
            detectable_effect=0.01,
            alpha=0.05,
            power=0.80
        )

        assert output_path.exists()
        assert result["actual_corpus_size"] == 3000
        assert "assertions" in result
        # Check if it meets the threshold (3000 > 2511)
        assert result["assertions"]["meets_claim_corpus_threshold"] is True

def test_claim_threshold_constant():
    """Verify the claim threshold constant is defined."""
    assert isinstance(CLAIM_CORPUS_THRESHOLD, int)
    assert CLAIM_CORPUS_THRESHOLD > 0