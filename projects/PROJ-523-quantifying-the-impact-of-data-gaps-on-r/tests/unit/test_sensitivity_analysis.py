"""
Unit tests for sensitivity analysis module (T030).

These tests verify the sensitivity sweep functionality without requiring
the full pipeline to be executed.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sensitivity_analysis import (
    SensitivityConfig,
    load_bias_summary,
    simulate_bias_variance,
    calculate_significance_change,
    run_sensitivity_sweep,
    save_sensitivity_results
)
from config import DATA_RESULTS_DIR

class TestSensitivityConfig:
    """Test the SensitivityConfig dataclass."""
    
    def test_alpha_values(self):
        """Test that alpha values map correctly."""
        config = SensitivityConfig(alpha='low', tolerance='medium')
        assert config.get_alpha_value() == 0.01
        
        config = SensitivityConfig(alpha='medium', tolerance='high')
        assert config.get_alpha_value() == 0.05
        
        config = SensitivityConfig(alpha='high', tolerance='low')
        assert config.get_alpha_value() == 0.10

    def test_tolerance_values(self):
        """Test that tolerance values map correctly."""
        config = SensitivityConfig(alpha='medium', tolerance='low')
        assert config.get_tolerance_value() == 0.01
        
        config = SensitivityConfig(alpha='high', tolerance='high')
        assert config.get_tolerance_value() == 0.10

class TestSensitivityFunctions:
    """Test individual sensitivity analysis functions."""
    
    def test_simulate_bias_variance_empty_data(self):
        """Test variance calculation with empty data."""
        result = simulate_bias_variance([], 0.05, 0.05)
        assert result == 0.0

    def test_simulate_bias_variance_single_item(self):
        """Test variance calculation with single item."""
        data = [{'bias_magnitude': 0.5}]
        result = simulate_bias_variance(data, 0.05, 0.05)
        assert result == 0.0

    def test_simulate_bias_variance_multiple_items(self):
        """Test variance calculation with multiple items."""
        data = [
            {'bias_magnitude': 0.1},
            {'bias_magnitude': 0.2},
            {'bias_magnitude': 0.3},
            {'bias_magnitude': 0.4}
        ]
        result = simulate_bias_variance(data, 0.05, 0.05)
        assert result > 0.0
        # Variance should be reduced by alpha and tolerance factors
        assert result < np.var([0.1, 0.2, 0.3, 0.4])

    def test_significance_change_calculation(self):
        """Test significance change calculation."""
        data = [
            {'bias_magnitude': 0.1, 'p_value': 0.01},
            {'bias_magnitude': 0.2, 'p_value': 0.03},
            {'bias_magnitude': 0.3, 'p_value': 0.07}
        ]
        # With alpha=0.05, two results should be significant
        result = calculate_significance_change(data, 0.05, 0.05)
        assert result == pytest.approx(2/3, rel=0.01)

@pytest.fixture
def mock_bias_summary(tmp_path):
    """Create a temporary bias summary CSV for testing."""
    csv_path = tmp_path / "bias_summary.csv"
    csv_path.write_text(
        "realization_id,gap_fraction,algorithm_index,bias_magnitude\n"
        "1,0.05,0,0.12\n"
        "2,0.05,1,0.15\n"
        "3,0.10,0,0.18\n"
        "4,0.10,1,0.22\n"
        "5,0.15,0,0.25\n"
    )
    return csv_path

def test_load_bias_summary(mock_bias_summary, tmp_path):
    """Test loading bias summary from CSV."""
    # Temporarily override DATA_RESULTS_DIR
    with patch('analysis.sensitivity_analysis.DATA_RESULTS_DIR', tmp_path):
        # Copy mock file to expected location
        import shutil
        shutil.copy(mock_bias_summary, tmp_path / "bias_summary.csv")
        
        results = load_bias_summary()
        assert len(results) == 5
        assert results[0]['gap_fraction'] == 0.05
        assert results[0]['bias_magnitude'] == 0.12

def test_save_sensitivity_results(tmp_path):
    """Test saving sensitivity results to JSON."""
    results = {
        'sweep_parameters': {
            'alpha_levels': ['low', 'medium'],
            'tolerance_levels': ['low', 'medium']
        },
        'results': [
            {
                'alpha': 'low',
                'tolerance': 'low',
                'bias_variance': 0.00123456,
                'significance_change': 0.25
            }
        ],
        'total_combinations': 1
    }
    
    output_path = tmp_path / "test_sensitivity.json"
    save_sensitivity_results(results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['total_combinations'] == 1
    assert loaded['results'][0]['bias_variance'] == 0.00123456

def test_run_sensitivity_sweep_structure(tmp_path):
    """Test that the sweep produces the correct structure."""
    # Create mock bias data
    mock_data = [
        {'bias_magnitude': 0.1},
        {'bias_magnitude': 0.2},
        {'bias_magnitude': 0.15}
    ]
    
    with patch('analysis.sensitivity_analysis.load_bias_summary', return_value=mock_data):
        with patch('analysis.sensitivity_analysis.DATA_RESULTS_DIR', tmp_path):
            results = run_sensitivity_sweep()
            
            assert 'sweep_parameters' in results
            assert 'results' in results
            assert 'total_combinations' in results
            assert results['total_combinations'] == 9  # 3x3 combinations
            
            # Check result structure
            for res in results['results']:
                assert 'alpha' in res
                assert 'tolerance' in res
                assert 'bias_variance' in res
                assert 'significance_change' in res
                assert res['alpha'] in ['low', 'medium', 'high']
                assert res['tolerance'] in ['low', 'medium', 'high']