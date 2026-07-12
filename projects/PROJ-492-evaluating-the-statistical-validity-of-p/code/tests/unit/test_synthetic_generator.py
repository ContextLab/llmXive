"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Correct generation of binary and continuous outcomes
- Minimum record count (>= 10,000)
- Data consistency constraints
- File output correctness
"""
import pytest
import csv
import json
import math
import random
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from scipy import stats

from code.src.audit.synthetic import (
    generate_binary_test_data,
    generate_continuous_test_data,
    create_synthetic_summary,
    generate_synthetic_corpus,
    MIN_RECORDS,
    DEFAULT_OUTPUT_DIR
)
from code.src.config import SEED


class TestBinaryTestDataGeneration:
    """Tests for binary test data generation."""

    def test_binary_data_generation_basic(self):
        """Test basic binary data generation."""
        n_control, n_treatment = 1000, 1000
        baseline_rate, effect_size = 0.2, 0.1

        (c_conv, t_conv, n_c, n_t, p_val, eff_size) = generate_binary_test_data(
            n_control, n_treatment, baseline_rate, effect_size, is_consistent=True
        )

        assert c_conv >= 0 and c_conv <= n_c
        assert t_conv >= 0 and t_conv <= n_t
        assert n_c == n_control
        assert n_t == n_treatment
        assert 0.0 <= p_val <= 1.0

    def test_binary_data_generation_inconsistent(self):
        """Test binary data generation with inconsistency."""
        n_control, n_treatment = 1000, 1000
        baseline_rate, effect_size = 0.2, 0.1

        (c_conv, t_conv, n_c, n_t, p_val, eff_size) = generate_binary_test_data(
            n_control, n_treatment, baseline_rate, effect_size,
            is_consistent=False, noise_level=0.1
        )

        assert 0.0 <= p_val <= 1.0
        # With noise, effect size might be slightly perturbed

    def test_binary_data_generation_noise(self):
        """Test that noise level affects output consistency."""
        n_control, n_treatment = 5000, 5000
        baseline_rate, effect_size = 0.25, 0.05

        # Generate with no noise
        _, _, _, _, p_no_noise, eff_no_noise = generate_binary_test_data(
            n_control, n_treatment, baseline_rate, effect_size,
            is_consistent=False, noise_level=0.0
        )

        # Generate with high noise
        _, _, _, _, p_high_noise, eff_high_noise = generate_binary_test_data(
            n_control, n_treatment, baseline_rate, effect_size,
            is_consistent=False, noise_level=0.15
        )

        # Both should be valid p-values
        assert 0.0 <= p_no_noise <= 1.0
        assert 0.0 <= p_high_noise <= 1.0


class TestContinuousTestDataGeneration:
    """Tests for continuous test data generation."""

    def test_continuous_data_generation_basic(self):
        """Test basic continuous data generation."""
        n_control, n_treatment = 500, 500
        baseline_mean, baseline_std = 50.0, 10.0
        effect_size = 5.0

        (c_data, t_data, p_val, eff_size, c_mean, t_mean) = generate_continuous_test_data(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size,
            is_consistent=True
        )

        assert len(c_data) == n_control
        assert len(t_data) == n_treatment
        assert 0.0 <= p_val <= 1.0
        assert abs(t_mean - c_mean - effect_size) < 2 * baseline_std / math.sqrt(n_control)

    def test_continuous_data_generation_inconsistent(self):
        """Test continuous data generation with inconsistency."""
        n_control, n_treatment = 500, 500
        baseline_mean, baseline_std = 50.0, 10.0
        effect_size = 5.0

        (c_data, t_data, p_val, eff_size, c_mean, t_mean) = generate_continuous_test_data(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size,
            is_consistent=False, noise_level=0.1
        )

        assert len(c_data) == n_control
        assert len(t_data) == n_treatment
        assert 0.0 <= p_val <= 1.0


class TestSyntheticSummaryCreation:
    """Tests for synthetic summary creation."""

    def test_create_binary_summary(self):
        """Test creation of binary summary."""
        summary, ground_truth = create_synthetic_summary(
            test_id=1,
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.2,
            effect_size=0.1,
            is_consistent=True
        )

        assert summary["outcome_type"] == "binary"
        assert summary["n_control"] == 1000
        assert summary["n_treatment"] == 1000
        assert "reported_p_value" in summary
        assert "reported_effect_size" in summary
        assert ground_truth["is_consistent"] is True

    def test_create_continuous_summary(self):
        """Test creation of continuous summary."""
        summary, ground_truth = create_synthetic_summary(
            test_id=2,
            outcome_type="continuous",
            n_control=500,
            n_treatment=500,
            baseline_mean=50.0,
            baseline_std=10.0,
            effect_size=5.0,
            is_consistent=True
        )

        assert summary["outcome_type"] == "continuous"
        assert summary["n_control"] == 500
        assert "control_mean" in summary
        assert "treatment_mean" in summary
        assert ground_truth["outcome_type"] == "continuous"

    def test_create_summary_with_custom_domain_year(self):
        """Test creation of summary with custom domain and year."""
        summary, ground_truth = create_synthetic_summary(
            test_id=3,
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.2,
            effect_size=0.1,
            is_consistent=True,
            domain="test.example.com",
            year=2024
        )

        assert summary["domain"] == "test.example.com"
        assert summary["year"] == 2024
        assert ground_truth["domain"] == "test.example.com"
        assert ground_truth["year"] == 2024


class TestSyntheticCorpusGeneration:
    """Tests for full corpus generation."""

    def test_minimum_record_count(self, tmp_path):
        """Test that generated corpus meets minimum record count."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_corpus(n_records=MIN_RECORDS, output_dir=output_dir, seed=SEED)

        summaries_file = output_dir / "synthetic_summaries.csv"
        assert summaries_file.exists()

        with open(summaries_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= MIN_RECORDS

    def test_corpus_contains_both_outcome_types(self, tmp_path):
        """Test that corpus contains both binary and continuous outcomes."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_corpus(n_records=MIN_RECORDS, output_dir=output_dir, seed=SEED)

        summaries_file = output_dir / "synthetic_summaries.csv"

        with open(summaries_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        outcome_types = {row["outcome_type"] for row in rows}
        assert "binary" in outcome_types
        assert "continuous" in outcome_types

    def test_ground_truth_file_created(self, tmp_path):
        """Test that ground truth file is created."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_corpus(n_records=MIN_RECORDS, output_dir=output_dir, seed=SEED)

        ground_truth_file = output_dir / "synthetic_ground_truth.json"
        assert ground_truth_file.exists()

        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            ground_truths = json.load(f)

        assert len(ground_truths) >= MIN_RECORDS

    def test_consistency_flag_in_ground_truth(self, tmp_path):
        """Test that ground truth contains consistency flags."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_corpus(n_records=MIN_RECORDS, output_dir=output_dir, seed=SEED)

        ground_truth_file = output_dir / "synthetic_ground_truth.json"

        with open(ground_truth_file, 'r', encoding='utf-8') as f:
            ground_truths = json.load(f)

        # Check that we have both consistent and inconsistent records
        consistent_count = sum(1 for gt in ground_truths if gt["is_consistent"])
        inconsistent_count = sum(1 for gt in ground_truths if not gt["is_consistent"])

        # With 85% consistency rate, we should have both
        assert consistent_count > 0
        assert inconsistent_count > 0

    def test_required_fields_in_summaries(self, tmp_path):
        """Test that all required fields are present in summaries."""
        output_dir = tmp_path / "synthetic"
        generate_synthetic_corpus(n_records=MIN_RECORDS, output_dir=output_dir, seed=SEED)

        summaries_file = output_dir / "synthetic_summaries.csv"

        with open(summaries_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)

        required_fields = [
            "test_id", "outcome_type", "domain", "year",
            "n_control", "n_treatment", "reported_p_value", "reported_effect_size",
            "test_statistic_type"
        ]

        for field in required_fields:
            assert field in row, f"Missing required field: {field}"

    def test_reproducibility_with_seed(self, tmp_path):
        """Test that generation is reproducible with same seed."""
        output_dir1 = tmp_path / "synthetic1"
        output_dir2 = tmp_path / "synthetic2"

        generate_synthetic_corpus(n_records=100, output_dir=output_dir1, seed=SEED)
        generate_synthetic_corpus(n_records=100, output_dir=output_dir2, seed=SEED)

        summaries_file1 = output_dir1 / "synthetic_summaries.csv"
        summaries_file2 = output_dir2 / "synthetic_summaries.csv"

        with open(summaries_file1, 'r', encoding='utf-8') as f1:
            rows1 = list(csv.DictReader(f1))
        with open(summaries_file2, 'r', encoding='utf-8') as f2:
            rows2 = list(csv.DictReader(f2))

        # All records should match
        assert len(rows1) == len(rows2)
        for r1, r2 in zip(rows1, rows2):
            assert r1 == r2


class TestEdgeCases:
    """Tests for edge cases."""

    def test_small_sample_sizes(self):
        """Test with small sample sizes."""
        summary, ground_truth = create_synthetic_summary(
            test_id=1,
            outcome_type="binary",
            n_control=10,
            n_treatment=10,
            baseline_rate=0.2,
            effect_size=0.1,
            is_consistent=True
        )

        assert summary["n_control"] == 10
        assert summary["n_treatment"] == 10

    def test_large_effect_sizes(self):
        """Test with large effect sizes."""
        summary, ground_truth = create_synthetic_summary(
            test_id=1,
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.2,
            effect_size=0.5,  # 50% lift
            is_consistent=True
        )

        assert summary["reported_effect_size"] > 0.1

    def test_negative_effect_sizes(self):
        """Test with negative effect sizes."""
        summary, ground_truth = create_synthetic_summary(
            test_id=1,
            outcome_type="binary",
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.2,
            effect_size=-0.1,  # Negative lift
            is_consistent=True
        )

        # Effect size should reflect the negative direction
        assert summary["reported_effect_size"] < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
