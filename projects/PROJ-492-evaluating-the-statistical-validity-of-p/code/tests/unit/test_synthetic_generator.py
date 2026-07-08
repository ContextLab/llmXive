"""
Unit tests for the synthetic dataset generator.
Verifies generation of >= 10,000 records with both outcome types.
"""
import csv
import json
import os
import pytest
from pathlib import Path
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

DATA_DIR = Path("data/synthetic")
SUMMARIES_FILE = DATA_DIR / "synthetic_summaries.csv"
METADATA_FILE = DATA_DIR / "synthetic_metadata.json"


class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds_deterministic(self):
        """Test that setting seeds produces deterministic results."""
        set_all_seeds(SEED)
        val1 = np.random.random()
        set_all_seeds(SEED)
        val2 = np.random.random()
        assert val1 == val2, "Seeding should produce identical results"

    def test_generate_sample_sizes_range(self):
        """Test sample sizes are within expected range."""
        n_control, n_treatment = generate_sample_sizes()
        assert 100 <= n_control <= 10000
        assert 100 <= n_treatment <= 10000
        assert isinstance(n_control, int)
        assert isinstance(n_treatment, int)

    def test_generate_binary_outcome_structure(self):
        """Test binary outcome generation produces correct structure."""
        data = generate_binary_outcome(1000, 1000, 0.5, 0.1)
        assert data["outcome_type"] == "binary"
        assert data["n_control"] == 1000
        assert data["n_treatment"] == 1000
        assert "control_successes" in data
        assert "treatment_successes" in data
        assert "p_value" in data
        assert 0.0 <= data["p_value"] <= 1.0

    def test_generate_continuous_outcome_structure(self):
        """Test continuous outcome generation produces correct structure."""
        data = generate_continuous_outcome(1000, 1000, 50.0, 10.0, 0.1)
        assert data["outcome_type"] == "continuous"
        assert data["n_control"] == 1000
        assert data["n_treatment"] == 1000
        assert "control_mean" in data
        assert "treatment_mean" in data
        assert "p_value" in data
        assert 0.0 <= data["p_value"] <= 1.0

    def test_generate_synthetic_dataset_minimum_count(self):
        """Test that generated dataset has at least 10,000 records."""
        summaries = generate_synthetic_dataset(total_count=10000)
        assert len(summaries) >= 10000, \
            f"Expected >= 10000 summaries, got {len(summaries)}"

    def test_generate_synthetic_dataset_both_types(self):
        """Test that both binary and continuous outcomes are present."""
        summaries = generate_synthetic_dataset(total_count=10000)
        types = [s["outcome_type"] for s in summaries]
        assert "binary" in types, "Binary outcomes missing"
        assert "continuous" in types, "Continuous outcomes missing"

    def test_verify_outcome_types_raises_on_missing(self):
        """Test that verify_outcome_types raises if type is missing."""
        binary_only = [{"outcome_type": "binary"}]
        with pytest.raises(AssertionError):
            verify_outcome_types(binary_only)

        continuous_only = [{"outcome_type": "continuous"}]
        with pytest.raises(AssertionError):
            verify_outcome_types(continuous_only)

    def test_verify_outcome_types_success(self):
        """Test verify_outcome_types passes with mixed data."""
        mixed = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        counts = verify_outcome_types(mixed)
        assert counts["binary"] == 1
        assert counts["continuous"] == 1

    def test_main_creates_files(self):
        """Test that main() creates expected output files."""
        # Run generation
        main()

        # Verify files exist
        assert SUMMARIES_FILE.exists(), "Summaries file not created"
        assert METADATA_FILE.exists(), "Metadata file not created"

    def test_main_file_contents_valid(self):
        """Test that generated files have valid content."""
        main()

        # Check CSV row count
        with open(SUMMARIES_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            header = rows[0]
            data_rows = rows[1:]

        assert len(data_rows) >= 10000, \
            f"Expected >= 10000 data rows, got {len(data_rows)}"

        # Verify header contains required fields
        required_fields = ["outcome_type", "n_control", "n_treatment", "p_value"]
        for field in required_fields:
            assert field in header, f"Missing field in CSV: {field}"

        # Check outcome types in data
        types = [row[0] for row in data_rows]  # outcome_type is first column
        assert "binary" in types, "Binary outcomes missing in CSV"
        assert "continuous" in types, "Continuous outcomes missing in CSV"

    def test_main_metadata_valid(self):
        """Test that metadata JSON is valid and complete."""
        main()

        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        assert "total_records" in metadata
        assert metadata["total_records"] >= 10000
        assert "outcome_counts" in metadata
        assert metadata["outcome_counts"]["binary"] > 0
        assert metadata["outcome_counts"]["continuous"] > 0
        assert "parameters" in metadata
        assert metadata["parameters"]["seed"] == SEED
