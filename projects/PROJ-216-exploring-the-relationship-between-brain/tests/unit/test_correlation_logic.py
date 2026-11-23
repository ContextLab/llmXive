import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import (
    compute_correlation, 
    analyze_correlations, 
    bonferroni_correction,
    load_graph_metrics,
    calculate_power
)

class TestCorrelationLogic:
    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        return {
            'x': [1.0, 2.0, 3.0, 4.0, 5.0],
            'y': [2.0, 4.0, 5.0, 4.0, 5.0]
        }

    @pytest.fixture
    def mock_metrics_csv(self, tmp_path):
        """Create a temporary CSV file with mock metrics."""
        csv_path = tmp_path / "metrics.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'metric_name', 'value', 'fluid_intelligence_score', 'age', 'gender'])
            writer.writeheader()
            writer.writerow({'subject_id': 's1', 'metric_name': 'efficiency', 'value': 0.5, 'fluid_intelligence_score': 100.0, 'age': 25, 'gender': 'M'})
            writer.writerow({'subject_id': 's2', 'metric_name': 'efficiency', 'value': 0.6, 'fluid_intelligence_score': 110.0, 'age': 30, 'gender': 'F'})
            writer.writerow({'subject_id': 's3', 'metric_name': 'efficiency', 'value': 0.4, 'fluid_intelligence_score': 90.0, 'age': 22, 'gender': 'M'})
            writer.writerow({'subject_id': 's4', 'metric_name': 'clustering', 'value': 0.3, 'fluid_intelligence_score': 105.0, 'age': 28, 'gender': 'F'})
        return str(csv_path)

    def test_compute_correlation_perfect(self):
        """Test correlation with perfect positive relationship."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        corr, p_val = compute_correlation(x, y, method='pearson')
        assert corr is not None
        assert abs(corr - 1.0) < 1e-6
        assert p_val is not None
        assert p_val < 0.05

    def test_compute_correlation_negative(self):
        """Test correlation with perfect negative relationship."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        corr, p_val = compute_correlation(x, y, method='pearson')
        assert corr is not None
        assert abs(corr - (-1.0)) < 1e-6
        assert p_val is not None
        assert p_val < 0.05

    def test_compute_correlation_random(self):
        """Test correlation with random data (should be near zero)."""
        x = [1.0, 5.0, 2.0, 8.0, 3.0]
        y = [9.0, 1.0, 7.0, 2.0, 6.0]
        corr, p_val = compute_correlation(x, y, method='pearson')
        # We don't assert exact value, just that it computes without error
        assert isinstance(corr, float)
        assert -1.0 <= corr <= 1.0

    def test_compute_correlation_insufficient_data(self):
        """Test correlation with insufficient data points."""
        x = [1.0, 2.0]
        y = [3.0, 4.0]
        corr, p_val = compute_correlation(x, y, method='pearson')
        assert corr is None
        assert p_val is None

    def test_bonferroni_correction(self):
        """Test Bonferroni correction calculation."""
        p_values = [0.01, 0.05, 0.03]
        n_tests = 3
        corrected = bonferroni_correction(p_values, n_tests)
        expected = [0.03, 0.15, 0.09]
        for c, e in zip(corrected, expected):
            assert abs(c - e) < 1e-6
        
        # Test capping at 1.0
        p_values_high = [0.5, 0.6]
        corrected_high = bonferroni_correction(p_values_high, 3)
        assert corrected_high[0] == 1.0 # 1.5 capped
        assert corrected_high[1] == 1.0 # 1.8 capped

    def test_analyze_correlations_integration(self, mock_metrics_csv):
        """Test full correlation analysis on mock data."""
        data = load_graph_metrics(mock_metrics_csv)
        result = analyze_correlations(data, 'efficiency')
        
        assert result['metric_name'] == 'efficiency'
        assert result['n'] == 3
        assert result['correlation'] is not None
        assert -1.0 <= result['correlation'] <= 1.0
        assert result['p_value'] is not None
        assert result['method'] == 'pearson'

    def test_calculate_power(self):
        """Test power calculation function."""
        # With N=10 and r=0.8, power should be reasonable
        power = calculate_power(10, 0.8)
        assert 0.0 <= power <= 1.0
        
        # With N=10 and r=0.1, power should be low
        power_low = calculate_power(10, 0.1)
        assert power_low < power # Lower effect size -> lower power
        
        # With N=3, power should be 0
        power_zero = calculate_power(3, 0.5)
        assert power_zero == 0.0