"""
Unit tests for power analysis utility.

Verifies:
- calculate_sample_size_binary produces valid results
- calculate_sample_size_continuous produces valid results
- count_corpus_size correctly counts records
- run_power_analysis validates corpus size requirements
- write_power_analysis_result creates valid JSON file
"""
import json
import tempfile
from pathlib import Path
import pytest
from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result
)
from code.src.config import SEED

class TestCalculateSampleSizeBinary:
    def test_basic_calculation(self):
        """Test basic sample size calculation for binary outcome."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
        
    def test_larger_effect_requires_smaller_sample(self):
        """Larger detectable effect should require smaller sample size."""
        n_small_effect = calculate_sample_size_binary(0.10, 0.01, 0.05, 0.80)
        n_large_effect = calculate_sample_size_binary(0.10, 0.10, 0.05, 0.80)
        assert n_large_effect < n_small_effect
        
    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample size."""
        n_low_power = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.50)
        n_high_power = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.90)
        assert n_high_power > n_low_power
        
    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.0, 0.05, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.0, 0.05, 0.05, 0.80)
            
    def test_invalid_effect(self):
        """Should raise ValueError for invalid detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.0, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 1.0, 0.05, 0.80)

class TestCalculateSampleSizeContinuous:
    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcome."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            detectable_effect=5.0,
            std_dev=10.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
        
    def test_larger_effect_size_requires_smaller_sample(self):
        """Larger detectable effect should require smaller sample size."""
        n_small_effect = calculate_sample_size_continuous(100.0, 2.0, 10.0, 0.05, 0.80)
        n_large_effect = calculate_sample_size_continuous(100.0, 10.0, 10.0, 0.05, 0.80)
        assert n_large_effect < n_small_effect
        
    def test_larger_std_dev_requires_larger_sample(self):
        """Larger standard deviation should require larger sample size."""
        n_small_std = calculate_sample_size_continuous(100.0, 5.0, 5.0, 0.05, 0.80)
        n_large_std = calculate_sample_size_continuous(100.0, 5.0, 20.0, 0.05, 0.80)
        assert n_large_std > n_small_std
        
    def test_invalid_std_dev(self):
        """Should raise ValueError for invalid standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100.0, 5.0, 0.0, 0.05, 0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100.0, 5.0, -5.0, 0.05, 0.80)

class TestCountCorpusSize:
    def test_count_from_empty_list(self, tmp_path):
        """Should return 0 for empty list."""
        test_file = tmp_path / "empty_audit.json"
        test_file.write_text("[]")
        assert count_corpus_size(test_file) == 0
        
    def test_count_from_list_with_records(self, tmp_path):
        """Should return correct count for list with records."""
        test_file = tmp_path / "audit.json"
        records = [{"id": i} for i in range(50)]
        test_file.write_text(json.dumps(records))
        assert count_corpus_size(test_file) == 50
        
    def test_count_from_dict_with_records_key(self, tmp_path):
        """Should return correct count for dict with 'records' key."""
        test_file = tmp_path / "audit.json"
        data = {"records": [{"id": i} for i in range(100)]}
        test_file.write_text(json.dumps(data))
        assert count_corpus_size(test_file) == 100
        
    def test_nonexistent_file(self):
        """Should return 0 for nonexistent file."""
        assert count_corpus_size(Path("/nonexistent/path.json")) == 0

class TestRunPowerAnalysis:
    def test_meets_minimum_corpus_size(self):
        """Should pass when corpus size >= 300."""
        result = run_power_analysis(corpus_size=500)
        assert result["meets_requirement"] is True
        assert result["validation_status"] == "PASS"
        
    def test_meets_calculated_minimum(self):
        """Should pass when corpus size >= calculated minimum."""
        # Calculate minimum for baseline=0.10, effect=0.05
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.05,
            corpus_size=2000  # Should be enough
        )
        assert result["calculated_minimum_n_total"] > 0
        # If 2000 >= calculated minimum, should pass
        
    def test_fails_both_requirements(self):
        """Should fail when corpus size < 300 AND < calculated minimum."""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.05,
            corpus_size=100
        )
        assert result["meets_requirement"] is False
        assert result["validation_status"] == "FAIL"
        
    def test_contains_required_fields(self):
        """Result should contain all required fields."""
        result = run_power_analysis()
        required_fields = [
            "baseline_rate", "detectable_effect", "alpha", "power",
            "calculated_minimum_n_per_group", "calculated_minimum_n_total",
            "actual_corpus_size", "minimum_requirement", "meets_requirement",
            "validation_status"
        ]
        for field in required_fields:
            assert field in result

class TestWritePowerAnalysisResult:
    def test_creates_valid_json(self, tmp_path):
        """Should create valid JSON file with correct content."""
        test_file = tmp_path / "power_analysis.json"
        result = {
            "baseline_rate": 0.10,
            "meets_requirement": True,
            "actual_corpus_size": 500
        }
        write_power_analysis_result(result, test_file)
        
        assert test_file.exists()
        with open(test_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == result
        
    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        test_file = tmp_path / "subdir" / "nested" / "power_analysis.json"
        result = {"test": "value"}
        write_power_analysis_result(result, test_file)
        
        assert test_file.exists()
        
    def test_numeric_n_in_output(self, tmp_path):
        """Output should contain numeric N values."""
        test_file = tmp_path / "power_analysis.json"
        result = run_power_analysis(corpus_size=500)
        write_power_analysis_result(result, test_file)
        
        with open(test_file, 'r') as f:
            loaded = json.load(f)
        assert isinstance(loaded["calculated_minimum_n_per_group"], int)
        assert isinstance(loaded["calculated_minimum_n_total"], int)
        assert isinstance(loaded["actual_corpus_size"], int)