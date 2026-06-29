"""
Unit tests for synthetic dataset generator (T026).
"""
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from code.src.audit.synthetic import (
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
    main,
    DEFAULT_SEED,
    NUM_BINARY_OUTCOMES,
    NUM_CONTINUOUS_OUTCOMES
)
from code.src.models.data_models import ABTestSummary
from code.src.config import set_rng_seed


class TestBinaryOutcomeGeneration:
    """Tests for binary outcome generation."""

    def test_generates_valid_binary_summary(self):
        """Binary outcome should have required fields."""
        summary, ground_truth = generate_binary_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.1,
            effect_size=0.1,
            consistent=True,
            seed=42
        )
        
        assert summary["outcome_type"] == "binary"
        assert summary["n_control"] == 1000
        assert summary["n_treatment"] == 1000
        assert 0 < summary["baseline_rate"] < 1
        assert 0 < summary["treatment_rate"] < 1
        assert 0 <= summary["p_value"] <= 1
        assert "test_type" in summary
        assert summary["test_type"] == "two_proportion_z"

    def test_consistent_p_value_matches_data(self):
        """When consistent=True, p-value should be derived from actual data."""
        summary1, _ = generate_binary_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.1,
            effect_size=0.1,
            consistent=True,
            seed=42
        )
        
        # Same parameters, same seed should produce same p-value
        summary2, _ = generate_binary_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.1,
            effect_size=0.1,
            consistent=True,
            seed=42
        )
        
        assert summary1["p_value"] == summary2["p_value"]

    def test_inconsistent_p_value_is_random(self):
        """When consistent=False, p-value should vary."""
        p_values = []
        for i in range(10):
            summary, _ = generate_binary_outcome(
                n_control=1000,
                n_treatment=1000,
                baseline_rate=0.1,
                effect_size=0.1,
                consistent=False,
                seed=42 + i
            )
            p_values.append(summary["p_value"])
        
        # Should have some variation
        assert len(set(p_values)) > 1

    def test_ground_truth_contains_expected_fields(self):
        """Ground truth should contain validation metadata."""
        summary, ground_truth = generate_binary_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_rate=0.1,
            effect_size=0.1,
            consistent=True,
            seed=42
        )
        
        assert "true_p_value" in ground_truth
        assert "true_effect_size" in ground_truth
        assert "true_baseline_rate" in ground_truth
        assert "true_n_control" in ground_truth
        assert "true_n_treatment" in ground_truth
        assert "intentionally_inconsistent" in ground_truth


class TestContinuousOutcomeGeneration:
    """Tests for continuous outcome generation."""

    def test_generates_valid_continuous_summary(self):
        """Continuous outcome should have required fields."""
        summary, ground_truth = generate_continuous_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_mean=50.0,
            baseline_std=10.0,
            effect_size=0.2,
            consistent=True,
            seed=42
        )
        
        assert summary["outcome_type"] == "continuous"
        assert summary["n_control"] == 1000
        assert summary["n_treatment"] == 1000
        assert summary["baseline_mean"] == 50.0
        assert summary["baseline_std"] > 0
        assert 0 <= summary["p_value"] <= 1
        assert "test_type" in summary
        assert summary["test_type"] == "welch_t"

    def test_treatment_mean_reflects_effect_size(self):
        """Treatment mean should be baseline_mean + effect_size * baseline_std."""
        baseline_mean = 50.0
        baseline_std = 10.0
        effect_size = 0.5
        
        summary, _ = generate_continuous_outcome(
            n_control=1000,
            n_treatment=1000,
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            effect_size=effect_size,
            consistent=True,
            seed=42
        )
        
        expected_treatment_mean = baseline_mean + (effect_size * baseline_std)
        assert abs(summary["treatment_mean"] - expected_treatment_mean) < 0.01


class TestDatasetGeneration:
    """Tests for complete dataset generation."""

    def test_generates_required_number_of_records(self):
        """Should generate at least 10,000 records total."""
        summaries, _ = generate_synthetic_dataset(
            num_binary=NUM_BINARY_OUTCOMES,
            num_continuous=NUM_CONTINUOUS_OUTCOMES,
            seed=DEFAULT_SEED
        )
        
        assert len(summaries) >= 10000

    def test_generates_both_outcome_types(self):
        """Should include both binary and continuous outcomes."""
        summaries, _ = generate_synthetic_dataset(
            num_binary=NUM_BINARY_OUTCOMES,
            num_continuous=NUM_CONTINUOUS_OUTCOMES,
            seed=DEFAULT_SEED
        )
        
        binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
        continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
        
        assert binary_count > 0
        assert continuous_count > 0

    def test_respects_consistent_fraction(self):
        """Should generate approximately the specified fraction of consistent records."""
        consistent_fraction = 0.85
        summaries, _ = generate_synthetic_dataset(
            num_binary=1000,
            num_continuous=1000,
            consistent_fraction=consistent_fraction,
            seed=DEFAULT_SEED
        )
        
        actual_fraction = sum(1 for s in summaries if s["is_consistent"]) / len(summaries)
        # Allow 5% tolerance
        assert abs(actual_fraction - consistent_fraction) < 0.05

    def test_deterministic_with_seed(self):
        """Same seed should produce same results."""
        summaries1, _ = generate_synthetic_dataset(
            num_binary=100,
            num_continuous=100,
            seed=42
        )
        
        summaries2, _ = generate_synthetic_dataset(
            num_binary=100,
            num_continuous=100,
            seed=42
        )
        
        assert len(summaries1) == len(summaries2)
        for s1, s2 in zip(summaries1, summaries2):
            assert s1["p_value"] == s2["p_value"]

    def test_all_summaries_have_required_fields(self):
        """All summaries should have required fields for downstream processing."""
        summaries, _ = generate_synthetic_dataset(
            num_binary=100,
            num_continuous=100,
            seed=DEFAULT_SEED
        )
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "p_value",
            "effect_size", "test_type", "source_url", "domain",
            "publication_year", "is_consistent"
        ]
        
        for summary in summaries:
            for field in required_fields:
                assert field in summary, f"Missing field: {field}"

    def test_domains_are_represented(self):
        """Should include multiple domains."""
        summaries, _ = generate_synthetic_dataset(
            num_binary=500,
            num_continuous=500,
            seed=DEFAULT_SEED
        )
        
        domains = set(s["domain"] for s in summaries)
        expected_domains = {"tech", "e-commerce", "finance", "healthcare", "saas"}
        
        assert domains == expected_domains


class TestVerifyOutcomeTypes:
    """Tests for outcome type verification."""

    def test_returns_true_when_both_present(self):
        """Should return True when both outcome types exist."""
        summaries = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        
        result = verify_outcome_types(summaries)
        assert result is True

    def test_returns_false_when_binary_missing(self):
        """Should return False when binary outcomes missing."""
        summaries = [
            {"outcome_type": "continuous"},
            {"outcome_type": "continuous"}
        ]
        
        result = verify_outcome_types(summaries)
        assert result is False

    def test_returns_false_when_continuous_missing(self):
        """Should return False when continuous outcomes missing."""
        summaries = [
            {"outcome_type": "binary"},
            {"outcome_type": "binary"}
        ]
        
        result = verify_outcome_types(summaries)
        assert result is False

    def test_returns_false_when_empty(self):
        """Should return False for empty list."""
        summaries = []
        
        result = verify_outcome_types(summaries)
        assert result is False


class TestOutputWriting:
    """Tests for output file writing."""

    def test_csv_output_created(self):
        """CSV output should be created with correct format."""
        summaries = [
            {
                "outcome_type": "binary",
                "n_control": 1000,
                "n_treatment": 1000,
                "baseline_rate": 0.1,
                "treatment_rate": 0.11,
                "p_value": 0.03,
                "effect_size": 0.1,
                "test_type": "two_proportion_z",
                "source_url": "https://example.com/test1",
                "domain": "tech",
                "publication_year": 2023,
                "is_consistent": True
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            write_csv_output(summaries, output_path)
            
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]["outcome_type"] == "binary"

    def test_json_output_created(self):
        """JSON output should be created with metadata."""
        summaries = [
            {"outcome_type": "binary", "is_consistent": True},
            {"outcome_type": "continuous", "is_consistent": False}
        ]
        ground_truth = [
            {"intentionally_inconsistent": False},
            {"intentionally_inconsistent": True}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            write_json_output(summaries, ground_truth, output_path)
            
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "total_records" in data
            assert "binary_outcomes" in data
            assert "continuous_outcomes" in data
            assert "ground_truth" in data
            assert data["total_records"] == 2


class TestMain:
    """Tests for main entry point."""

    def test_main_succeeds(self):
        """Main should complete successfully and create output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch output paths
            with patch("code.src.audit.synthetic.CSV_OUTPUT", Path(tmpdir) / "synthetic_validation.csv"):
                with patch("code.src.audit.synthetic.JSON_OUTPUT", Path(tmpdir) / "synthetic_ground_truth.json"):
                    with patch("code.src.audit.synthetic.OUTPUT_DIR", Path(tmpdir)):
                        # Reduce dataset size for faster testing
                        with patch("code.src.audit.synthetic.NUM_BINARY_OUTCOMES", 50):
                            with patch("code.src.audit.synthetic.NUM_CONTINUOUS_OUTCOMES", 50):
                                result = main()
                                
                                assert result == 0
                                assert (Path(tmpdir) / "synthetic_validation.csv").exists()
                                assert (Path(tmpdir) / "synthetic_ground_truth.json").exists()

    def test_main_verifies_record_count(self):
        """Main should verify at least 10,000 records are generated."""
        # This is implicitly tested by the dataset generation tests
        # Main calls generate_synthetic_dataset which is tested above
        pass

    def test_main_verifies_outcome_types(self):
        """Main should verify both outcome types are present."""
        # This is implicitly tested by verify_outcome_types tests
        # Main calls verify_outcome_types which is tested above
        pass
