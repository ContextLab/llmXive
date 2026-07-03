"""Tests for power analysis module."""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import csv

from analysis.power import (
    compute_effect_size,
    compute_power,
    compute_detectable_effect_size,
    load_experiment_results,
    run_power_analysis,
    generate_power_report,
    PowerAnalysisResult
)


class TestEffectSizeComputation:
    """Test effect size calculations."""

    def test_cohen_d_identical_groups(self):
        """Effect size should be zero for identical groups."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        effect_size = compute_effect_size(group1, group2, "cohen_d")
        assert np.isclose(effect_size, 0.0)

    def test_cohen_d_different_groups(self):
        """Effect size should be positive for different groups."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

        effect_size = compute_effect_size(group1, group2, "cohen_d")
        assert effect_size < 0  # group1 < group2

    def test_hedges_g_correction(self):
        """Hedges' g should be slightly different from Cohen's d."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

        d = compute_effect_size(group1, group2, "cohen_d")
        g = compute_effect_size(group1, group2, "hedges_g")

        # Hedges' g should be slightly smaller in magnitude
        assert abs(g) < abs(d)

    def test_invalid_method(self):
        """Should raise ValueError for unknown method."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([4.0, 5.0, 6.0])

        with pytest.raises(ValueError):
            compute_effect_size(group1, group2, "unknown_method")


class TestPowerComputation:
    """Test power calculations."""

    def test_power_increases_with_effect_size(self):
        """Power should increase with larger effect sizes."""
        sample_size = 50

        power_small = compute_power(0.2, sample_size)
        power_medium = compute_power(0.5, sample_size)
        power_large = compute_power(0.8, sample_size)

        assert power_small < power_medium < power_large

    def test_power_increases_with_sample_size(self):
        """Power should increase with larger sample sizes."""
        effect_size = 0.5

        power_small_n = compute_power(effect_size, 20)
        power_medium_n = compute_power(effect_size, 50)
        power_large_n = compute_power(effect_size, 100)

        assert power_small_n < power_medium_n < power_large_n

    def test_power_bounds(self):
        """Power should be between 0 and 1."""
        power = compute_power(0.5, 30)
        assert 0.0 <= power <= 1.0


class TestDetectableEffectSize:
    """Test detectable effect size calculations."""

    def test_detectable_es_decreases_with_sample_size(self):
        """Detectable effect size should decrease with larger samples."""
        power = 0.80

        es_small_n = compute_detectable_effect_size(20, power)
        es_medium_n = compute_detectable_effect_size(50, power)
        es_large_n = compute_detectable_effect_size(100, power)

        assert es_large_n < es_medium_n < es_small_n

    def test_detectable_es_decreases_with_power(self):
        """Detectable effect size should increase with higher target power."""
        sample_size = 50

        es_low_power = compute_detectable_effect_size(sample_size, 0.50)
        es_medium_power = compute_detectable_effect_size(sample_size, 0.80)
        es_high_power = compute_detectable_effect_size(sample_size, 0.95)

        assert es_low_power < es_medium_power < es_high_power


class TestExperimentResultsLoading:
    """Test loading of experiment results."""

    def test_load_results_creates_split(self):
        """Should correctly split results by context condition."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['game_id', 'specialization_index', 'context_condition'])
            writer.writeheader()

            # Add some test data
            for i in range(10):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': 0.5 + i * 0.01,
                    'context_condition': 'full'
                })

            for i in range(10, 20):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': 0.3 + (i - 10) * 0.01,
                    'context_condition': 'limited'
                })

            temp_path = Path(f.name)

        full, limited = load_experiment_results(temp_path, 'specialization_index')

        assert len(full) == 10
        assert len(limited) == 10

        # Clean up
        temp_path.unlink()

    def test_load_results_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_experiment_results(Path('/nonexistent/path.csv'), 'specialization_index')


class TestPowerAnalysisExecution:
    """Test end-to-end power analysis execution."""

    def test_run_power_analysis(self):
        """Should produce valid power analysis results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['game_id', 'specialization_index', 'context_condition'])
            writer.writeheader()

            # Create realistic test data
            np.random.seed(42)
            for i in range(50):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': np.random.normal(0.6, 0.1),
                    'context_condition': 'full'
                })

            for i in range(50, 100):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': np.random.normal(0.5, 0.1),
                    'context_condition': 'limited'
                })

            temp_path = Path(f.name)

        results = run_power_analysis(temp_path, 'specialization_index')

        assert len(results) == 1
        result = results[0]

        assert isinstance(result, PowerAnalysisResult)
        assert result.sample_size > 0
        assert -2 <= result.observed_effect_size <= 2  # Reasonable effect size range
        assert 0 <= result.power <= 1

        # Clean up
        temp_path.unlink()

    def test_generate_power_report(self):
        """Should generate valid JSON report file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['game_id', 'specialization_index', 'context_condition'])
            writer.writeheader()

            np.random.seed(42)
            for i in range(30):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': np.random.normal(0.6, 0.1),
                    'context_condition': 'full'
                })

            for i in range(30, 60):
                writer.writerow({
                    'game_id': i,
                    'specialization_index': np.random.normal(0.5, 0.1),
                    'context_condition': 'limited'
                })

            temp_data_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_output_path = Path(f.name)

        try:
            report = generate_power_report(
                temp_data_path,
                temp_output_path,
                metrics=['specialization_index']
            )

            assert 'results' in report
            assert len(report['results']) > 0
            assert temp_output_path.exists()

        finally:
            temp_data_path.unlink()
            temp_output_path.unlink()