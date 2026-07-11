"""
Unit tests for power_analysis.py (T028)
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    MIN_CORPUS_SIZE_THRESHOLD
)
from code.src.config import SEED


class TestCalculateSampleSizeBinary:
    def test_standard_calculation(self):
        """Test standard calculation with known parameters."""
        # Baseline 0.1, effect 0.05 -> p1=0.15
        # Alpha 0.05, Power 0.8
        n = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.80)
        assert n > 0
        # Approximate check: should be in the hundreds
        assert 500 < n < 2000

    def test_invalid_baseline(self):
        with pytest.raises(ValueError):
            calculate_sample_size_binary(-0.1, 0.05)

    def test_zero_effect(self):
        """Effect of 0 should result in infinite sample size."""
        n = calculate_sample_size_binary(0.10, 0.0)
        assert np.isinf(n)


class TestCalculateSampleSizeContinuous:
    def test_standard_calculation(self):
        """Test with Cohen's d = 0.5."""
        n = calculate_sample_size_continuous(effect_size=0.5, alpha=0.05, power=0.80)
        assert n > 0
        # Approximate: 2 * (1.96 + 0.84)^2 / 0.25 ≈ 2 * 7.84 / 0.25 ≈ 62.72
        assert 60 < n < 70


class TestCountCorpusSize:
    def test_count_list(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            path = Path(f.name)
        
        try:
            count = count_corpus_size(path)
            assert count == 3
        finally:
            path.unlink()

    def test_count_dict_with_records(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            path = Path(f.name)
        
        try:
            count = count_corpus_size(path)
            assert count == 2
        finally:
            path.unlink()

    def test_missing_file(self):
        count = count_corpus_size(Path("/nonexistent/file.json"))
        assert count == 0


class TestRunPowerAnalysis:
    def test_full_run(self):
        """Test the full pipeline function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a dummy audit report
            audit_path = tmpdir_path / "audit_report.json"
            # Create a corpus larger than the threshold (2510.17)
            dummy_records = [{"id": i, "url": f"http://example.com/{i}"} for i in range(2600)]
            with open(audit_path, 'w') as f:
                json.dump(dummy_records, f)
            
            output_path = tmpdir_path / "power_analysis.json"
            
            result = run_power_analysis(
                input_audit_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05
            )
            
            assert output_path.exists()
            assert result["current_corpus_size"] == 2600
            assert result["assertion"]["meets_claim_threshold"] is True
            assert result["status"] == "success"

    def test_fails_threshold(self):
        """Test when corpus is too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            audit_path = tmpdir_path / "audit_report.json"
            # Create a corpus smaller than the threshold
            dummy_records = [{"id": i} for i in range(100)]
            with open(audit_path, 'w') as f:
                json.dump(dummy_records, f)
            
            output_path = tmpdir_path / "power_analysis.json"
            
            result = run_power_analysis(
                input_audit_path=audit_path,
                output_path=output_path
            )
            
            assert result["current_corpus_size"] == 100
            assert result["assertion"]["meets_claim_threshold"] is False
            assert result["status"] == "warning"
            
            # Verify file content
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert "threshold_n" in data["claim_reference"]
                assert data["claim_reference"]["threshold_n"] == MIN_CORPUS_SIZE_THRESHOLD
