"""
Unit tests for the synthetic dataset generator (T026).
"""
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np
from scipy import stats

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_binary_outcome_data,
    generate_continuous_outcome_data,
    generate_synthetic_record,
    generate_dataset,
    MIN_N_RECORDS
)
from code.src.models.data_models import ABTestSummary


class TestSyntheticGenerator(TestCase):
    """Tests for synthetic data generation logic."""

    def test_binary_outcome_generation(self):
        """Test that binary outcome data is generated with valid ranges."""
        data = generate_binary_outcome_data(
            n=1000,
            baseline_rate=0.1,
            effect_size_rel=0.1,
            is_inconsistent=False
        )

        self.assertEqual(data["outcome_type"], "binary")
        self.assertGreater(data["n_control"], 0)
        self.assertGreater(data["n_treatment"], 0)
        self.assertGreaterEqual(data["baseline_rate"], 0)
        self.assertLessEqual(data["baseline_rate"], 1)
        self.assertGreaterEqual(data["treatment_rate"], 0)
        self.assertLessEqual(data["treatment_rate"], 1)
        self.assertGreaterEqual(data["true_p_value"], 0)
        self.assertLessEqual(data["true_p_value"], 1)

    def test_continuous_outcome_generation(self):
        """Test that continuous outcome data is generated with valid ranges."""
        data = generate_continuous_outcome_data(
            n=1000,
            baseline_mean=50.0,
            effect_size_rel=0.1,
            std_dev=10.0,
            is_inconsistent=False
        )

        self.assertEqual(data["outcome_type"], "continuous")
        self.assertGreater(data["n_control"], 0)
        self.assertGreater(data["n_treatment"], 0)
        self.assertGreater(data["baseline_mean"], 0)
        self.assertGreater(data["treatment_mean"], 0)
        self.assertGreater(data["baseline_std"], 0)
        self.assertGreater(data["treatment_std"], 0)
        self.assertGreaterEqual(data["true_p_value"], 0)
        self.assertLessEqual(data["true_p_value"], 1)

    def test_inconsistency_injection(self):
        """Test that inconsistency is correctly injected."""
        # P-value inconsistency
        data = generate_binary_outcome_data(
            n=10000,
            baseline_rate=0.2,
            effect_size_rel=0.2,
            is_inconsistent=True,
            inconsistency_type="p_value"
        )

        self.assertTrue(data["is_inconsistent"])
        self.assertEqual(data["inconsistency_reason"], "p_value")

        # The reported p-value should differ significantly from true p-value
        diff = abs(data["reported_p_value"] - data["true_p_value"])
        # We expect a large difference, though exact value depends on random seed
        self.assertGreater(diff, 0.05)

    def test_record_generation(self):
        """Test that ABTestSummary records are generated correctly."""
        record = generate_synthetic_record(
            record_id=1,
            is_inconsistent=False,
            outcome_type="binary"
        )

        self.assertIsInstance(record, ABTestSummary)
        self.assertEqual(record.outcome_type, "binary")
        self.assertIsNotNone(record.id)
        self.assertIsNotNone(record.url)
        self.assertIsNotNone(record.domain)

    def test_dataset_generation_count(self):
        """Test that the dataset generates at least MIN_N_RECORDS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_dataset(output_dir, n_records=MIN_N_RECORDS)

            json_path = output_dir / "synthetic_summaries.json"
            csv_path = output_dir / "synthetic_summaries.csv"

            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())

            # Check JSON count
            with open(json_path, "r") as f:
                data = json.load(f)
            self.assertGreaterEqual(len(data), MIN_N_RECORDS)

            # Check CSV count
            with open(csv_path, "r") as f:
                reader = csv.reader(f)
                rows = list(reader)
            # Subtract header
            self.assertGreaterEqual(len(rows) - 1, MIN_N_RECORDS)

    def test_dataset_mixed_outcomes(self):
        """Test that dataset contains both binary and continuous outcomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_dataset(output_dir, n_records=200)

            json_path = output_dir / "synthetic_summaries.json"
            with open(json_path, "r") as f:
                data = json.load(f)

            outcome_types = set(r["outcome_type"] for r in data)
            self.assertIn("binary", outcome_types)
            self.assertIn("continuous", outcome_types)

    def test_statistical_validity_binary(self):
        """Verify that generated binary data follows binomial distribution properties."""
        # Generate many records with same params and check mean/variance
        n = 1000
        p = 0.2
        trials = 50

        observed_rates = []
        for _ in range(trials):
            data = generate_binary_outcome_data(
                n=n,
                baseline_rate=p,
                effect_size_rel=0.0, # No effect
                is_inconsistent=False
            )
            observed_rates.append(data["baseline_rate"])

        # Mean should be close to p
        mean_rate = np.mean(observed_rates)
        self.assertAlmostEqual(mean_rate, p, delta=0.02)

        # Variance should be close to p(1-p)/n
        expected_var = p * (1 - p) / n
        observed_var = np.var(observed_rates)
        self.assertAlmostEqual(observed_var, expected_var, delta=0.0001)

    def test_statistical_validity_continuous(self):
        """Verify that generated continuous data follows normal distribution properties."""
        n = 1000
        mu = 50.0
        sigma = 10.0
        trials = 50

        observed_means = []
        for _ in range(trials):
            data = generate_continuous_outcome_data(
                n=n,
                baseline_mean=mu,
                effect_size_rel=0.0,
                std_dev=sigma,
                is_inconsistent=False
            )
            observed_means.append(data["baseline_mean"])

        # Mean should be close to mu
        mean_val = np.mean(observed_means)
        self.assertAlmostEqual(mean_val, mu, delta=1.0)

        # Std dev should be close to sigma/sqrt(n)
        expected_std = sigma / math.sqrt(n)
        observed_std = np.std(observed_means)
        self.assertAlmostEqual(observed_std, expected_std, delta=0.5)

    def test_p_value_distribution_under_null(self):
        """Test that p-values are uniformly distributed under the null hypothesis."""
        # Generate data with no effect (effect_size_rel = 0)
        p_values = []
        for _ in range(1000):
            data = generate_binary_outcome_data(
                n=1000,
                baseline_rate=0.2,
                effect_size_rel=0.0,
                is_inconsistent=False
            )
            p_values.append(data["true_p_value"])

        # Check proportion of p < 0.05 (should be ~0.05)
        significant_count = sum(1 for p in p_values if p < 0.05)
        proportion = significant_count / len(p_values)
        # Allow some variance (0.05 +/- 0.02)
        self.assertGreaterEqual(proportion, 0.03)
        self.assertLessEqual(proportion, 0.07)
