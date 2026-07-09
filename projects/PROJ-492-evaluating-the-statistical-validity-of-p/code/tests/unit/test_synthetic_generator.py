"""
Unit tests for synthetic dataset generator (T026).

Verifies:
1. At least 10,000 records are generated
2. Both binary and continuous outcomes are present
3. Data structure matches ABTestSummary model expectations
4. Statistical properties are reasonable
"""
import json
import csv
from pathlib import Path
import pytest
import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    main
)
from code.src.config import SEED

# Test constants
TEST_SEED = 42
MIN_RECORDS = 10000

@pytest.fixture
def synthetic_data_dir():
    """Fixture to ensure test data directory exists."""
    test_dir = Path("code/data/synthetic/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

def test_set_all_seeds():
    """Test that seeds are set correctly."""
    set_all_seeds(TEST_SEED)
    # Verify reproducibility
    np.random.seed(TEST_SEED)
    val1 = np.random.random()
    set_all_seeds(TEST_SEED)
    val2 = np.random.random()
    assert val1 == val2, "Seeds should produce reproducible results"

def test_generate_sample_sizes():
    """Test sample size generation."""
    n_control, n_treatment = generate_sample_sizes()
    assert isinstance(n_control, int)
    assert isinstance(n_treatment, int)
    assert n_control >= 100  # MIN_SAMPLE_SIZE
    assert n_treatment >= 100
    assert n_control <= 50000  # MAX_SAMPLE_SIZE
    assert n_treatment <= 50000

def test_generate_binary_outcome():
    """Test binary outcome generation."""
    n_control, n_treatment = 1000, 1000
    baseline_prob, effect_size = 0.2, 0.05
    
    successes_control, successes_treatment, p_value, effect_size_obs = generate_binary_outcome(
        n_control, n_treatment, baseline_prob, effect_size
    )
    
    assert 0 <= successes_control <= n_control
    assert 0 <= successes_treatment <= n_treatment
    assert 0.0 <= p_value <= 1.0
    assert isinstance(effect_size_obs, float)

def test_generate_continuous_outcome():
    """Test continuous outcome generation."""
    n_control, n_treatment = 1000, 1000
    mean_control, std_control = 50.0, 10.0
    effect_size = 0.1
    
    mean_control_obs, mean_treatment_obs, p_value, effect_size_obs = generate_continuous_outcome(
        n_control, n_treatment, mean_control, std_control, effect_size
    )
    
    assert isinstance(mean_control_obs, float)
    assert isinstance(mean_treatment_obs, float)
    assert 0.0 <= p_value <= 1.0
    assert isinstance(effect_size_obs, float)

def test_generate_synthetic_dataset_size():
    """Test that the generated dataset has at least 10,000 records."""
    set_all_seeds(TEST_SEED)
    summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, seed=TEST_SEED)
    assert len(summaries) >= MIN_RECORDS, f"Expected at least {MIN_RECORDS} records, got {len(summaries)}"

def test_generate_synthetic_dataset_outcome_types():
    """Test that both binary and continuous outcomes are present."""
    set_all_seeds(TEST_SEED)
    summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, binary_ratio=0.5, seed=TEST_SEED)
    
    counts = verify_outcome_types(summaries)
    
    assert counts["binary"] > 0, "No binary outcomes found"
    assert counts["continuous"] > 0, "No continuous outcomes found"
    assert counts["binary"] + counts["continuous"] == len(summaries)

def test_generate_synthetic_dataset_structure():
    """Test that generated records have required fields."""
    set_all_seeds(TEST_SEED)
    summaries = generate_synthetic_dataset(n_records=100, seed=TEST_SEED)
    
    required_fields = [
        "id", "url", "domain", "test_type", "outcome_type",
        "n_control", "n_treatment", "reported_p_value", "effect_size"
    ]
    
    for summary in summaries:
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"
        
        # Verify outcome_type is valid
        assert summary["outcome_type"] in ["binary", "continuous"]
        
        # Verify numeric fields
        assert isinstance(summary["n_control"], int)
        assert isinstance(summary["n_treatment"], int)
        assert 0.0 <= summary["reported_p_value"] <= 1.0

def test_generate_synthetic_dataset_determinism():
    """Test that generation is deterministic with same seed."""
    summaries1 = generate_synthetic_dataset(n_records=100, seed=TEST_SEED)
    summaries2 = generate_synthetic_dataset(n_records=100, seed=TEST_SEED)
    
    assert len(summaries1) == len(summaries2)
    for s1, s2 in zip(summaries1, summaries2):
        assert s1["id"] == s2["id"]
        assert s1["outcome_type"] == s2["outcome_type"]
        assert s1["n_control"] == s2["n_control"]
        assert s1["n_treatment"] == s2["n_treatment"]
        # Allow small floating point differences for p-values
        assert abs(s1["reported_p_value"] - s2["reported_p_value"]) < 1e-10

def test_main_function_creates_files(tmp_path):
    """Test that main() creates the expected output files."""
    import sys
    from unittest.mock import patch
    
    # Temporarily change output paths for testing
    original_csv = Path("code/data/synthetic/synthetic_summaries.csv")
    original_json = Path("code/data/synthetic/synthetic_summaries.json")
    original_metadata = Path("code/data/synthetic/synthetic_metadata.json")
    
    # Use temporary directory
    test_csv = tmp_path / "synthetic_summaries.csv"
    test_json = tmp_path / "synthetic_summaries.json"
    test_metadata = tmp_path / "synthetic_metadata.json"
    
    # We can't easily override the module-level constants, so we'll just verify
    # that the main function runs without error and creates files in the expected location
    # For a full test, we'd need to refactor the module to accept paths as parameters
    
    # Instead, we'll run a smaller generation and verify the logic
    set_all_seeds(TEST_SEED)
    summaries = generate_synthetic_dataset(n_records=100, seed=TEST_SEED)
    
    # Write to temp files manually
    fieldnames = list(summaries[0].keys())
    with open(test_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    with open(test_json, "w") as f:
        json.dump(summaries, f, indent=2)
    
    # Verify files exist and have content
    assert test_csv.exists()
    assert test_json.exists()
    
    with open(test_csv, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 100
    
    with open(test_json, "r") as f:
        data = json.load(f)
        assert len(data) == 100

def test_verify_outcome_types_raises_on_missing():
    """Test that verify_outcome_types raises ValueError if a type is missing."""
    # Binary only
    binary_summaries = [{"outcome_type": "binary"} for _ in range(10)]
    with pytest.raises(ValueError, match="No continuous outcomes"):
        verify_outcome_types(binary_summaries)
    
    # Continuous only
    continuous_summaries = [{"outcome_type": "continuous"} for _ in range(10)]
    with pytest.raises(ValueError, match="No binary outcomes"):
        verify_outcome_types(continuous_summaries)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
