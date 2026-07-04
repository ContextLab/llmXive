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
    write_power_analysis_result
)

def test_calculate_sample_size_binary():
    """Test binary sample size calculation."""
    # Standard case: 10% baseline, 2% effect, 80% power, 5% alpha
    n = calculate_sample_size_binary(0.10, 0.02, 0.05, 0.80)
    assert n > 0
    # Expected value should be around 3900-4000 for these parameters
    assert 3000 < n < 5000

def test_calculate_sample_size_binary_invalid_input():
    """Test that invalid inputs raise errors."""
    with pytest.raises(ValueError):
        calculate_sample_size_binary(0.0, 0.02, 0.05, 0.80)  # baseline_rate=0
    
    with pytest.raises(ValueError):
        calculate_sample_size_binary(0.10, 0.0, 0.05, 0.80)  # effect=0

def test_calculate_sample_size_continuous():
    """Test continuous sample size calculation."""
    n = calculate_sample_size_continuous(10.0, 1.0, 2.0, 0.05, 0.80)
    assert n > 0
    # Expected value should be around 64 for these parameters (Cohen's d=0.5)
    assert 50 < n < 100

def test_count_corpus_size_empty_file():
    """Test counting corpus size with empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("[]")
        temp_path = Path(f.name)
    
    try:
        count = count_corpus_size(temp_path)
        assert count == 0
    finally:
        os.unlink(temp_path)

def test_count_corpus_size_with_exclusions():
    """Test counting corpus size with exclusions."""
    data = [
        {"id": 1, "data_quality_warning": False},
        {"id": 2, "data_quality_warning": True},
        {"id": 3, "data_quality_warning": False}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)
    
    try:
        count = count_corpus_size(temp_path)
        assert count == 2
    finally:
        os.unlink(temp_path)

def test_run_power_analysis():
    """Test full power analysis run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "power_analysis.json"
        corpus_path = Path(tmpdir) / "audit_report.json"
        
        # Create a dummy audit report
        with open(corpus_path, 'w') as f:
            json.dump([{"id": i, "data_quality_warning": False} for i in range(301)], f)
        
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80,
            corpus_path=corpus_path,
            seed=42
        )
        
        assert "calculated_minimum_n_per_group" in result
        assert "corpus_size" in result
        assert result["corpus_size"] == 301
        assert result["meets_requirement"] is True

def test_write_power_analysis_result():
    """Test writing power analysis result to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "result.json"
        result = {"test": 123}
        
        write_power_analysis_result(result, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == result
