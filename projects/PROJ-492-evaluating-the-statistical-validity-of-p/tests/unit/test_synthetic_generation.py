"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
  1. Generator produces at least 10,000 records
  2. Both binary and continuous outcome types are present
  3. Data structure matches expected schema
  4. Inconsistency flags are applied correctly
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_sample_sizes
)


class TestSyntheticGeneration:
    """Test suite for synthetic data generation."""

    def test_minimum_record_count(self):
        """Verify that at least 10,000 records are generated."""
        summaries = generate_synthetic_dataset(n_records=10000)
        assert len(summaries) >= 10000, f"Expected >= 10000 records, got {len(summaries)}"

    def test_both_outcome_types_present(self):
        """Verify that both binary and continuous outcomes are present."""
        summaries = generate_synthetic_dataset(n_records=10000)
        binary_count, continuous_count = verify_outcome_types(summaries)
        
        assert binary_count > 0, "No binary outcomes generated"
        assert continuous_count > 0, "No continuous outcomes generated"
        assert binary_count + continuous_count == len(summaries)

    def test_binary_outcome_structure(self):
        """Verify binary outcome records have correct fields."""
        summary = generate_binary_outcome(100, 100, 0.1, 0.05, False)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", 
            "successes_control", "successes_treatment",
            "baseline_rate", "treatment_rate", "effect_size",
            "p_reconstructed", "p_reported", "is_inconsistent"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"
        
        assert summary["outcome_type"] == "binary"
        assert 0 <= summary["p_reported"] <= 1.0

    def test_continuous_outcome_structure(self):
        """Verify continuous outcome records have correct fields."""
        summary = generate_continuous_outcome(100, 100, 500.0, 25.0, 100.0, False)
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "mean_control", "mean_treatment", "std_control", "std_treatment",
            "effect_size", "p_reconstructed", "p_reported", "is_inconsistent"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"
        
        assert summary["outcome_type"] == "continuous"
        assert 0 <= summary["p_reported"] <= 1.0

    def test_inconsistency_injection(self):
        """Verify that inconsistency flag is set correctly."""
        consistent = generate_binary_outcome(100, 100, 0.1, 0.05, False)
        inconsistent = generate_binary_outcome(100, 100, 0.1, 0.05, True)
        
        assert consistent["is_inconsistent"] is False
        assert inconsistent["is_inconsistent"] is True

    def test_sample_sizes_positive(self):
        """Verify sample sizes are always positive and reasonable."""
        for _ in range(100):
            n_c, n_t = generate_sample_sizes(0)
            assert n_c >= 50, f"Control size too small: {n_c}"
            assert n_t >= 50, f"Treatment size too small: {n_t}"

    def test_csv_output_format(self):
        """Test that CSV output is valid and readable."""
        import tempfile
        summaries = generate_synthetic_dataset(n_records=100)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
            fieldnames = list(summaries[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summaries)
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 100
                assert "outcome_type" in rows[0]
        finally:
            os.unlink(temp_path)

    def test_deterministic_seed(self):
        """Verify that same seed produces same results."""
        from code.src.config import set_rng_seed
        import random
        
        set_rng_seed(42)
        random.seed(42)
        summaries1 = generate_synthetic_dataset(n_records=100)
        
        set_rng_seed(42)
        random.seed(42)
        summaries2 = generate_synthetic_dataset(n_records=100)
        
        # Check first few records match
        for s1, s2 in zip(summaries1[:5], summaries2[:5]):
            assert s1["id"] == s2["id"]
            assert s1["outcome_type"] == s2["outcome_type"]
            assert s1["p_reported"] == s2["p_reported"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
