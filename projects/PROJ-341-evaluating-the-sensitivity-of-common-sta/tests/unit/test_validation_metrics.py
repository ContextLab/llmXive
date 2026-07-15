"""
Unit tests for validation_metrics.py (T034)

Tests for:
- load_simulated_pvalues_for_comparison
- load_real_data_pvalues
- calculate_real_data_power
- calculate_ks_distance
- calculate_validation_metrics
- save_validation_metrics
"""

import os
import json
import numpy as np
from scipy import stats

# Import the module under test
from code.analysis.validation_metrics import (
    load_simulated_pvalues_for_comparison,
    load_real_data_pvalues,
    calculate_real_data_power,
    calculate_ks_distance,
    calculate_validation_metrics,
    save_validation_metrics
)


class TestLoadSimulatedPValues:
    """Tests for load_simulated_pvalues_for_comparison"""

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty CSV file"""
        csv_path = tmp_path / "p_values_raw.csv"
        csv_path.write_text("sample_size,effect_size,test_type,p_value\n")

        result = load_simulated_pvalues_for_comparison()
        assert result == {}

    def test_load_single_entry(self, tmp_path):
        """Test loading a single entry"""
        csv_path = tmp_path / "p_values_raw.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value\n"
            "10,0.5,t-test,0.03\n"
        )

        result = load_simulated_pvalues_for_comparison()
        assert (10, 0.5) in result
        assert len(result[(10, 0.5)]) == 1
        assert result[(10, 0.5)][0] == 0.03

    def test_load_multiple_entries(self, tmp_path):
        """Test loading multiple entries"""
        csv_path = tmp_path / "p_values_raw.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value\n"
            "10,0.5,t-test,0.03\n"
            "10,0.5,t-test,0.04\n"
            "20,0.3,anova,0.06\n"
        )

        result = load_simulated_pvalues_for_comparison()
        assert len(result[(10, 0.5)]) == 2
        assert len(result[(20, 0.3)]) == 1

    def test_filter_by_test_type(self, tmp_path):
        """Test filtering by test type"""
        csv_path = tmp_path / "p_values_raw.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value\n"
            "10,0.5,t-test,0.03\n"
            "10,0.5,anova,0.04\n"
        )

        result = load_simulated_pvalues_for_comparison(test_type='t-test')
        assert len(result) == 1
        assert (10, 0.5) in result


class TestLoadRealDataPValues:
    """Tests for load_real_data_pvalues"""

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty CSV file"""
        csv_path = tmp_path / "real_data_pvalues.csv"
        csv_path.write_text("test_type,p_value\n")

        result = load_real_data_pvalues()
        assert result == {}

    def test_load_single_entry(self, tmp_path):
        """Test loading a single entry"""
        csv_path = tmp_path / "real_data_pvalues.csv"
        csv_path.write_text(
            "test_type,p_value\n"
            "t-test,0.03\n"
        )

        result = load_real_data_pvalues()
        assert 't-test' in result
        assert result['t-test'] == [0.03]

    def test_load_multiple_test_types(self, tmp_path):
        """Test loading multiple test types"""
        csv_path = tmp_path / "real_data_pvalues.csv"
        csv_path.write_text(
            "test_type,p_value\n"
            "t-test,0.03\n"
            "anova,0.04\n"
            "chi-squared,0.05\n"
        )

        result = load_real_data_pvalues()
        assert len(result) == 3
        assert 't-test' in result
        assert 'anova' in result
        assert 'chi-squared' in result


class TestCalculateRealDataPower:
    """Tests for calculate_real_data_power"""

    def test_empty_list(self):
        """Test with empty list"""
        result = calculate_real_data_power([])
        assert np.isnan(result['empirical_power'])
        assert result['sample_size'] == 0

    def test_all_rejections(self):
        """Test when all p-values reject null"""
        p_values = [0.01, 0.02, 0.03, 0.04]
        result = calculate_real_data_power(p_values, alpha=0.05)
        assert result['empirical_power'] == 1.0
        assert result['sample_size'] == 4

    def test_no_rejections(self):
        """Test when no p-values reject null"""
        p_values = [0.1, 0.2, 0.3, 0.4]
        result = calculate_real_data_power(p_values, alpha=0.05)
        assert result['empirical_power'] == 0.0
        assert result['sample_size'] == 4

    def test_partial_rejections(self):
        """Test with partial rejections"""
        p_values = [0.01, 0.06, 0.03, 0.1]
        result = calculate_real_data_power(p_values, alpha=0.05)
        assert result['empirical_power'] == 0.5  # 2 out of 4
        assert result['sample_size'] == 4


class TestCalculateKsDistance:
    """Tests for calculate_ks_distance"""

    def test_empty_lists(self):
        """Test with empty lists"""
        result = calculate_ks_distance([], [])
        assert 'insufficient_data' in result['note']

    def test_identical_distributions(self):
        """Test with identical distributions"""
        np.random.seed(42)
        sim = np.random.uniform(0, 1, 100)
        real = sim.copy()
        result = calculate_ks_distance(list(sim), list(real))
        assert result['ks_statistic'] == 0.0

    def test_different_distributions(self):
        """Test with different distributions"""
        np.random.seed(42)
        sim = np.random.uniform(0, 0.5, 100)  # Uniform on [0, 0.5]
        real = np.random.uniform(0.5, 1.0, 100)  # Uniform on [0.5, 1.0]
        result = calculate_ks_distance(list(sim), list(real))
        # KS statistic should be high for very different distributions
        assert result['ks_statistic'] > 0.5
        assert not np.isnan(result['p_value'])

    def test_single_values(self):
        """Test with single values"""
        result = calculate_ks_distance([0.03], [0.04])
        assert not np.isnan(result['ks_statistic'])


class TestCalculateValidationMetrics:
    """Tests for calculate_validation_metrics"""

    def test_missing_files(self, tmp_path, monkeypatch):
        """Test when required files are missing"""
        # Monkeypatch paths to point to non-existent files
        monkeypatch.setattr(
            "code.analysis.validation_metrics.SIMULATED_PVALUES_PATH",
            str(tmp_path / "nonexistent.csv")
        )
        monkeypatch.setattr(
            "code.analysis.validation_metrics.REAL_DATA_PVALUES_PATH",
            str(tmp_path / "nonexistent.csv")
        )

        with pytest.raises(FileNotFoundError):
            calculate_validation_metrics()

    def test_structure_of_output(self, tmp_path, monkeypatch):
        """Test that output has expected structure"""
        # Create minimal test files
        sim_csv = tmp_path / "p_values_raw.csv"
        sim_csv.write_text(
            "sample_size,effect_size,test_type,p_value\n"
            "10,0.5,t-test,0.03\n"
            "10,0.5,t-test,0.04\n"
            "20,0.3,anova,0.06\n"
        )

        real_csv = tmp_path / "real_data_pvalues.csv"
        real_csv.write_text(
            "test_type,p_value\n"
            "t-test,0.03\n"
            "t-test,0.04\n"
            "anova,0.06\n"
        )

        monkeypatch.setattr(
            "code.analysis.validation_metrics.SIMULATED_PVALUES_PATH",
            str(sim_csv)
        )
        monkeypatch.setattr(
            "code.analysis.validation_metrics.REAL_DATA_PVALUES_PATH",
            str(real_csv)
        )

        metrics = calculate_validation_metrics()

        assert 'timestamp' in metrics
        assert 'alpha' in metrics
        assert 'test_types' in metrics
        assert 'summary' in metrics
        assert 'total_tests' in metrics['summary']
        assert 'passed' in metrics['summary']
        assert 'overall_status' in metrics['summary']


class TestSaveValidationMetrics:
    """Tests for save_validation_metrics"""

    def test_save_and_load(self, tmp_path):
        """Test saving and reloading metrics"""
        metrics = {
            'test': 'validation',
            'value': 42,
            'nested': {'key': 'value'}
        }

        output_path = tmp_path / "test_metrics.json"
        saved_path = save_validation_metrics(metrics, str(output_path))

        assert saved_path == str(output_path)
        assert output_path.exists()

        with open(output_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == metrics

    def test_creates_directory(self, tmp_path):
        """Test that function creates output directory if needed"""
        metrics = {'test': 'value'}
        nested_path = tmp_path / "subdir" / "metrics.json"

        save_validation_metrics(metrics, str(nested_path))
        assert nested_path.exists()