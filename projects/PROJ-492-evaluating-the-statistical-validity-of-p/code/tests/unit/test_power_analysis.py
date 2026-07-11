"""
Unit tests for power analysis utility.

Tests FR-025 requirements:
- Sample size calculation for binary outcomes
- Sample size calculation for continuous outcomes
- Corpus size counting
- Output file generation
- Claim threshold validation
"""

import json
import pytest
from pathlib import Path
import tempfile
import os

import numpy as np
from scipy import stats

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    write_power_analysis_result,
    run_power_analysis
)


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation with standard parameters."""
        n, metadata = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )

        assert n > 0
        assert isinstance(n, float)
        assert metadata['baseline_rate'] == 0.10
        assert metadata['treatment_rate'] == 0.15
        assert metadata['detectable_effect'] == 0.05
        assert metadata['alpha'] == 0.05
        assert metadata['power'] == 0.80

    def test_larger_effect_requires_smaller_sample(self):
        """Larger detectable effect should require smaller sample size."""
        n_small_effect, _ = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )

        n_large_effect, _ = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.10,
            alpha=0.05,
            power=0.80
        )

        assert n_large_effect < n_small_effect

    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample size."""
        n_low_power, _ = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )

        n_high_power, _ = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.90
        )

        assert n_high_power > n_low_power

    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )

        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=-0.1,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )

    def test_invalid_effect_size(self):
        """Should raise ValueError for invalid effect size."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=1.5,
                alpha=0.05,
                power=0.80
            )

        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=-0.5,
                alpha=0.05,
                power=0.80
            )

    def test_invalid_treatment_rate(self):
        """Should raise ValueError if treatment rate exceeds 1."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.90,
                detectable_effect=0.15,  # 0.90 + 0.15 = 1.05 > 1
                alpha=0.05,
                power=0.80
            )


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcomes."""
        n, metadata = calculate_sample_size_continuous(
            baseline_mean=100,
            detectable_effect=5,
            std_dev=15,
            alpha=0.05,
            power=0.80
        )

        assert n > 0
        assert isinstance(n, float)
        assert metadata['effect_size'] == pytest.approx(5/15, rel=0.01)

    def test_larger_effect_size(self):
        """Larger effect size should require smaller sample."""
        n_small, _ = calculate_sample_size_continuous(
            baseline_mean=100,
            detectable_effect=2,
            std_dev=15,
            alpha=0.05,
            power=0.80
        )

        n_large, _ = calculate_sample_size_continuous(
            baseline_mean=100,
            detectable_effect=10,
            std_dev=15,
            alpha=0.05,
            power=0.80
        )

        assert n_large < n_small

    def test_invalid_std_dev(self):
        """Should raise ValueError for non-positive standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=100,
                detectable_effect=5,
                std_dev=0,
                alpha=0.05,
                power=0.80
            )

        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=100,
                detectable_effect=5,
                std_dev=-5,
                alpha=0.05,
                power=0.80
            )


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_from_list(self):
        """Should correctly count records from a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            temp_path.unlink()

    def test_count_from_dict(self):
        """Should correctly count records from a dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            count_corpus_size(Path("/nonexistent/path/file.json"))

    def test_invalid_format(self):
        """Should raise ValueError for invalid JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"data": [{"id": 1}]}, f)  # No 'records' key and not a list
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                count_corpus_size(temp_path)
        finally:
            temp_path.unlink()


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""

    def test_write_to_json(self):
        """Should write valid JSON to file."""
        result = {
            "test": "value",
            "number": 42,
            "nested": {"key": "value"}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
          output_path = Path(tmpdir) / "test_output.json"
          write_power_analysis_result(result, output_path)

          assert output_path.exists()

          with open(output_path, 'r') as f:
              loaded = json.load(f)

          assert loaded == result

    def test_creates_directories(self):
        """Should create parent directories if they don't exist."""
        result = {"test": "value"}

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "subdir" / "nested" / "output.json"
            write_power_analysis_result(result, nested_path)

            assert nested_path.exists()


class TestRunPowerAnalysis:
    """Tests for the main power analysis workflow."""

    def test_full_workflow(self):
        """Test complete power analysis workflow."""
        # Create a mock audit report
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create mock audit report with enough records
            audit_data = [{"id": i, "status": "consistent"} for i in range(3000)]
            audit_path = tmpdir_path / "audit_report.json"
            with open(audit_path, 'w') as f:
                json.dump(audit_data, f)

            output_path = tmpdir_path / "power_analysis.json"

            # Run power analysis
            result = run_power_analysis(
                audit_report_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80,
                claim_threshold=2510.17487
            )

            # Verify results
            assert result['actual_corpus_size'] == 3000
            assert result['results']['meets_claim_threshold'] is True
            assert result['results']['meets_power_requirement'] is True
            assert result['status'] == 'PASS'

            # Verify output file was created
            assert output_path.exists()

            with open(output_path, 'r') as f:
                saved_result = json.load(f)

            assert saved_result == result

    def test_corpus_below_threshold(self):
        """Should report FAIL when corpus is below threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create mock audit report with few records
            audit_data = [{"id": i} for i in range(100)]
            audit_path = tmpdir_path / "audit_report.json"
            with open(audit_path, 'w') as f:
                json.dump(audit_data, f)

            output_path = tmpdir_path / "power_analysis.json"

            result = run_power_analysis(
                audit_report_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80,
                claim_threshold=2510.17487
            )

            assert result['actual_corpus_size'] == 100
            assert result['results']['meets_claim_threshold'] is False
            assert result['status'] == 'FAIL'

    def test_missing_audit_report(self):
        """Should raise error when audit report is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "nonexistent.json"
            output_path = Path(tmpdir) / "output.json"

            with pytest.raises(FileNotFoundError):
                run_power_analysis(
                    audit_report_path=audit_path,
                    output_path=output_path
                )
