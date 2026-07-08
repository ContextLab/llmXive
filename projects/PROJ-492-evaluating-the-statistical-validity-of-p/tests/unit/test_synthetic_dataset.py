"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
1. Generation of at least 10,000 records
2. Presence of both binary and continuous outcomes
3. Data integrity and schema compliance
4. Reproducibility via seeding
"""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_summaries,
    write_metadata,
    DEFAULT_COUNT,
    BINARY_RATIO
)
from code.src.config import SEED

class TestSyntheticDatasetGeneration:
    """Test suite for synthetic dataset generation."""

    def test_minimum_record_count(self):
        """Verify that the generator produces at least 10,000 records (FR-030)."""
        summaries = generate_synthetic_dataset(count=10000, seed=SEED)
        assert len(summaries) >= 10000, f"Expected at least 10,000 records, got {len(summaries)}"

    def test_both_outcome_types_present(self):
        """Verify that both binary and continuous outcomes are generated."""
        summaries = generate_synthetic_dataset(count=10000, seed=SEED)
        counts = verify_outcome_types(summaries)

        assert counts["binary"] > 0, "No binary outcomes generated"
        assert counts["continuous"] > 0, "No continuous outcomes generated"

    def test_outcome_type_ratio(self):
        """Verify that the ratio of outcome types is approximately 50/50."""
        summaries = generate_synthetic_dataset(count=10000, seed=SEED)
        counts = verify_outcome_types(summaries)
        total = counts["binary"] + counts["continuous"]

        binary_ratio = counts["binary"] / total
        # Allow 20% tolerance around 0.5
        assert 0.3 <= binary_ratio <= 0.7, f"Binary ratio {binary_ratio} outside expected range"

    def test_required_fields_present(self):
        """Verify that all required fields are present in generated summaries."""
        required_fields = [
            "url", "domain", "year", "outcome_type",
            "control_sample_size", "treatment_sample_size",
            "reported_p_value", "is_significant"
        ]

        summaries = generate_synthetic_dataset(count=100, seed=SEED)
        for summary in summaries:
            for field in required_fields:
                assert field in summary, f"Missing required field: {field}"

    def test_sample_size_ranges(self):
        """Verify that sample sizes are within expected ranges."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            c_size = summary["control_sample_size"]
            t_size = summary["treatment_sample_size"]

            assert 100 <= c_size <= 50000, f"Control size {c_size} out of range"
            assert 100 <= t_size <= 50000, f"Treatment size {t_size} out of range"

    def test_p_value_range(self):
        """Verify that p-values are within valid probability range [0, 1]."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            p_val = summary["reported_p_value"]
            assert 0.0 <= p_val <= 1.0, f"P-value {p_val} out of range [0, 1]"

    def test_reproducibility(self):
        """Verify that generation is reproducible with the same seed."""
        summaries1 = generate_synthetic_dataset(count=100, seed=42)
        summaries2 = generate_synthetic_dataset(count=100, seed=42)

        # Compare first few fields to ensure reproducibility
        for s1, s2 in zip(summaries1, summaries2):
            assert s1["outcome_type"] == s2["outcome_type"]
            assert s1["control_sample_size"] == s2["control_sample_size"]
            assert s1["treatment_sample_size"] == s2["treatment_sample_size"]

    def test_binary_specific_fields(self):
        """Verify that binary outcomes have correct specific fields."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            if summary["outcome_type"] == "binary":
                assert "baseline_conversion_rate" in summary
                assert "treatment_conversion_rate" in summary
                assert 0.0 <= summary["baseline_conversion_rate"] <= 1.0
                assert 0.0 <= summary["treatment_conversion_rate"] <= 1.0

    def test_continuous_specific_fields(self):
        """Verify that continuous outcomes have correct specific fields."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            if summary["outcome_type"] == "continuous":
                assert "baseline_mean" in summary
                assert "treatment_mean" in summary
                assert "control_std" in summary
                assert "treatment_std" in summary

    def test_domain_distribution(self):
        """Verify that domains are drawn from the expected list."""
        valid_domains = {
            "tech", "marketing", "finance", "healthcare", "education",
            "e-commerce", "gaming", "social-media", "retail", "logistics"
        }

        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            assert summary["domain"] in valid_domains, f"Invalid domain: {summary['domain']}"

    def test_year_range(self):
        """Verify that years are within expected range."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            year = summary["year"]
            assert 2018 <= year <= 2024, f"Year {year} out of range [2018, 2024]"

    def test_significance_flag_consistency(self):
        """Verify that is_significant flag matches p-value threshold."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)

        for summary in summaries:
            p_val = summary["reported_p_value"]
            is_sig = summary["is_significant"]

            expected_sig = p_val < 0.05
            assert is_sig == expected_sig, f"Significance flag mismatch for p={p_val}"

class TestSyntheticDatasetIO:
    """Test suite for synthetic dataset I/O operations."""

    def test_write_summaries_to_csv(self, tmp_path):
        """Verify that summaries can be written to and read from CSV."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)
        output_path = tmp_path / "test_summaries.csv"

        write_summaries(summaries, output_path)

        assert output_path.exists(), "CSV file was not created"

        # Read back and verify count
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(summaries), f"Expected {len(summaries)} rows, got {len(rows)}"

    def test_write_metadata_json(self, tmp_path):
        """Verify that metadata can be written to JSON."""
        summaries = generate_synthetic_dataset(count=100, seed=SEED)
        output_path = tmp_path / "test_metadata.json"

        write_metadata(summaries, output_path)

        assert output_path.exists(), "Metadata file was not created"

        with open(output_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        assert metadata["total_count"] == len(summaries)
        assert "outcome_type_counts" in metadata
        assert "generated_at" in metadata
        assert "seed" in metadata

    def test_large_dataset_generation(self):
        """Verify that the generator can handle the full 10,000+ record requirement."""
        # Generate the full required dataset
        summaries = generate_synthetic_dataset(count=10000, seed=SEED)

        assert len(summaries) >= 10000
        counts = verify_outcome_types(summaries)
        assert counts["binary"] > 0
        assert counts["continuous"] > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
