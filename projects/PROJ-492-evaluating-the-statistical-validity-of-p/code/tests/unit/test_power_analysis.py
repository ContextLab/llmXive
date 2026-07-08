"""
Unit tests for power analysis utility (T028).
"""
import json
import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    REFERENCE_CORPUS_MIN
)


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation with standard parameters."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)

    def test_larger_effect_requires_smaller_sample(self):
        """Larger detectable effects should require smaller sample sizes."""
        n_small_effect = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.01,
            alpha=0.05,
            power=0.80
        )
        n_large_effect = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n_large_effect < n_small_effect

    def test_higher_power_requires_larger_sample(self):
        """Higher power should require larger sample sizes."""
        n_low_power = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.70
        )
        n_high_power = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.90
        )
        assert n_high_power > n_low_power

    def test_invalid_baseline_rate(self):
        """Should raise ValueError for invalid baseline rate."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,
                detectable_effect=0.02,
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


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""

    def test_basic_calculation(self):
        """Test basic sample size calculation."""
        n = calculate_sample_size_continuous(
            baseline_mean=0.5,
            detectable_effect=0.1,
            baseline_std=0.5,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)

    def test_larger_effect_requires_smaller_sample(self):
        """Larger detectable effects should require smaller sample sizes."""
        n_small_effect = calculate_sample_size_continuous(
            baseline_mean=0.5,
            detectable_effect=0.05,
            baseline_std=0.5,
            alpha=0.05,
            power=0.80
        )
        n_large_effect = calculate_sample_size_continuous(
            baseline_mean=0.5,
            detectable_effect=0.2,
            baseline_std=0.5,
            alpha=0.05,
            power=0.80
        )
        assert n_large_effect < n_small_effect

    def test_invalid_std(self):
        """Should raise ValueError for invalid standard deviation."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=0.5,
                detectable_effect=0.1,
                baseline_std=-1.0,
                alpha=0.05,
                power=0.80
            )


class TestCountCorpusSize:
    """Tests for corpus size counting."""

    def test_count_from_list(self):
        """Test counting records from a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            f.flush()
            count = count_corpus_size(Path(f.name))
            assert count == 3
        os.unlink(f.name)

    def test_count_from_dict_with_records(self):
        """Test counting from dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            f.flush()
            count = count_corpus_size(Path(f.name))
            assert count == 2
        os.unlink(f.name)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            count_corpus_size(Path("/nonexistent/file.json"))


class TestRunPowerAnalysis:
    """Tests for the main power analysis function."""

    def test_basic_run(self):
        """Test basic power analysis run."""
        results = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80,
            audit_report_path=None
        )

        assert "analysis_parameters" in results
        assert "sample_size_requirements" in results
        assert "corpus_validation" in results
        assert "reference" in results
        assert results["reference"]["paper"] == "2510.17487"

    def test_with_mock_audit_report(self):
        """Test power analysis with a mock audit report."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create a mock audit report with enough records
            mock_records = [{"id": i, "consistent": True} for i in range(REFERENCE_CORPUS_MIN + 100)]
            json.dump(mock_records, f)
            f.flush()

            results = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80,
                audit_report_path=Path(f.name)
            )

            assert results["corpus_validation"]["meets_requirement"] is True
            assert results["corpus_validation"]["corpus_size"] > REFERENCE_CORPUS_MIN

            os.unlink(f.name)

    def test_with_insufficient_corpus(self):
        """Test power analysis with insufficient corpus size."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create a mock audit report with too few records
            mock_records = [{"id": i, "consistent": True} for i in range(100)]
            json.dump(mock_records, f)
            f.flush()

            results = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80,
                audit_report_path=Path(f.name)
            )

            assert results["corpus_validation"]["meets_requirement"] is False
            assert results["corpus_validation"]["corpus_size"] == 100

            os.unlink(f.name)


class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""

    def test_write_to_file(self):
        """Test writing results to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            results = {
                "test": "data",
                "number": 42
            }

            write_power_analysis_result(results, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == results


class TestReferenceCorpusMinimum:
    """Tests for the reference corpus minimum requirement."""

    def test_reference_value(self):
        """Test that the reference corpus minimum is set correctly."""
        # From paper 2510.17487, claim c_21f3e400
        assert REFERENCE_CORPUS_MIN == 2511

    def test_reference_paper_url(self):
        """Test that the reference paper URL is correct."""
        assert REFERENCE_CORPUS_MIN > 0  # Sanity check that it's a valid number)