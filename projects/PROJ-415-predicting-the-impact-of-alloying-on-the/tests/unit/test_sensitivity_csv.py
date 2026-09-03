import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

from config import REPORTS_DIR, DATA_DIR
from validation.sensitivity import (
    run_sensitivity_sweep, 
    calculate_stability_metric, 
    save_sensitivity_sweep_csv,
    calculate_baseline_shift
)

@pytest.fixture
def mock_curated_data(tmp_path):
    """Create a mock curated CSV for testing sensitivity logic."""
    data = {
        'host_symbol': ['Cu', 'Cu', 'Cu', 'Ag', 'Ag'],
        'solute_symbol': ['Zn', 'Ni', 'Au', 'Pd', 'Rh'],
        'concentration': [0.0, 0.05, 0.1, 0.0, 0.05],
        'activation_energy': [2.0, 2.1, 2.2, 1.5, 1.6], # Pure Cu=2.0, Pure Ag=1.5
        'crystal_structure': ['FCC'] * 5,
        'diffusion_mode': ['self'] * 5
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / 'filtered.csv'
    df.to_csv(csv_path, index=False)
    return csv_path

def test_baseline_shift_calculation(mock_curated_data):
    df = pd.read_csv(mock_curated_data)
    result_df = calculate_baseline_shift(df)
    
    # Pure Cu (0.0) -> shift should be 0 (2.0 - 2.0)
    # Zn (0.0) -> shift = 2.0 - 2.0 = 0.0? Wait, Zn is solute, Cu is host.
    # Row 0: host=Cu, conc=0.0, E=2.0. Pure Cu E=2.0. Shift = 0.0.
    # Row 1: host=Cu, conc=0.05, E=2.1. Pure Cu E=2.0. Shift = 0.1.
    # Row 3: host=Ag, conc=0.0, E=1.5. Pure Ag E=1.5. Shift = 0.0.
    
    assert 'baseline_shift' in result_df.columns
    assert abs(result_df.iloc[0]['baseline_shift']) < 1e-6
    assert abs(result_df.iloc[1]['baseline_shift'] - 0.1) < 1e-6

def test_sensitivity_sweep_logic(mock_curated_data):
    df = pd.read_csv(mock_curated_data)
    df = calculate_baseline_shift(df)
    
    # Manually set shifts for testing: [0.0, 0.1, 0.2, 0.0, 0.1] (assuming linear interp for Ag if needed, but here 0.0 exists)
    # Actually, let's rely on the function.
    
    results = run_sensitivity_sweep(df)
    
    assert len(results) > 0
    assert results[0]['threshold_eV'] == 0.45
    assert 'classification_rate' in results[0]
    
    # At 0.45, no shift (max 0.2 in mock) is > 0.45, so rate should be 0.0
    # If we had a shift > 0.45, rate would be > 0
    assert results[0]['classification_rate'] == 0.0

def test_stability_metric_calculation():
    mock_results = [
        {'threshold_eV': 0.45, 'classification_rate': 0.5},
        {'threshold_eV': 0.46, 'classification_rate': 0.5},
        {'threshold_eV': 0.47, 'classification_rate': 0.5},
    ]
    metrics = calculate_stability_metric(mock_results)
    
    assert metrics['stability_sd'] == 0.0
    assert metrics['mean_classification_rate'] == 0.5

def test_csv_output_generation(tmp_path):
    # Create a mock result list
    results = [
        {'threshold_eV': 0.45, 'classification_rate': 0.1, 'count_significant': 1, 'total_count': 10},
        {'threshold_eV': 0.46, 'classification_rate': 0.0, 'count_significant': 0, 'total_count': 10},
    ]
    stability = {'stability_sd': 0.0707, 'mean_classification_rate': 0.05}
    
    output_path = tmp_path / 'sensitivity_sweep.csv'
    save_sensitivity_sweep_csv(results, stability, output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    
    assert 'threshold_eV' in df.columns
    assert 'classification_rate' in df.columns
    assert 'stability_sd' in df.columns
    assert 'mean_classification_rate' in df.columns
    
    assert len(df) == 2
    assert df.iloc[0]['stability_sd'] == 0.0707
    assert df.iloc[0]['threshold_eV'] == 0.45