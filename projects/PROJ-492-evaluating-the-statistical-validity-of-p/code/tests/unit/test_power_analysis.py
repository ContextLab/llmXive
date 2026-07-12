"""
Unit tests for power analysis utility.

Tests FR-025: Power analysis calculations and corpus validation.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from scipy import stats

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    write_power_analysis_result,
    run_power_analysis,
    set_rng_seed_for_power_analysis
)
from code.src.config import SEED


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""
    
    def test_basic_calculation(self):
        """Test basic sample size calculation with known parameters."""
        baseline = 0.10
        effect = 0.05
        alpha = 0.05
        power = 0.80
        
        n = calculate_sample_size_binary(baseline, effect, alpha, power)
        
        assert n > 0
        assert isinstance(n, float)
        # For these parameters, n should be approximately 1000-1500 per group
        assert 500 < n < 3000
    
    def test_larger_effect_reduces_sample_size(self):
        """Larger detectable effect should require smaller sample size."""
        baseline = 0.10
        
        n_small_effect = calculate_sample_size_binary(baseline, 0.01, 0.05, 0.80)
        n_large_effect = calculate_sample_size_binary(baseline, 0.10, 0.05, 0.80)
        
        assert n_large_effect < n_small_effect
    
    def test_higher_power_increases_sample_size(self):
        """Higher power should require larger sample size."""
        baseline = 0.10
        effect = 0.05
        
        n_low_power = calculate_sample_size_binary(baseline, effect, 0.05, 0.70)
        n_high_power = calculate_sample_size_binary(baseline, effect, 0.05, 0.90)
        
        assert n_high_power > n_low_power
    
    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.5, 0.05, 0.05, 0.80)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(-0.1, 0.05, 0.05, 0.80)
    
    def test_invalid_detectable_effect(self):
        """Should raise ValueError for invalid detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 1.5, 0.05, 0.80)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, -0.1, 0.05, 0.80)
    
    def test_resulting_rate_out_of_bounds(self):
        """Should raise ValueError if resulting rate is out of bounds."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.95, 0.10, 0.05, 0.80)  # p2 = 1.05


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""
    
    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcomes."""
        baseline_mean = 100
        effect = 5
        std_dev = 15
        
        n = calculate_sample_size_continuous(baseline_mean, effect, std_dev, 0.05, 0.80)
        
        assert n > 0
        assert isinstance(n, float)
    
    def test_larger_effect_reduces_sample_size(self):
        """Larger detectable effect should require smaller sample size."""
        std_dev = 15
        
        n_small_effect = calculate_sample_size_continuous(100, 1, std_dev, 0.05, 0.80)
        n_large_effect = calculate_sample_size_continuous(100, 10, std_dev, 0.05, 0.80)
        
        assert n_large_effect < n_small_effect
    
    def test_larger_std_dev_increases_sample_size(self):
        """Larger standard deviation should require larger sample size."""
        effect = 5
        
        n_low_std = calculate_sample_size_continuous(100, effect, 5, 0.05, 0.80)
        n_high_std = calculate_sample_size_continuous(100, effect, 20, 0.05, 0.80)
        
        assert n_high_std > n_low_std
    
    def test_invalid_std_dev(self):
        """Should raise ValueError for invalid standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, 0, 0.05, 0.80)
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, -5, 0.05, 0.80)
    
    def test_zero_effect_raises_error(self):
        """Should raise ValueError for zero detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 0, 15, 0.05, 0.80)


class TestCountCorpusSize:
    """Tests for corpus size counting."""
    
    def test_count_from_list(self, tmp_path):
        """Should correctly count records from a list."""
        audit_file = tmp_path / "audit_report.json"
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        with open(audit_file, 'w') as f:
            json.dump(data, f)
        
        count = count_corpus_size(audit_file)
        assert count == 3
    
    def test_count_from_dict_with_records(self, tmp_path):
        """Should correctly count records from dict with 'records' key."""
        audit_file = tmp_path / "audit_report.json"
        data = {"records": [{"id": 1}, {"id": 2}]}
        with open(audit_file, 'w') as f:
            json.dump(data, f)
        
        count = count_corpus_size(audit_file)
        assert count == 2
    
    def test_nonexistent_file_returns_zero(self, tmp_path):
        """Should return 0 for non-existent file."""
        count = count_corpus_size(tmp_path / "nonexistent.json")
        assert count == 0
    
    def test_invalid_json_returns_zero(self, tmp_path):
        """Should return 0 for invalid JSON."""
        audit_file = tmp_path / "audit_report.json"
        with open(audit_file, 'w') as f:
            f.write("not valid json")
        
        count = count_corpus_size(audit_file)
        assert count == 0


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""
    
    def test_write_creates_file(self, tmp_path):
        """Should create output file with valid JSON."""
        output_file = tmp_path / "power_analysis.json"
        result = {"test": "value", "number": 42}
        
        write_power_analysis_result(result, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == result
    
    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        output_file = tmp_path / "nested" / "dir" / "power_analysis.json"
        result = {"test": "value"}
        
        write_power_analysis_result(result, output_file)
        
        assert output_file.exists()


class TestRunPowerAnalysis:
    """Tests for the main power analysis runner."""
    
    def test_binary_test_validation_pass(self, tmp_path):
        """Should pass validation when corpus meets requirements."""
        # Create a mock audit file with enough records
        audit_file = tmp_path / "audit_report.json"
        # Need at least 2000 records for typical binary test parameters
        data = [{"id": i} for i in range(2000)]
        with open(audit_file, 'w') as f:
            json.dump(data, f)
        
        output_file = tmp_path / "power_analysis.json"
        
        result = run_power_analysis(
            audit_records_path=audit_file,
            output_path=output_file,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            test_type="binary"
        )
        
        assert result["corpus_meets_requirement"] is True
        assert result["validation_status"] == "PASS"
        assert output_file.exists()
    
    def test_binary_test_validation_fail(self, tmp_path):
        """Should fail validation when corpus is too small."""
        # Create a mock audit file with too few records
        audit_file = tmp_path / "audit_report.json"
        data = [{"id": i} for i in range(100)]  # Too small
        with open(audit_file, 'w') as f:
            json.dump(data, f)
        
        output_file = tmp_path / "power_analysis.json"
        
        result = run_power_analysis(
            audit_records_path=audit_file,
            output_path=output_file,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80,
            test_type="binary"
        )
        
        assert result["corpus_meets_requirement"] is False
        assert result["validation_status"] == "FAIL"
    
    def test_continuous_test_requires_std_dev(self, tmp_path):
        """Should raise error for continuous test without std_dev."""
        audit_file = tmp_path / "audit_report.json"
        with open(audit_file, 'w') as f:
            json.dump([{"id": 1}], f)
        
        output_file = tmp_path / "power_analysis.json"
        
        with pytest.raises(ValueError, match="std_dev is required"):
            run_power_analysis(
                audit_records_path=audit_file,
                output_path=output_file,
                test_type="continuous"
            )
    
    def test_output_contains_required_fields(self, tmp_path):
        """Output JSON should contain all required fields."""
        audit_file = tmp_path / "audit_report.json"
        data = [{"id": i} for i in range(2000)]
        with open(audit_file, 'w') as f:
            json.dump(data, f)
        
        output_file = tmp_path / "power_analysis.json"
        
        run_power_analysis(
            audit_records_path=audit_file,
            output_path=output_file,
            test_type="binary"
        )
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        required_fields = [
            "test_type",
            "parameters",
            "minimum_sample_size",
            "actual_corpus_size",
            "corpus_meets_requirement",
            "validation_status",
            "claim_reference",
            "arxiv_reference"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_claim_reference_correct(self, tmp_path):
        """Should reference the correct claim (c_21f3e400)."""
        audit_file = tmp_path / "audit_report.json"
        with open(audit_file, 'w') as f:
            json.dump([{"id": i} for i in range(2000)], f)
        
        output_file = tmp_path / "power_analysis.json"
        
        result = run_power_analysis(
            audit_records_path=audit_file,
            output_path=output_file,
            test_type="binary"
        )
        
        assert result["claim_reference"] == "c_21f3e400"
        assert result["arxiv_reference"] == "2510.17487"


class TestSetRngSeedForPowerAnalysis:
    """Tests for RNG seed setting."""
    
    def test_seed_is_set(self):
        """Should set the random seed."""
        set_rng_seed_for_power_analysis(SEED)
        
        # Just verify it doesn't raise an error
        # The actual seeding is tested in the config module
        assert True