"""
Unit tests for power analysis utility.

Tests FR-025 requirements:
- Correct calculation of minimum sample size
- Proper handling of edge cases
- Corpus validation logic
- JSON output format
"""
import json
import tempfile
from pathlib import Path
import pytest

import numpy as np
from scipy import stats

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    MIN_CORPUS_SIZE_THRESHOLD
)
from code.src.config import SEED

class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_standard_calculation(self):
        """Test standard calculation with typical parameters."""
        n = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.80
        )
        
        # Should be a positive integer
        assert n > 0
        assert isinstance(n, (int, np.integer))
        
        # Check against expected range (should be around 1200-1300 per group)
        assert 1000 < n < 2000

    def test_larger_effect_requires_smaller_sample(self):
        """Larger effect sizes should require smaller sample sizes."""
        n_small_effect = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.01,
            alpha=0.05,
            power=0.80
        )
        
        n_large_effect = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.10,
            alpha=0.05,
            power=0.80
        )
        
        assert n_large_effect < n_small_effect

    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample sizes."""
        n_low_power = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.70
        )
        
        n_high_power = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.90
        )
        
        assert n_high_power > n_low_power

    def test_invalid_baseline_raises_error(self):
        """Invalid baseline values should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline=0.0, effect_size=0.05)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline=1.0, effect_size=0.05)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline=-0.1, effect_size=0.05)

    def test_invalid_effect_size_raises_error(self):
        """Invalid effect size values should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline=0.10, effect_size=0.95)  # p2 > 1

    def test_threshold_requirement(self):
        """Verify that the calculated N meets the threshold requirement."""
        # The task requires meeting the threshold from claim c_21f3e400
        # which specifies N >= 2510.17487
        n = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.80
        )
        
        # The total N (both groups) should meet the threshold
        total_n = 2 * n
        assert total_n >= MIN_CORPUS_SIZE_THRESHOLD, \
            f"Total N ({total_n}) must meet threshold ({MIN_CORPUS_SIZE_THRESHOLD})"

class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_standard_calculation(self):
        """Test standard calculation for continuous outcomes."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            effect_size=5.0,
            baseline_std=15.0,
            alpha=0.05,
            power=0.80
        )
        
        assert n > 0
        assert isinstance(n, (int, np.integer))

    def test_invalid_std_raises_error(self):
        """Invalid standard deviation should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=100.0,
                effect_size=5.0,
                baseline_std=0.0
            )
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=100.0,
                effect_size=5.0,
                baseline_std=-1.0
            )

class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_from_list(self):
        """Count records from a list structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            temp_path.unlink()

    def test_count_from_dict_with_records(self):
        """Count records from a dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            temp_path.unlink()

    def test_file_not_found_raises_error(self):
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            count_corpus_size(Path("/nonexistent/path/file.json"))

class TestRunPowerAnalysis:
    """Tests for the main power analysis runner."""

    def test_full_run_with_defaults(self):
        """Test full run with default parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            result = run_power_analysis(
                output_path=output_path
            )
            
            # Check required fields
            assert "baseline_rate" in result
            assert "detectable_effect_size" in result
            assert "alpha" in result
            assert "power" in result
            assert "minimum_n_per_group" in result
            assert "total_minimum_n" in result
            assert "corpus_meets_requirement" in result
            assert "threshold_reference" in result
            
            # Check numeric values
            assert result["minimum_n_per_group"] > 0
            assert result["total_minimum_n"] > 0
            
            # Check output file was created
            assert output_path.exists()
            
            # Verify file content matches result
            with open(output_path) as f:
                file_result = json.load(f)
            
            assert file_result == result

    def test_run_with_audit_report(self):
        """Test run with an audit report for corpus validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a mock audit report
            audit_path = tmpdir_path / "audit_report.json"
            mock_records = [{"id": i, "consistent": True} for i in range(3000)]
            with open(audit_path, 'w') as f:
                json.dump(mock_records, f)
            
            output_path = tmpdir_path / "power_analysis.json"
            
            result = run_power_analysis(
                audit_report_path=audit_path,
                output_path=output_path
            )
            
            # Should have corpus size info
            assert result["corpus_size"] == 3000
            assert result["validation_message"] is not None

    def test_run_without_audit_report(self):
        """Test run without audit report (corpus validation skipped)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            result = run_power_analysis(
                audit_report_path=None,
                output_path=output_path
            )
            
            # Corpus size should be None
            assert result["corpus_size"] is None
            assert result["corpus_meets_requirement"] is True  # Default when not validated
            assert result["validation_message"] is None

class TestOutputFormat:
    """Tests for JSON output format compliance."""

    def test_output_contains_numeric_n(self):
        """Verify output contains numeric N values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            run_power_analysis(output_path=output_path)
            
            with open(output_path) as f:
                result = json.load(f)
            
            # Both N values should be numeric
            assert isinstance(result["minimum_n_per_group"], (int, float))
            assert isinstance(result["total_minimum_n"], (int, float))
            
            # Should be positive
            assert result["minimum_n_per_group"] > 0
            assert result["total_minimum_n"] > 0

    def test_output_contains_threshold_citation(self):
        """Verify output contains the required citation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            
            run_power_analysis(output_path=output_path)
            
            with open(output_path) as f:
                result = json.load(f)
            
            assert "threshold_reference" in result
            assert "threshold_citation" in result
            assert result["threshold_citation"] == "https://arxiv.org/abs/2510.17487"