"""Unit tests for power analysis utility (FR-025)."""

import json
import os
import tempfile
import pytest

from src.audit.power_analysis import (
    calculate_minimum_sample_size,
    calculate_power,
    run_power_analysis,
    write_output
)


class TestCalculateMinimumSampleSize:
    """Tests for calculate_minimum_sample_size function."""
    
    def test_basic_calculation(self):
        """Test basic sample size calculation with standard parameters."""
        n = calculate_minimum_sample_size(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
    
    def test_larger_effect_requires_smaller_sample(self):
        """Larger detectable effects require smaller sample sizes."""
        n_small_effect = calculate_minimum_sample_size(
            baseline_rate=0.10,
            detectable_effect=0.01,
            alpha=0.05,
            power=0.80
        )
        n_large_effect = calculate_minimum_sample_size(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n_large_effect < n_small_effect
    
    def test_higher_power_requires_larger_sample(self):
        """Higher power requires larger sample sizes."""
        n_low_power = calculate_minimum_sample_size(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.70
        )
        n_high_power = calculate_minimum_sample_size(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.90
        )
        assert n_high_power > n_low_power
    
    def test_invalid_baseline_rate(self):
        """Test that invalid baseline rates raise ValueError."""
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(
                baseline_rate=1.5,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80
            )
    
    def test_invalid_effect(self):
        """Test that invalid effect sizes raise ValueError."""
        with pytest.raises(ValueError):
            calculate_minimum_sample_size(
                baseline_rate=0.10,
                detectable_effect=-0.01,
                alpha=0.05,
                power=0.80
            )

class TestCalculatePower:
    """Tests for calculate_power function."""
    
    def test_basic_power_calculation(self):
        """Test basic power calculation."""
        power = calculate_power(
            sample_size_per_group=1000,
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05
        )
        assert 0 <= power <= 1
    
    def test_larger_sample_increases_power(self):
        """Larger samples increase statistical power."""
        power_small = calculate_power(
            sample_size_per_group=500,
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05
        )
        power_large = calculate_power(
            sample_size_per_group=2000,
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05
        )
        assert power_large > power_small
    
    def test_larger_effect_increases_power(self):
        """Larger effects increase statistical power."""
        power_small_effect = calculate_power(
            sample_size_per_group=1000,
            baseline_rate=0.10,
            detectable_effect=0.01,
            alpha=0.05
        )
        power_large_effect = calculate_power(
            sample_size_per_group=1000,
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05
        )
        assert power_large_effect > power_small_effect

class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""
    
    def test_returns_required_fields(self):
        """Test that result contains all required fields."""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80,
            corpus_size=500,
            min_corpus_size=300
        )
        
        required_fields = [
            "baseline_rate",
            "detectable_effect",
            "alpha",
            "power",
            "minimum_sample_size_per_group",
            "total_minimum_sample_size",
            "corpus_size",
            "minimum_corpus_size_requirement",
            "meets_requirement",
            "actual_power_if_corpus_provided",
            "notes"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_meets_requirement_true(self):
        """Test meets_requirement is True when corpus is sufficient."""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            corpus_size=1000,
            min_corpus_size=300
        )
        assert result["meets_requirement"] is True
    
    def test_meets_requirement_false(self):
        """Test meets_requirement is False when corpus is insufficient."""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            corpus_size=100,
            min_corpus_size=300
        )
        assert result["meets_requirement"] is False
    
    def test_actual_power_calculated(self):
        """Test that actual power is calculated when corpus size provided."""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            corpus_size=1000,
            min_corpus_size=300
        )
        assert result["actual_power_if_corpus_provided"] is not None
        assert 0 <= result["actual_power_if_corpus_provided"] <= 1

class TestWriteOutput:
    """Tests for write_output function."""
    
    def test_writes_valid_json(self):
        """Test that output file contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            result = run_power_analysis()
            write_output(result, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded == result
    
    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test_output.json")
            result = run_power_analysis()
            write_output(result, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.exists(os.path.dirname(output_path))

class TestIntegration:
    """Integration tests for power analysis utility."""
    
    def test_full_workflow(self):
        """Test complete power analysis workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "power_analysis.json")
            
            # Run analysis
            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80,
                corpus_size=500,
                min_corpus_size=300
            )
            
            # Write output
            write_output(result, output_path)
            
            # Verify file exists and contains expected data
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["baseline_rate"] == 0.10
            assert loaded["detectable_effect"] == 0.02
            assert loaded["meets_requirement"] is True
            assert "minimum_sample_size_per_group" in loaded
            assert loaded["minimum_sample_size_per_group"] > 0
