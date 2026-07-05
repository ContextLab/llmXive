"""
Unit tests for synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Presence of both binary and continuous outcomes
- Correct data structure and field types
- Reproducibility via seeded RNGs
"""
import pytest
import json
import csv
import math
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    TOTAL_MIN_COUNT,
    SYNTHETIC_CSV_PATH,
    SYNTHETIC_JSON_PATH,
    METADATA_PATH
)
from code.src.config import SEED

class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds_reproducibility(self):
        """Test that setting seeds produces reproducible results."""
        set_all_seeds(SEED)
        result1 = generate_sample_sizes(100)
        
        set_all_seeds(SEED)
        result2 = generate_sample_sizes(100)
        
        assert result1 == result2, "Seeded generation should be reproducible"

    def test_generate_sample_sizes_range(self):
        """Test that sample sizes are within expected range."""
        sizes = generate_sample_sizes(1000)
        
        assert len(sizes) == 1000
        assert all(100 <= s <= 5000 for s in sizes), "Sample sizes must be between 100 and 5000"

    def test_generate_binary_outcome_structure(self):
        """Test binary outcome generation produces correct structure."""
        result = generate_binary_outcome(1000, 0.1, 0.05, False)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", 
            "control_conversions", "treatment_conversions",
            "obs_control_rate", "obs_treatment_rate",
            "reported_p_value", "reported_effect_size"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        assert result["outcome_type"] == "binary"
        assert 0 <= result["obs_control_rate"] <= 1
        assert 0 <= result["obs_treatment_rate"] <= 1
        assert 0 <= result["reported_p_value"] <= 1

    def test_generate_continuous_outcome_structure(self):
        """Test continuous outcome generation produces correct structure."""
        result = generate_continuous_outcome(1000, 50.0, 10.0, 0.2, False)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "control_mean", "treatment_mean", "control_std", "treatment_std",
            "reported_p_value", "reported_effect_size"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        assert result["outcome_type"] == "continuous"
        assert result["reported_p_value"] >= 0
        assert result["reported_p_value"] <= 1

    def test_generate_synthetic_dataset_minimum_count(self):
        """Test that generated dataset meets minimum count requirement."""
        summaries = generate_synthetic_dataset(total_count=TOTAL_MIN_COUNT)
        
        assert len(summaries) >= TOTAL_MIN_COUNT, \
            f"Generated {len(summaries)} records, need at least {TOTAL_MIN_COUNT}"

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that both binary and continuous outcomes are present."""
        summaries = generate_synthetic_dataset(total_count=TOTAL_MIN_COUNT)
        
        binary_count, continuous_count = verify_outcome_types(summaries)
        
        assert binary_count > 0, "Must have at least one binary outcome"
        assert continuous_count > 0, "Must have at least one continuous outcome"
        assert binary_count + continuous_count == len(summaries)

    def test_generate_synthetic_dataset_metadata_fields(self):
        """Test that all summaries have required metadata fields."""
        summaries = generate_synthetic_dataset(total_count=100)
        
        required_metadata = ["test_id", "domain", "year", "is_intentionally_inconsistent"]
        
        for summary in summaries:
            for field in required_metadata:
                assert field in summary, f"Missing metadata field: {field}"
            
            # Validate specific field constraints
            assert summary["outcome_type"] in ["binary", "continuous"]
            assert isinstance(summary["test_id"], str)
            assert isinstance(summary["domain"], str)
            assert isinstance(summary["year"], int)
            assert 2020 <= summary["year"] <= 2025
            assert isinstance(summary["is_intentionally_inconsistent"], bool)

    def test_verify_outcome_types_raises_on_missing(self):
        """Test that verification raises on missing outcome types."""
        # Test with only binary
        binary_only = [{"outcome_type": "binary"} for _ in range(10)]
        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(binary_only)
        
        # Test with only continuous
        continuous_only = [{"outcome_type": "continuous"} for _ in range(10)]
        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(continuous_only)

    def test_generate_synthetic_dataset_inconsistent_ratio(self):
        """Test that inconsistent ratio is approximately as specified."""
        summaries = generate_synthetic_dataset(
            total_count=1000,
            binary_ratio=0.5,
            inconsistent_ratio=0.2
        )
        
        inconsistent_count = sum(1 for s in summaries if s.get("is_intentionally_inconsistent"))
        actual_ratio = inconsistent_count / len(summaries)
        
        # Allow some variance due to randomness
        assert 0.15 <= actual_ratio <= 0.25, \
            f"Inconsistent ratio {actual_ratio:.3f} outside expected range [0.15, 0.25]"

    def test_csv_output_format(self):
        """Test that CSV output has correct format and content."""
        summaries = generate_synthetic_dataset(total_count=100)
        
        # Write to temporary file for testing
        test_path = Path("data/test_synthetic.csv")
        test_path.parent.mkdir(exist_ok=True)
        
        from code.src.audit.synthetic import write_csv_output
        write_csv_output(summaries, test_path)
        
        # Read and verify
        with open(test_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 100
        assert "outcome_type" in rows[0]
        assert "test_id" in rows[0]
        
        # Cleanup
        test_path.unlink()

    def test_json_output_format(self):
        """Test that JSON output has correct format and content."""
        summaries = generate_synthetic_dataset(total_count=100)
        
        # Write to temporary file for testing
        test_path = Path("data/test_synthetic.json")
        test_path.parent.mkdir(exist_ok=True)
        
        from code.src.audit.synthetic import write_json_output
        write_json_output(summaries, test_path)
        
        # Read and verify
        with open(test_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 100
        assert "outcome_type" in data[0]
        assert "test_id" in data[0]
        
        # Cleanup
        test_path.unlink()

    def test_deterministic_generation(self):
        """Test that generation is deterministic with fixed seed."""
        set_all_seeds(SEED)
        summaries1 = generate_synthetic_dataset(total_count=50)
        
        set_all_seeds(SEED)
        summaries2 = generate_synthetic_dataset(total_count=50)
        
        # Compare key fields
        for s1, s2 in zip(summaries1, summaries2):
            assert s1["outcome_type"] == s2["outcome_type"]
            assert s1["n_control"] == s2["n_control"]
            assert s1["n_treatment"] == s2["n_treatment"]
            # Allow small floating point differences
            assert math.isclose(s1["reported_p_value"], s2["reported_p_value"], rel_tol=1e-9)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
