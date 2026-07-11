"""
Unit tests for the synthetic dataset generator (T026).
"""
import csv
import os
import sys
from pathlib import Path

import pytest
import numpy as np

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    MIN_RECORDS,
    TARGET_RECORDS
)

class TestSyntheticGenerator:
    def test_minimum_record_count(self):
        """Verify that the generator produces at least MIN_RECORDS."""
        summaries, _ = generate_synthetic_dataset(n_records=TARGET_RECORDS)
        assert len(summaries) >= MIN_RECORDS, f"Generated {len(summaries)} records, expected >= {MIN_RECORDS}"

    def test_outcome_types_present(self):
        """Verify both binary and continuous outcomes are generated."""
        summaries, _ = generate_synthetic_dataset(n_records=TARGET_RECORDS)
        assert verify_outcome_types(summaries), "Missing binary or continuous outcomes"

    def test_required_fields_present(self):
        """Verify all required fields exist in generated summaries."""
        summaries, _ = generate_synthetic_dataset(n_records=100)
        required_fields = [
            "id", "domain", "outcome_type", "n_control", "n_treatment",
            "reported_p_value", "test_type", "year"
        ]
        for row in summaries:
            for field in required_fields:
                assert field in row, f"Missing field {field} in row {row.get('id')}"

    def test_p_value_range(self):
        """Verify reported p-values are within valid range (0, 1)."""
        summaries, _ = generate_synthetic_dataset(n_records=100)
        for row in summaries:
            p_val = row["reported_p_value"]
            assert 0.0 < p_val <= 1.0, f"P-value {p_val} out of range for {row['id']}"

    def test_sample_sizes_positive(self):
        """Verify sample sizes are positive integers."""
        summaries, _ = generate_synthetic_dataset(n_records=100)
        for row in summaries:
            assert row["n_control"] > 0, f"Invalid n_control for {row['id']}"
            assert row["n_treatment"] > 0, f"Invalid n_treatment for {row['id']}"

    def test_domains_valid(self):
        """Verify domains are from the expected list."""
        summaries, _ = generate_synthetic_dataset(n_records=100)
        valid_domains = {"tech", "finance", "health", "e-commerce", "education"}
        for row in summaries:
            assert row["domain"] in valid_domains, f"Invalid domain {row['domain']}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
