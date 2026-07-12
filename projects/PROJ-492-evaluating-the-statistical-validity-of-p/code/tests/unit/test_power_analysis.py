"""
Unit tests for power_analysis.py module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    CLAIM_CORPUS_THRESHOLD
)


class TestCalculateSampleSizeBinary:
    def test_standard_conversion_rate(self):
        """Test with standard 10% baseline and 5% lift."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        # Approximate expected value for these parameters is around 393 per group
        assert 350 < n < 450

    def test_higher_power_requires_larger_n(self):
        """Increasing power should increase sample size."""
        n_80 = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.80)
        n_90 = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.90)
        assert n_90 > n_80

    def test_smaller_effect_requires_larger_n(self):
        """Detecting smaller effects requires larger sample size."""
        n_5 = calculate_sample_size_binary(0.10, 0.05, 0.05, 0.80)
        n_2 = calculate_sample_size_binary(0.10, 0.02, 0.05, 0.80)
        assert n_2 > n_5

    def test_invalid_rates(self):
        """Should raise error for rates outside (0, 1)."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.5, 0.05)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(-0.1, 0.05)

    def test_zero_effect(self):
        """Should raise error for zero detectable effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.0)


class TestCalculateSampleSizeContinuous:
    def test_standard_parameters(self):
        """Test with standard parameters."""
        n = calculate_sample_size_continuous(
            baseline_mean=100,
            detectable_effect=5,
            baseline_std=10,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        # Approximate expected value is around 64 per group
        assert 60 < n < 70

    def test_invalid_std(self):
        """Should raise error for non-positive std."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, 0)
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 5, -1)

    def test_zero_effect(self):
        """Should raise error for zero effect."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 0, 10)


class TestCountCorpusSize:
    def test_count_list(self):
        """Count records when data is a list."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            temp_path.unlink()

    def test_count_nested_dict(self):
        """Count records when data is a dict with 'records' key."""
        data = {"records": [{"id": 1}, {"id": 2}]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            temp_path.unlink()

    def test_nonexistent_file(self):
        """Should return 0 for non-existent file."""
        count = count_corpus_size(Path("/nonexistent/path/file.json"))
        assert count == 0

    def test_invalid_json(self):
        """Should return 0 for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            temp_path.unlink()


class TestRunPowerAnalysis:
    def test_run_creates_output(self):
        """Test that run_power_analysis creates the output file."""
        # Create a temporary audit report
        audit_data = [{"id": i} for i in range(1000)] # 1000 records
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            audit_file = tmp_path / "audit_report.json"
            output_file = tmp_path / "power_analysis.json"

            with open(audit_file, 'w') as f:
                json.dump(audit_data, f)

            result = run_power_analysis(
                output_path=output_file,
                audit_report_path=audit_file,
                baseline_rate=0.10,
                detectable_effect=0.05
            )

            assert output_file.exists()
            assert result["corpus_size"] == 1000
            assert "binary_n" in result
            assert "continuous_n" in result

    def test_threshold_assertion(self):
        """Test that the threshold check works correctly."""
        # Test with corpus size below threshold
        audit_data = [{"id": i} for i in range(100)] # 100 records
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            audit_file = tmp_path / "audit_report.json"
            output_file = tmp_path / "power_analysis.json"

            with open(audit_file, 'w') as f:
                json.dump(audit_data, f)

            result = run_power_analysis(
                output_path=output_file,
                audit_report_path=audit_file,
                baseline_rate=0.10,
                detectable_effect=0.05
            )

            assert result["meets_threshold"] is False
            assert result["threshold"] == CLAIM_CORPUS_THRESHOLD

            # Test with corpus size above threshold
            large_data = [{"id": i} for i in range(3000)] # 3000 records
            audit_file2 = tmp_path / "audit_report_large.json"
            output_file2 = tmp_path / "power_analysis_large.json"

            with open(audit_file2, 'w') as f:
                json.dump(large_data, f)

            result2 = run_power_analysis(
                output_path=output_file2,
                audit_report_path=audit_file2,
                baseline_rate=0.10,
                detectable_effect=0.05
            )

            assert result2["meets_threshold"] is True
            assert result2["corpus_size"] == 3000
