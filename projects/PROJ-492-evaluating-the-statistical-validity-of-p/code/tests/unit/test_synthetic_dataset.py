"""
Unit tests for synthetic dataset generator (T026).
Verifies generation of at least 10,000 records with both binary and continuous outcomes.
"""
import json
import csv
import pytest
from pathlib import Path
import shutil
import tempfile

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_sample_sizes
)
from code.src.config import SEED


class TestSyntheticDatasetGenerator:
    """Test suite for synthetic dataset generation."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_minimum_record_count(self, temp_output_dir):
        """Verify that at least 10,000 records are generated."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            output_dir=temp_output_dir
        )
        
        assert len(summaries) >= 10000, \
            f"Expected at least 10,000 records, got {len(summaries)}"

    def test_binary_outcomes_present(self, temp_output_dir):
        """Verify that binary outcomes are present in the dataset."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )
        
        binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
        assert binary_count > 0, "No binary outcomes generated"
        
        # Check that binary outcomes have required fields
        binary_summaries = [s for s in summaries if s["outcome_type"] == "binary"]
        for summary in binary_summaries[:5]:  # Check first 5
            assert "rate_control" in summary
            assert "rate_treatment" in summary
            assert "conversions_control" in summary
            assert "conversions_treatment" in summary

    def test_continuous_outcomes_present(self, temp_output_dir):
        """Verify that continuous outcomes are present in the dataset."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )
        
        continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
        assert continuous_count > 0, "No continuous outcomes generated"
        
        # Check that continuous outcomes have required fields
        continuous_summaries = [s for s in summaries if s["outcome_type"] == "continuous"]
        for summary in continuous_summaries[:5]:  # Check first 5
            assert "mean_control" in summary
            assert "mean_treatment" in summary
            assert "std_control" in summary
            assert "std_treatment" in summary

    def test_both_outcome_types_verified(self, temp_output_dir):
        """Verify that both outcome types are present using verification function."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=temp_output_dir
        )
        
        # This should not raise an exception
        verify_outcome_types(summaries)

    def test_csv_output_created(self, temp_output_dir):
        """Verify that CSV output file is created and contains data."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            output_dir=temp_output_dir
        )
        
        csv_path = temp_output_dir / "synthetic_summaries.csv"
        assert csv_path.exists(), "CSV output file not created"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) >= 10000, f"CSV contains {len(rows)} rows, expected >= 10000"

    def test_json_output_created(self, temp_output_dir):
        """Verify that JSON output file is created and contains data."""
        summaries = generate_synthetic_dataset(
            total_records=10000,
            output_dir=temp_output_dir
        )
        
        json_path = temp_output_dir / "synthetic_summaries.json"
        assert json_path.exists(), "JSON output file not created"
        
        with open(json_path, 'r') as f:
            loaded_summaries = json.load(f)
        
        assert len(loaded_summaries) >= 10000, \
            f"JSON contains {len(loaded_summaries)} records, expected >= 10000"

    def test_sample_size_generation(self):
        """Test sample size generation function."""
        for _ in range(10):
            n_control, n_treatment = generate_sample_sizes()
            assert n_control >= 100, "Control sample size too small"
            assert n_treatment >= 80, "Treatment sample size too small"
            assert n_control <= 10000, "Control sample size too large"
            assert n_treatment <= 12000, "Treatment sample size too large"

    def test_binary_outcome_generation(self):
        """Test binary outcome generation function."""
        n_control, n_treatment = 1000, 1200
        baseline_rate = 0.15
        effect_size = 0.05
        
        result = generate_binary_outcome(n_control, n_treatment, baseline_rate, effect_size)
        
        assert result["n_control"] == n_control
        assert result["n_treatment"] == n_treatment
        assert 0 <= result["rate_control"] <= 1
        assert 0 <= result["rate_treatment"] <= 1
        assert 0 <= result["p_value"] <= 1
        assert result["outcome_type"] == "binary"

    def test_continuous_outcome_generation(self):
        """Test continuous outcome generation function."""
        n_control, n_treatment = 1000, 1200
        baseline_mean = 50.0
        baseline_std = 15.0
        effect_size = 2.0
        
        result = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size
        )
        
        assert result["n_control"] == n_control
        assert result["n_treatment"] == n_treatment
        assert result["mean_control"] > 0
        assert result["mean_treatment"] > 0
        assert result["std_control"] > 0
        assert result["std_treatment"] > 0
        assert 0 <= result["p_value"] <= 1
        assert result["outcome_type"] == "continuous"

    def test_reproducibility(self, temp_output_dir):
        """Test that generation is reproducible with the same seed."""
        summaries1 = generate_synthetic_dataset(
            total_records=100,
            output_dir=temp_output_dir / "run1"
        )
        
        summaries2 = generate_synthetic_dataset(
            total_records=100,
            output_dir=temp_output_dir / "run2"
        )
        
        # Compare first few records
        for i in range(5):
            assert summaries1[i]["id"] == summaries2[i]["id"]
            assert summaries1[i]["p_value"] == summaries2[i]["p_value"]

    def test_record_structure(self, temp_output_dir):
        """Verify that each record has the required structure."""
        summaries = generate_synthetic_dataset(
            total_records=100,
            output_dir=temp_output_dir
        )
        
        required_fields = [
            "id", "url", "domain", "year", "outcome_type",
            "n_control", "n_treatment", "p_value", "effect_size",
            "is_significant", "generated_at"
        ]
        
        for summary in summaries[:10]:
            for field in required_fields:
                assert field in summary, f"Missing field: {field}"

    def test_domain_distribution(self, temp_output_dir):
        """Verify that multiple domains are represented."""
        summaries = generate_synthetic_dataset(
            total_records=1000,
            output_dir=temp_output_dir
        )
        
        domains = set(s["domain"] for s in summaries)
        assert len(domains) >= 5, f"Expected at least 5 domains, got {len(domains)}"

    def test_year_distribution(self, temp_output_dir):
        """Verify that multiple years are represented."""
        summaries = generate_synthetic_dataset(
            total_records=1000,
            output_dir=temp_output_dir
        )
        
        years = set(s["year"] for s in summaries)
        assert len(years) >= 5, f"Expected at least 5 years, got {len(years)}"
        assert all(2018 <= y <= 2024 for y in years), "Year out of expected range"
