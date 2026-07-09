"""
Unit tests for power analysis utility.

Tests FR-025 compliance: sample size calculation and corpus validation.
"""
import json
import pytest
from pathlib import Path
import numpy as np
from scipy import stats

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result
)
from code.src.utils.logger import get_default_logger

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def sample_corpus_json(tmp_path):
    """Create a sample audit report JSON file."""
    corpus_path = tmp_path / "audit_report.json"
    sample_data = [
        {"id": 1, "inconsistent": False},
        {"id": 2, "inconsistent": True},
        {"id": 3, "inconsistent": False},
        {"id": 4, "inconsistent": True},
        {"id": 5, "inconsistent": False}
    ]
    with open(corpus_path, 'w') as f:
        json.dump(sample_data, f)
    return corpus_path

def test_calculate_sample_size_binary_valid_inputs():
    """Test sample size calculation with valid inputs."""
    n = calculate_sample_size_binary(
        baseline_rate=0.05,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80
    )
    
    assert isinstance(n, int)
    assert n > 0
    # For small effect sizes, n should be reasonably large
    assert n >= 1000

def test_calculate_sample_size_binary_invalid_baseline():
    """Test that invalid baseline rate raises ValueError."""
    with pytest.raises(ValueError):
        calculate_sample_size_binary(
            baseline_rate=0,  # Invalid
            detectable_effect=0.01,
            alpha=0.05,
            power=0.80
        )
    
    with pytest.raises(ValueError):
        calculate_sample_size_binary(
            baseline_rate=1.5,  # Invalid
            detectable_effect=0.01,
            alpha=0.05,
            power=0.80
        )

def test_calculate_sample_size_binary_invalid_effect():
    """Test that invalid detectable effect raises ValueError."""
    with pytest.raises(ValueError):
        calculate_sample_size_binary(
            baseline_rate=0.05,
            detectable_effect=0,  # Invalid
            alpha=0.05,
            power=0.80
        )
    
    with pytest.raises(ValueError):
        calculate_sample_size_binary(
            baseline_rate=0.05,
            detectable_effect=1.5,  # Invalid
            alpha=0.05,
            power=0.80
        )

def test_calculate_sample_size_binary_zero_effect():
    """Test that zero effect size raises ValueError."""
    # This should raise an error because effect size becomes zero
    with pytest.raises(ValueError):
        calculate_sample_size_binary(
            baseline_rate=0.5,
            detectable_effect=0.0,
            alpha=0.05,
            power=0.80
        )

def test_calculate_sample_size_continuous_valid_inputs():
    """Test sample size calculation for continuous outcomes."""
    n = calculate_sample_size_continuous(
        baseline_mean=10.0,
        detectable_effect=1.0,
        std_dev=2.0,
        alpha=0.05,
        power=0.80
    )
    
    assert isinstance(n, int)
    assert n > 0

def test_calculate_sample_size_continuous_invalid_std():
    """Test that invalid std_dev raises ValueError."""
    with pytest.raises(ValueError):
        calculate_sample_size_continuous(
            baseline_mean=10.0,
            detectable_effect=1.0,
            std_dev=0,  # Invalid
            alpha=0.05,
            power=0.80
        )
    
    with pytest.raises(ValueError):
        calculate_sample_size_continuous(
            baseline_mean=10.0,
            detectable_effect=1.0,
            std_dev=-1.0,  # Invalid
            alpha=0.05,
            power=0.80
        )

def test_count_corpus_size_valid_file(sample_corpus_json):
    """Test counting records in a valid corpus file."""
    count = count_corpus_size(sample_corpus_json)
    assert count == 5

def test_count_corpus_size_nonexistent_file():
    """Test that nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        count_corpus_size(Path("/nonexistent/path/file.json"))

def test_run_power_analysis_basic(temp_output_dir):
    """Test basic power analysis execution."""
    result = run_power_analysis(
        baseline_rate=0.05,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80,
        corpus_path=None,
        output_path=None,
        logger=get_default_logger(__name__)
    )
    
    assert "min_sample_size_per_group" in result
    assert "min_total_sample_size" in result
    assert "corpus_size" not in result or result["corpus_size"] is None
    assert isinstance(result["min_sample_size_per_group"], int)
    assert result["min_sample_size_per_group"] > 0

def test_run_power_analysis_with_corpus(temp_output_dir, sample_corpus_json):
    """Test power analysis with corpus validation."""
    result = run_power_analysis(
        baseline_rate=0.05,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80,
        corpus_path=sample_corpus_json,
        output_path=None,
        logger=get_default_logger(__name__)
    )
    
    assert result["corpus_size"] == 5
    assert "corpus_valid" in result
    assert result["requirement_reference"] == "c_21f3e400"
    assert result["requirement_source"] == "https://arxiv.org/abs/2510.17487"

def test_write_power_analysis_result(temp_output_dir):
    """Test writing results to JSON file."""
    result = {
        "baseline_rate": 0.05,
        "min_sample_size_per_group": 1234,
        "corpus_valid": True
    }
    
    output_path = temp_output_dir / "power_analysis.json"
    write_power_analysis_result(result, output_path, get_default_logger(__name__))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved = json.load(f)
        
    assert saved["min_sample_size_per_group"] == 1234
    assert saved["baseline_rate"] == 0.05

def test_power_analysis_result_contains_numeric_n(temp_output_dir, sample_corpus_json):
    """Test that result contains numeric N as required by FR-025."""
    result = run_power_analysis(
        baseline_rate=0.05,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80,
        corpus_path=sample_corpus_json,
        output_path=temp_output_dir / "power_analysis.json",
        logger=get_default_logger(__name__)
    )
    
    # Verify the result contains a numeric N
    assert isinstance(result["min_sample_size_per_group"], (int, float))
    assert result["min_sample_size_per_group"] > 0
    
    # Verify the written file also contains numeric N
    with open(temp_output_dir / "power_analysis.json", 'r') as f:
        saved = json.load(f)
        
    assert isinstance(saved["min_sample_size_per_group"], (int, float))
    assert saved["min_sample_size_per_group"] > 0

def test_power_analysis_validates_corpus_against_claim(temp_output_dir, sample_corpus_json):
    """Test that corpus validation references claim c_21f3e400."""
    result = run_power_analysis(
        baseline_rate=0.05,
        detectable_effect=0.01,
        alpha=0.05,
        power=0.80,
        corpus_path=sample_corpus_json,
        output_path=temp_output_dir / "power_analysis.json",
        logger=get_default_logger(__name__)
    )
    
    assert "corpus_valid" in result
    assert result["requirement_reference"] == "c_21f3e400"
    assert "2510.17487" in result["requirement_source"]
    assert "arxiv.org" in result["requirement_source"]
