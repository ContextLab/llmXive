"""
Unit tests for power_analysis module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    CLAIM_C_21F3E400_MIN_N
)
from code.src.config import SEED

class TestSampleSizeCalculations:
    def test_binary_sample_size_basic(self):
        """Test basic binary sample size calculation."""
        # Baseline 10%, effect 5% -> p2 = 0.15
        n = calculate_sample_size_binary(0.10, 0.15, alpha=0.05, power=0.80)
        assert n > 0
        # Rough check: should be in the thousands for small effects
        assert 1000 < n < 100000

    def test_binary_sample_size_effect_size(self):
        """Verify that larger effect sizes require smaller sample sizes."""
        n_small_effect = calculate_sample_size_binary(0.10, 0.11, alpha=0.05, power=0.80)
        n_large_effect = calculate_sample_size_binary(0.10, 0.20, alpha=0.05, power=0.80)
        assert n_small_effect > n_large_effect

    def test_continuous_sample_size_basic(self):
        """Test basic continuous sample size calculation."""
        n = calculate_sample_size_continuous(100.0, 105.0, sigma=10.0, alpha=0.05, power=0.80)
        assert n > 0
        # Effect size d = 0.5, n should be around 128 per group (2 * (1.96+0.84)^2 / 0.25)
        assert 50 < n < 500

    def test_invalid_proportions(self):
        """Test that invalid proportions raise errors."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.0, 0.1, alpha=0.05, power=0.80)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.1, 0.1, alpha=0.05, power=0.80)

class TestCorpusCounting:
    def test_count_empty_list(self):
        """Test counting records in an empty list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)

    def test_count_list(self):
        """Test counting records in a list."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    def test_count_dict_with_records(self):
        """Test counting records in a dict with 'records' key."""
        data = {"records": [{"id": 1}, {"id": 2}]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            os.unlink(temp_path)

    def test_missing_file(self):
        """Test handling of missing file."""
        count = count_corpus_size(Path("/nonexistent/path/file.json"))
        assert count == 0

class TestRunPowerAnalysis:
    def test_run_analysis_basic(self):
        """Test basic run of power analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            result = run_power_analysis(
                baseline=0.10,
                detectable_effect=0.05,
                output_path=output_path
            )
            
            assert "calculated_minimum_n" in result
            assert result["calculated_minimum_n"] > 0
            assert result["claim_validation"]["status"] == "N/A" # No audit report provided
            
            # Check file was written
            assert output_path.exists()
            with open(output_path) as f:
                saved_result = json.load(f)
            assert saved_result == result

    def test_run_analysis_with_corpus(self):
        """Test power analysis with a mock audit report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create a mock audit report with enough records
            mock_data = [{"id": i} for i in range(CLAIM_C_21F3E400_MIN_N + 100)]
            with open(audit_path, 'w') as f:
                json.dump(mock_data, f)
            
            result = run_power_analysis(
                baseline=0.10,
                detectable_effect=0.05,
                audit_report_path=audit_path,
                output_path=output_path
            )
            
            assert result["claim_validation"]["meets_requirement"] is True
            assert result["claim_validation"]["status"] == "PASS"
            assert result["claim_validation"]["actual_corpus_size"] == CLAIM_C_21F3E400_MIN_N + 100

    def test_run_analysis_insufficient_corpus(self):
        """Test power analysis with insufficient corpus size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create a mock audit report with too few records
            mock_data = [{"id": i} for i in range(100)]
            with open(audit_path, 'w') as f:
                json.dump(mock_data, f)
            
            result = run_power_analysis(
                baseline=0.10,
                detectable_effect=0.05,
                audit_report_path=audit_path,
                output_path=output_path
            )
            
            assert result["claim_validation"]["meets_requirement"] is False
            assert result["claim_validation"]["status"] == "FAIL"
            assert result["claim_validation"]["actual_corpus_size"] == 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
