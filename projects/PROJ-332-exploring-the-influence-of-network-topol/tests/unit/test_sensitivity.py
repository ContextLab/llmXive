import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import SimulationConfig
from sensitivity_analysis import (
    run_sensitivity_sweep,
    calculate_deviation_report,
    report_sensitivity_results,
    analyze_sensitivity
)

@pytest.fixture
def sample_config():
    return SimulationConfig(
        N=50,
        p=0.1,
        d=50.0,
        l=1000.0,
        seed=42,
        material="Si",
        target_degree=4.0,
        sensitivity_factor_range=[0.8, 1.0, 1.2]
    )

@pytest.fixture
def sample_sweep_results():
    return [
        {'factor': 0.8, 'conductivity': 120.0, 'deviation': -0.10},
        {'factor': 1.0, 'conductivity': 133.33, 'deviation': 0.0},
        {'factor': 1.2, 'conductivity': 146.66, 'deviation': 0.10}
    ]

def test_sensitivity_sweep(sample_config):
    """Test that sensitivity sweep runs and returns expected structure."""
    # Mock the graph generation and solver to avoid complex dependencies
    with patch('sensitivity_analysis.generate_nanowire_network') as mock_gen, \
         patch('sensitivity_analysis.assign_thermal_resistance') as mock_res, \
         patch('sensitivity_analysis.solve_kirchhoff_heat_flow') as mock_solve, \
         patch('sensitivity_analysis.get_material_conductivity') as mock_k:
        
        # Setup mocks
        mock_gen.return_value = MagicMock()
        mock_res.return_value = {}
        mock_solve.side_effect = [100.0, 110.0, 120.0]  # Different conductivities
        mock_k.return_value = 149.0  # Si bulk conductivity
        
        results = run_sensitivity_sweep(sample_config, [0.8, 1.0, 1.2])
        
        # Verify results structure
        assert isinstance(results, list)
        assert len(results) == 3
        assert all('factor' in r for r in results)
        assert all('conductivity' in r for r in results)
        assert all('deviation' in r for r in results)

def test_deviation_report_calculation(sample_sweep_results):
    """Test deviation report calculation."""
    report = calculate_deviation_report(sample_sweep_results)
    
    assert not report.empty
    assert 'mean_deviation' in report.columns
    assert 'std_dev' in report.columns
    assert 'max_deviation' in report.columns
    
    # Verify calculated values
    assert report['mean_deviation'].iloc[0] == pytest.approx(0.0, abs=1e-6)
    assert report['max_deviation'].iloc[0] == pytest.approx(0.10, abs=1e-6)

def test_sensitivity_within_bounds(sample_sweep_results):
    """Test that sensitivity analysis correctly identifies within-bound results."""
    report = calculate_deviation_report(sample_sweep_results)
    metrics = analyze_sensitivity(report)
    
    # Max deviation is 0.10 (10%), should be within bounds
    assert abs(metrics['max_deviation']) <= 0.10

def test_sensitivity_exceeds_bounds(sample_sweep_results):
    """Test that sensitivity analysis correctly identifies out-of-bound results."""
    # Modify results to have larger deviation
    large_deviation_results = [
        {'factor': 0.8, 'conductivity': 90.0, 'deviation': -0.20},
        {'factor': 1.0, 'conductivity': 133.33, 'deviation': 0.0},
        {'factor': 1.2, 'conductivity': 176.66, 'deviation': 0.32}
    ]
    
    report = calculate_deviation_report(large_deviation_results)
    metrics = analyze_sensitivity(report)
    
    # Max deviation is 0.32 (32%), should exceed bounds
    assert abs(metrics['max_deviation']) > 0.10

def test_empty_sweep_results():
    """Test handling of empty sweep results."""
    report = calculate_deviation_report([])
    assert report.empty
    
    metrics = analyze_sensitivity(report)
    assert metrics['max_deviation'] == 0.0
    assert metrics['std_dev'] == 0.0

def test_report_sensitivity_results(capsys, sample_sweep_results):
    """Test that sensitivity results are logged correctly."""
    report = calculate_deviation_report(sample_sweep_results)
    metrics = analyze_sensitivity(report)
    
    report_sensitivity_results(metrics)
    
    captured = capsys.readouterr()
    assert 'Sensitivity Analysis Results' in captured.err or 'Mean Deviation' in captured.err
    assert '±10%' in captured.err or 'acceptable bounds' in captured.err.lower()
