"""
Unit tests for the power_analysis module.
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
    run_power_analysis
)


class TestCalculateSampleSizeBinary:
    def test_standard_calculation(self):
        """Test standard calculation with known parameters."""
        # Baseline 10%, detect 5% lift (15% vs 10%), alpha 0.05, power 0.8
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        # Expected n per group is roughly 390-400 for these parameters
        assert n > 0
        assert n < 10000

    def test_invalid_baseline(self):
        """Test that invalid baseline raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline_rate=0.0, detectable_effect=0.05)

        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline_rate=1.0, detectable_effect=0.05)

    def test_invalid_effect(self):
        """Test that invalid effect raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(baseline_rate=0.10, detectable_effect=0.0)

    def test_large_effect_reduces_sample_size(self):
        """Larger detectable effect should require smaller sample size."""
        n_small_effect = calculate_sample_size_binary(0.10, 0.01, 0.05, 0.80)
        n_large_effect = calculate_sample_size_binary(0.10, 0.10, 0.05, 0.80)
        assert n_large_effect < n_small_effect


class TestCalculateSampleSizeContinuous:
    def test_standard_calculation(self):
        """Test standard calculation for continuous data."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            detectable_effect=5.0,
            std_dev=10.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0

    def test_zero_std_dev_raises_error(self):
        """Test that zero standard deviation raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100.0, 5.0, 0.0)


class TestCountCorpusSize:
    def test_count_list(self):
        """Test counting records from a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            path = Path(f.name)

        try:
            count = count_corpus_size(path)
            assert count == 3
        finally:
            path.unlink()

    def test_count_dict_with_records(self):
        """Test counting from a dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            path = Path(f.name)

        try:
            count = count_corpus_size(path)
            assert count == 2
        finally:
            path.unlink()

    def test_missing_file(self):
        """Test handling of missing file."""
        count = count_corpus_size(Path("/nonexistent/path.json"))
        assert count == 0


class TestRunPowerAnalysis:
    def test_end_to_end(self):
        """Test the full run_power_analysis workflow."""
        # Create a temporary audit report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create a corpus of 3000 items to satisfy the 2510 threshold
            records = [{"id": i, "inconsistent": False} for i in range(3000)]
            json.dump(records, f)
            input_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
            output_path.unlink()  # Remove so the function can create it

        try:
            results, condition_met = run_power_analysis(
                audit_report_path=input_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05
            )

            assert "calculated_minimum_n" in results
            assert "corpus_size" in results
            assert results["corpus_size"] == 3000
            assert condition_met is True

            # Verify the output file was created
            assert output_path.exists()
            with open(output_path, 'r') as f:
                output_data = json.load(f)
            assert output_data["meets_claim_condition"] is True

        finally:
            input_path.unlink()
            if output_path.exists():
                output_path.unlink()

    def test_corpus_too_small(self):
        """Test when corpus size is below threshold."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create a corpus of 100 items (below 2510 threshold)
            records = [{"id": i} for i in range(100)]
            json.dump(records, f)
            input_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
            output_path.unlink()

        try:
            results, condition_met = run_power_analysis(
                audit_report_path=input_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05
            )

            assert results["corpus_size"] == 100
            assert condition_met is False

            with open(output_path, 'r') as f:
                output_data = json.load(f)
            assert output_data["meets_claim_condition"] is False

        finally:
            input_path.unlink()
            if output_path.exists():
                output_path.unlink()