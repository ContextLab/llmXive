"""
Unit tests for meta_analysis.py (Diebold-Mariano and Westfall-Young).
"""

import os
import sys
import tempfile
import csv
from pathlib import Path
import pytest
import numpy as np

from src.evaluation.meta_analysis import (
    calculate_loss_differential,
    diebold_mariano_statistic,
    calculate_dm_statistics,
    westfall_young_correction,
    load_forecasts_and_outcomes,
    run_meta_analysis
)

@pytest.fixture
def sample_forecasts():
    """Generate simple synthetic forecasts for testing."""
    np.random.seed(42)
    n = 50
    outcome = np.random.randn(n)
    # Model A: good forecasts
    forecast_a = outcome + np.random.randn(n) * 0.5
    # Model B: worse forecasts
    forecast_b = outcome + np.random.randn(n) * 1.5
    return {
        'model_a': forecast_a.tolist(),
        'model_b': forecast_b.tolist()
    }, outcome.tolist(), ['model_a', 'model_b']

@pytest.fixture
def temp_forecast_file(sample_forecasts):
    """Create a temporary CSV file with forecast data."""
    forecasts, outcomes, model_names = sample_forecasts
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'model_a', 'model_b'])
        for i in range(len(outcomes)):
            writer.writerow([f"2020-{i:02d}-01", forecasts['model_a'][i], forecasts['model_b'][i]])
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_outcome_file(sample_forecasts):
    """Create a temporary CSV file with outcome data."""
    forecasts, outcomes, model_names = sample_forecasts
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'actual'])
        for i in range(len(outcomes)):
            writer.writerow([f"2020-{i:02d}-01", outcomes[i]])
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_loss_differential():
    """Test loss differential calculation."""
    forecast_a = [1.0, 2.0]
    forecast_b = [1.5, 2.5]
    outcome = [1.0, 2.0]
    
    # e_a = [0, 0], e_b = [-0.5, -0.5]
    # loss_a = [0, 0], loss_b = [0.25, 0.25]
    # diff = [-0.25, -0.25]
    diff = calculate_loss_differential(forecast_a, forecast_b, outcome)
    assert len(diff) == 2
    assert np.isclose(diff[0], -0.25)
    assert np.isclose(diff[1], -0.25)

def test_diebold_mariano_statistic():
    """Test DM statistic calculation."""
    # Perfect forecasts (loss diff = 0) -> stat = 0
    loss_diff = [0.0, 0.0, 0.0]
    stat = diebold_mariano_statistic(loss_diff)
    assert stat == 0.0

    # Non-zero mean
    loss_diff = [1.0, 1.0, 1.0]
    stat = diebold_mariano_statistic(loss_diff)
    # mean = 1, var = 0 -> stat = 0 (division by zero handled)
    # Actually if var is 0, we return 0.
    assert stat == 0.0

    # With variance
    loss_diff = [1.0, -1.0, 1.0]
    stat = diebold_mariano_statistic(loss_diff)
    # mean = 1/3, var = 4/3 (ddof=1)
    # se = sqrt(4/3 / 3) = sqrt(4/9) = 2/3
    # stat = (1/3) / (2/3) = 0.5
    assert np.isclose(stat, 0.5, atol=1e-4)

def test_westfall_young_correction_basic(sample_forecasts):
    """Test that Westfall-Young correction runs and returns valid p-values."""
    forecasts, outcomes, model_names = sample_forecasts
    # Use few permutations for speed in unit test
    p_vals = westfall_young_correction(
        forecasts, outcomes, model_names, n_permutations=10, seed=42
    )
    assert len(p_vals) == 1  # Only one pair
    assert (0.0 <= list(p_vals.values())[0] <= 1.0)

def test_run_meta_analysis_integration(temp_forecast_file, temp_outcome_file):
    """Integration test for the full meta-analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "meta_analysis.csv"
        
        run_meta_analysis(
            Path(temp_forecast_file),
            Path(temp_outcome_file),
            output_path
        )
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert 'dm_statistic' in rows[0]
            assert 'adjusted_p_value' in rows[0]
            assert 'significant' in rows[0]

def test_load_forecasts_and_outcomes_missing_file():
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        load_forecasts_and_outcomes(Path("nonexistent.csv"), Path("nonexistent.csv"))
