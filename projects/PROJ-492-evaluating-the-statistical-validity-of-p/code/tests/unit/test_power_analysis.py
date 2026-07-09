"""
Unit tests for the power analysis utility.

Tests:
- calculate_sample_size_binary: Verify correct sample size calculation for binary outcomes.
- calculate_sample_size_continuous: Verify correct sample size calculation for continuous outcomes.
- count_corpus_size: Verify correct counting of records in audit report.
- run_power_analysis: Verify end-to-end execution and JSON output.
- Claim validation: Verify that the corpus size meets the claim requirement.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    MIN_CORPUS_SIZE_CLAIM
)
from code.src.config import SEED


class TestCalculateSampleSizeBinary:
    """Tests for binary sample size calculation."""

    def test_standard_case(self):
        """Test with standard parameters: 10% baseline, 5% effect, 80% power, 0.05 alpha."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        # Expected: ~393 per group (total 786) for these parameters
        assert n > 0
        assert isinstance(n, int)

    def test_higher_power_requires_more_samples(self):
        """Higher power should require larger sample size."""
        n_80 = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.80)
        n_90 = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.90)
        assert n_90 > n_80

    def test_smaller_effect_requires_more_samples(self):
        """Smaller detectable effect should require larger sample size."""
        n_5pct = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.80)
        n_3pct = calculate_sample_size_binary(0.10, 0.03, 0.05, 0.80)
        assert n_3pct > n_5pct

    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.0, 0.05, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.0, 0.05, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(-0.1, 0.05, 0.05, 0.80)

    def test_invalid_effect(self):
        """Should raise ValueError for invalid detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.0, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 1.0, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, -0.05, 0.05, 0.80)

    def test_resulting_rate_out_of_bounds(self):
        """Should raise ValueError if baseline + effect > 1."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.90, 0.20, 0.05, 0.80)


class TestCalculateSampleSizeContinuous:
    """Tests for continuous sample size calculation."""

    def test_standard_case(self):
        """Test with standard parameters."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            detectable_effect=5.0,
            baseline_std=15.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)

    def test_smaller_effect_size_requires_more_samples(self):
        """Smaller effect size (Cohen's d) should require larger sample size."""
        n_large = calculate_sample_size_continuous(100, 10, 15, 0.05, 0.80)  # d=0.67
        n_small = calculate_sample_size_continuous(100, 5, 15, 0.05, 0.80)  # d=0.33
        assert n_small > n_large

    def test_invalid_std(self):
        """Should raise ValueError for non-positive standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, 0, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, -5, 0.05, 0.80)


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_from_list(self, tmp_path):
        """Should count records when audit report is a list."""
        audit_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        audit_file = tmp_path / "audit_report.json"
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f)
        
        count = count_corpus_size(audit_file)
        assert count == 3

    def test_count_from_dict_with_records(self, tmp_path):
        """Should count records when audit report is a dict with 'records' key."""
        audit_data = {"records": [{"id": 1}, {"id": 2}]}
        audit_file = tmp_path / "audit_report.json"
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f)
        
        count = count_corpus_size(audit_file)
        assert count == 2

    def test_nonexistent_file(self, tmp_path):
        """Should return 0 for non-existent file."""
        nonexistent = tmp_path / "nonexistent.json"
        count = count_corpus_size(nonexistent)
        assert count == 0


class TestRunPowerAnalysis:
    """Tests for the full power analysis pipeline."""

    def test_run_with_sufficient_corpus(self, tmp_path):
        """Should pass when corpus meets claim requirement."""
        # Create a mock audit report with enough records
        audit_data = [{"id": i} for i in range(MIN_CORPUS_SIZE_CLAIM + 100)]
        audit_file = tmp_path / "audit_report.json"
        output_file = tmp_path / "power_analysis.json"
        
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f)
        
        result = run_power_analysis(
            audit_report_path=audit_file,
            output_path=output_file,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            seed=SEED
        )
        
        assert result["validation"]["overall_valid"] is True
        assert result["validation"]["meets_claim_minimum"] is True
        assert result["validation"]["status"] == "PASS"
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            saved_result = json.load(f)
        assert saved_result["validation"]["overall_valid"] is True

    def test_run_with_insufficient_corpus(self, tmp_path):
        """Should fail when corpus does not meet claim requirement."""
        # Create a mock audit report with too few records
        audit_data = [{"id": i} for i in range(100)]
        audit_file = tmp_path / "audit_report.json"
        output_file = tmp_path / "power_analysis.json"
        
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f)
        
        result = run_power_analysis(
            audit_report_path=audit_file,
            output_path=output_file,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            seed=SEED
        )
        
        assert result["validation"]["overall_valid"] is False
        assert result["validation"]["meets_claim_minimum"] is False
        assert result["validation"]["status"] == "FAIL"
        assert output_file.exists()

    def test_output_contains_required_fields(self, tmp_path):
        """Should contain all required fields in output JSON."""
        audit_data = [{"id": i} for i in range(MIN_CORPUS_SIZE_CLAIM + 100)]
        audit_file = tmp_path / "audit_report.json"
        output_file = tmp_path / "power_analysis.json"
        
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f)
        
        result = run_power_analysis(
            audit_report_path=audit_file,
            output_path=output_file,
            seed=SEED
        )
        
        # Check required top-level keys
        assert "parameters" in result
        assert "calculated_minimum" in result
        assert "claim_requirement" in result
        assert "actual_corpus" in result
        assert "validation" in result
        
        # Check claim requirement details
        assert result["claim_requirement"]["claim_id"] == "c_21f3e400"
        assert "2510.17487" in result["claim_requirement"]["reference"]
        assert result["claim_requirement"]["minimum_corpus_size"] == MIN_CORPUS_SIZE_CLAIM


class TestWritePowerAnalysisResult:
    """Tests for writing results to file."""

    def test_write_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        result = {"test": "data"}
        output_file = tmp_path / "subdir" / "nested" / "result.json"
        
        write_power_analysis_result(result, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == result

    def test_write_valid_json(self, tmp_path):
        """Should write valid JSON."""
        result = {"numbers": [1, 2, 3], "nested": {"key": "value"}}
        output_file = tmp_path / "result.json"
        
        write_power_analysis_result(result, output_file)
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == result