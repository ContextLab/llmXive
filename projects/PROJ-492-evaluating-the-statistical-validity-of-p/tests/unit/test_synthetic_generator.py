"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Binary and continuous outcome types
- Correct schema of generated summaries
- Ground truth consistency
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

from code.src.audit.synthetic import generate_synthetic_corpus, set_seeds
from code.src.config import SEED
from code.src.models.data_models import ABTestSummary


class TestSyntheticGenerator:
    """Tests for the synthetic dataset generator."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_minimum_record_count(self, temp_output_dir):
        """Verify that at least 10,000 records are generated (FR-030)."""
        summaries, ground_truth = generate_synthetic_corpus(
            n_records=10000,
            output_dir=temp_output_dir,
            seed=SEED
        )

        assert len(summaries) >= 10000, f"Expected >= 10000 records, got {len(summaries)}"
        assert len(ground_truth) >= 10000

    def test_binary_and_continuous_outcomes(self, temp_output_dir):
        """Verify both binary and continuous outcomes are generated."""
        summaries, _ = generate_synthetic_corpus(
            n_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir,
            seed=SEED
        )

        outcome_types = [s.outcome_type for s in summaries]
        assert "binary" in outcome_types, "No binary outcomes generated"
        assert "continuous" in outcome_types, "No continuous outcomes generated"

        binary_count = outcome_types.count("binary")
        continuous_count = outcome_types.count("continuous")
        assert binary_count > 0
        assert continuous_count > 0

    def test_summary_schema_validity(self, temp_output_dir):
        """Verify generated summaries conform to ABTestSummary schema."""
        summaries, _ = generate_synthetic_corpus(
            n_records=100,
            output_dir=temp_output_dir,
            seed=SEED
        )

        for summary in summaries:
            # Check required fields exist and have correct types
            assert isinstance(summary.test_id, str) and len(summary.test_id) > 0
            assert isinstance(summary.domain, str) and len(summary.domain) > 0
            assert isinstance(summary.year, int) and 2010 <= summary.year <= 2030
            assert summary.outcome_type in ["binary", "continuous"]
            assert isinstance(summary.n_control, int) and summary.n_control > 0
            assert isinstance(summary.n_treatment, int) and summary.n_treatment > 0
            assert isinstance(summary.metric_control, (int, float))
            assert isinstance(summary.metric_treatment, (int, float))
            assert isinstance(summary.p_value, (int, float)) and 0 <= summary.p_value <= 1
            assert isinstance(summary.is_significant, bool)
            assert isinstance(summary.effect_size, (int, float))

    def test_ground_truth_consistency(self, temp_output_dir):
        """Verify ground truth matches generated summaries."""
        summaries, ground_truth = generate_synthetic_corpus(
            n_records=100,
            output_dir=temp_output_dir,
            seed=SEED
        )

        # Create lookup by test_id
        gt_by_id = {gt["test_id"]: gt for gt in ground_truth}

        for summary in summaries:
            assert summary.test_id in gt_by_id, f"Missing ground truth for {summary.test_id}"
            gt = gt_by_id[summary.test_id]

            # Verify sample sizes match
            assert gt["n_control"] == summary.n_control
            assert gt["n_treatment"] == summary.n_treatment

            # Verify outcome type matches
            assert gt["outcome_type"] == summary.outcome_type

    def test_file_outputs_created(self, temp_output_dir):
        """Verify output files are created on disk."""
        summaries, ground_truth = generate_synthetic_corpus(
            n_records=100,
            output_dir=temp_output_dir,
            seed=SEED
        )

        summaries_path = temp_output_dir / "synthetic_summaries.json"
        ground_truth_path = temp_output_dir / "ground_truth.json"
        metadata_path = temp_output_dir / "synthetic_metadata.json"

        assert summaries_path.exists(), "Synthetic summaries file not created"
        assert ground_truth_path.exists(), "Ground truth file not created"
        assert metadata_path.exists(), "Metadata file not created"

        # Verify file contents
        with open(summaries_path, "r") as f:
            data = json.load(f)
            assert len(data) == 100

        with open(ground_truth_path, "r") as f:
            data = json.load(f)
            assert len(data) == 100

    def test_deterministic_generation(self, temp_output_dir):
        """Verify generation is deterministic with same seed."""
        summaries1, gt1 = generate_synthetic_corpus(
            n_records=50,
            output_dir=temp_output_dir / "run1",
            seed=42
        )

        summaries2, gt2 = generate_synthetic_corpus(
            n_records=50,
            output_dir=temp_output_dir / "run2",
            seed=42
        )

        # Compare test IDs and key values
        for s1, s2 in zip(summaries1, summaries2):
            assert s1.test_id == s2.test_id
            assert np.isclose(s1.p_value, s2.p_value)
            assert np.isclose(s1.effect_size, s2.effect_size)

    def test_domain_distribution(self, temp_output_dir):
        """Verify multiple domains are represented."""
        summaries, _ = generate_synthetic_corpus(
            n_records=1000,
            output_dir=temp_output_dir,
            seed=SEED
        )

        domains = set(s.domain for s in summaries)
        assert len(domains) >= 5, f"Expected at least 5 domains, got {len(domains)}"

    def test_year_distribution(self, temp_output_dir):
        """Verify year range is reasonable."""
        summaries, _ = generate_synthetic_corpus(
            n_records=1000,
            output_dir=temp_output_dir,
            seed=SEED
        )

        years = [s.year for s in summaries]
        assert min(years) >= 2018
        assert max(years) <= 2025

    def test_p_value_range(self, temp_output_dir):
        """Verify p-values are in valid range [0, 1]."""
        summaries, _ = generate_synthetic_corpus(
            n_records=100,
            output_dir=temp_output_dir,
            seed=SEED
        )

        for s in summaries:
            assert 0 <= s.p_value <= 1, f"Invalid p-value: {s.p_value}"

    def test_sample_size_constraints(self, temp_output_dir):
        """Verify sample sizes are positive integers."""
        summaries, _ = generate_synthetic_corpus(
            n_records=100,
            output_dir=temp_output_dir,
            seed=SEED
        )

        for s in summaries:
            assert s.n_control > 0
            assert s.n_treatment > 0
            assert isinstance(s.n_control, int)
            assert isinstance(s.n_treatment, int)
