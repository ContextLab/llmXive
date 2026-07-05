"""
Unit tests for power_analysis.py module.

Tests:
- calculate_sample_size_binary
- calculate_sample_size_continuous
- count_corpus_size
- run_power_analysis
- write_power_analysis_result
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result
)
from code.src.config import set_rng_seed, SEED


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_basic_binary_calculation(self):
        """Test basic binary sample size calculation."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, (int, np.integer))

    def test_higher_power_requires_more_samples(self):
        """Increasing power should increase required sample size."""
        n_80 = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        n_90 = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.90
        )
        assert n_90 > n_80

    def test_smaller_effect_requires_more_samples(self):
        """Smaller detectable effect should increase required sample size."""
        n_05 = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        n_02 = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )
        assert n_02 > n_05

    def test_invalid_baseline_rate_raises_error(self):
        """Invalid baseline rate should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.0,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.0,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )

    def test_invalid_effect_raises_error(self):
        """Invalid detectable effect should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=0.0,
                alpha=0.05,
                power=0.80
            )


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_basic_continuous_calculation(self):
        """Test basic continuous sample size calculation."""
        n = calculate_sample_size_continuous(
            baseline_mean=0.0,
            baseline_std=0.5,
            detectable_effect=0.1,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, (int, np.integer))

    def test_higher_power_requires_more_samples(self):
        """Increasing power should increase required sample size."""
        n_80 = calculate_sample_size_continuous(
            baseline_mean=0.0,
            baseline_std=0.5,
            detectable_effect=0.1,
            alpha=0.05,
            power=0.80
        )
        n_90 = calculate_sample_size_continuous(
            baseline_mean=0.0,
            baseline_std=0.5,
            detectable_effect=0.1,
            alpha=0.05,
            power=0.90
        )
        assert n_90 > n_80

    def test_smaller_effect_requires_more_samples(self):
        """Smaller detectable effect should increase required sample size."""
        n_10 = calculate_sample_size_continuous(
            baseline_mean=0.0,
            baseline_std=0.5,
            detectable_effect=0.1,
            alpha=0.05,
            power=0.80
        )
        n_05 = calculate_sample_size_continuous(
            baseline_mean=0.0,
            baseline_std=0.5,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n_05 > n_10

    def test_invalid_std_raises_error(self):
        """Invalid standard deviation should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=0.0,
                baseline_std=0.0,
                detectable_effect=0.1,
                alpha=0.05,
                power=0.80
            )


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_from_valid_json(self):
        """Test counting records from a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    def test_count_from_dict_with_records(self):
        """Test counting records from a dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            os.unlink(temp_path)

    def test_count_from_nonexistent_file(self):
        """Test counting from a non-existent file returns 0."""
        count = count_corpus_size(Path("/nonexistent/path/file.json"))
        assert count == 0

    def test_count_from_invalid_json(self):
        """Test counting from invalid JSON returns 0."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)


class TestRunPowerAnalysis:
    """Tests for the main power analysis function."""

    def test_run_with_sufficient_corpus(self):
        """Test power analysis with a corpus that meets requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"

            # Create a mock audit report with 500 records
            with open(audit_path, 'w') as f:
                json.dump([{"id": i} for i in range(500)], f)

            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80,
                audit_records_path=audit_path,
                output_path=output_path,
                minimum_corpus_size=300
            )

            assert result["actual_corpus_size"] == 500
            assert result["meets_requirement"] is True
            assert result["constraint_satisfied"] is True
            assert output_path.exists()

    def test_run_with_insufficient_corpus(self):
        """Test power analysis with a corpus that doesn't meet requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"

            # Create a mock audit report with 100 records (below 300)
            with open(audit_path, 'w') as f:
                json.dump([{"id": i} for i in range(100)], f)

            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80,
                audit_records_path=audit_path,
                output_path=output_path,
                minimum_corpus_size=300
            )

            assert result["actual_corpus_size"] == 100
            assert result["meets_requirement"] is False
            assert result["constraint_satisfied"] is False

    def test_constraint_logic_or_condition(self):
        """Test that constraint is satisfied if N >= 300 OR N >= calculated_minimum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit_report.json"

            # Create a mock audit report with exactly 300 records
            with open(audit_path, 'w') as f:
                json.dump([{"id": i} for i in range(300)], f)

            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80,
                audit_records_path=audit_path,
                minimum_corpus_size=300
            )

            # Should satisfy N >= 300 condition
            assert result["constraint_satisfied"] is True
            assert result["actual_corpus_size"] >= 300


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""

    def test_write_creates_file(self):
        """Test that writing creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            result = {
                "test": "value",
                "number": 42
            }

            write_power_analysis_result(result, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == result

    def test_write_creates_parent_directories(self):
        """Test that writing creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "power_analysis.json"
            result = {"test": "value"}

            write_power_analysis_result(result, output_path)

            assert output_path.exists()

    def test_write_with_datetime(self):
        """Test that datetime is serialized correctly."""
        from datetime import datetime
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            result = {
                "timestamp": datetime.now(),
                "value": 123
            }

            write_power_analysis_result(result, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert "timestamp" in loaded
            assert loaded["value"] == 123
