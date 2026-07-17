"""
Integration tests for the flight delay analysis pipeline.
Specifically tests the diagnostic plotting and validation flow (US3).
"""
import os
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import pipeline components
from preprocessing import preprocess_flight_delays
from models import (
    fit_all_base_distributions,
    fit_pareto_tail,
    estimate_x_min_ks,
    save_x_min_estimate,
    save_model_comparison,
)
from diagnostics import (
    hill_estimator,
    compute_hill_statistics,
    save_stability_curve,
    save_tail_index_estimate,
    bootstrap_gof_test,
    log_normal_discrimination,
    tail_ks_test,
)
from visualization import (
    plot_log_log_survival,
    plot_qq,
    plot_hill_stability,
)
from utils import setup_logging, check_memory_limit
from config import RANDOM_SEED, TARGET_YEAR

# Ensure logging is configured for the test run
setup_logging()


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data and results."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_cleaned_data(temp_data_dir):
    """
    Generate a realistic mock dataset that mimics the output of US1 (cleaned_delays.csv).
    This avoids dependency on the actual download for the integration test while
    ensuring the data structure and statistical properties (heavy tail) are present.
    """
    # Set seed for reproducibility
    rng = np.random.default_rng(RANDOM_SEED)
    
    n_samples = 5000
    
    # Generate a heavy-tailed distribution (Pareto) for the tail
    # alpha ~ 1.5 is a typical heavy tail index for delays
    alpha = 1.5
    x_min = 10.0
    tail_data = rng.pareto(alpha, size=int(n_samples * 0.1)) * x_min + x_min
    
    # Generate a light-tailed distribution (Gamma) for the bulk
    # Gamma(k=2, theta=10) has a mean of 20
    bulk_data = rng.gamma(k=2, theta=10, size=int(n_samples * 0.9))
    
    # Combine and shuffle
    combined = np.concatenate([bulk_data, tail_data])
    rng.shuffle(combined)
    
    # Create a DataFrame
    df = pd.DataFrame({
        'ArrDelay': np.maximum(combined, 0),
        'DepDelay': np.maximum(combined * 0.8, 0), # Correlated but slightly smaller
        'Carrier': ['AA', 'DL', 'UA', 'SW'] * (n_samples // 4),
        'FlightDate': pd.date_range(start='2023-01-01', periods=n_samples, freq='1min')
    })
    
    # Ensure non-negative delays
    df['ArrDelay'] = df['ArrDelay'].clip(lower=0)
    df['DepDelay'] = df['DepDelay'].clip(lower=0)
    
    # Save to CSV
    csv_path = Path(temp_data_dir) / 'cleaned_delays.csv'
    df.to_csv(csv_path, index=False)
    
    return csv_path


def test_full_diagnostic_pipeline(mock_cleaned_data, temp_data_dir):
    """
    Integration test: Run the full US3 diagnostic pipeline on cleaned data.
    
    Validates:
    1. x_min estimation works.
    2. Models fit successfully on the tail.
    3. Hill estimator produces a stability curve.
    4. Bootstrap GoF and Log-Normal discrimination run without error.
    5. Visualization functions generate files.
    """
    # Setup output paths
    data_dir = Path(temp_data_dir)
    results_dir = data_dir / 'results'
    figures_dir = data_dir / 'figures'
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    
    # 1. Load data
    df = pd.read_csv(mock_cleaned_data)
    delays = df['ArrDelay'].values
    
    # 2. Estimate x_min (T026 logic)
    x_min_estimate = estimate_x_min_ks(delays)
    x_min_path = results_dir / 'x_min_estimate.json'
    save_x_min_estimate(x_min_estimate, x_min_path)
    
    assert x_min_path.exists(), "x_min_estimate.json not created"
    with open(x_min_path) as f:
        x_min_data = json.load(f)
    assert 'x_min' in x_min_data
    
    # 3. Fit models on tail (T024, T025 logic)
    tail_data = delays[delays >= x_min_data['x_min']]
    assert len(tail_data) > 10, "Not enough tail data for fitting"
    
    # Fit base distributions on tail
    fitted_models = fit_all_base_distributions(tail_data)
    assert len(fitted_models) > 0, "No models fitted"
    
    # Fit Pareto on tail
    pareto_result = fit_pareto_tail(tail_data)
    assert pareto_result is not None, "Pareto fitting failed"
    
    # 4. Hill Estimator (T033 logic)
    hill_stats = compute_hill_statistics(tail_data)
    stability_curve_path = results_dir / 'stability_curve.csv'
    save_stability_curve(hill_stats, stability_curve_path)
    assert stability_curve_path.exists(), "stability_curve.csv not created"
    
    # Validate stability window
    is_valid, alpha_est = validate_stability_window(hill_stats)
    assert is_valid, "Stability window validation failed"
    
    tail_index_path = results_dir / 'tail_index_estimate.json'
    save_tail_index_estimate({'alpha': alpha_est, 'x_min': x_min_data['x_min']}, tail_index_path)
    assert tail_index_path.exists(), "tail_index_estimate.json not created"
    
    # 5. Bootstrap GoF (T034 logic)
    # Select the best model based on AIC (simplified for test)
    best_model_name = min(fitted_models, key=lambda m: m['aic'])
    bootstrap_pval = bootstrap_gof_test(
        tail_data, 
        best_model_name, 
        fitted_models[best_model_name]['params'],
        n_iter=100  # Reduced for speed
    )
    assert isinstance(bootstrap_pval, float), "Bootstrap p-value is not a float"
    
    # 6. Log-Normal Discrimination (T035 logic)
    ln_result = log_normal_discrimination(tail_data)
    assert ln_result is not None, "Log-Normal discrimination failed"
    
    # 7. Tail KS Test (T038 logic)
    tail_ks_pval = tail_ks_test(tail_data, best_model_name, fitted_models[best_model_name]['params'])
    assert isinstance(tail_ks_pval, float), "Tail KS p-value is not a float"
    
    # 8. Visualization (T036, T037)
    # Plot Log-Log Survival
    plot_log_log_survival(
        tail_data, 
        fitted_models, 
        pareto_result,
        save_path=str(figures_dir / 'log_log_survival.png')
    )
    assert (figures_dir / 'log_log_survival.png').exists(), "log_log_survival.png not created"
    
    # Plot QQ
    plot_qq(
        tail_data, 
        best_model_name, 
        fitted_models[best_model_name]['params'],
        save_path=str(figures_dir / 'qq_plot.png')
    )
    assert (figures_dir / 'qq_plot.png').exists(), "qq_plot.png not created"
    
    # Plot Hill Stability
    plot_hill_stability(
        hill_stats, 
        save_path=str(figures_dir / 'hill_stability.png')
    )
    assert (figures_dir / 'hill_stability.png').exists(), "hill_stability.png not created"
    
    # Verify all expected output files exist
    expected_files = [
        'x_min_estimate.json',
        'stability_curve.csv',
        'tail_index_estimate.json',
        'log_log_survival.png',
        'qq_plot.png',
        'hill_stability.png'
    ]
    
    for fname in expected_files:
        fpath = results_dir / fname if fname.endswith('.json') or fname.endswith('.csv') else figures_dir / fname
        assert fpath.exists(), f"Expected output file missing: {fpath}"

def validate_stability_window(hill_stats):
    """
    Helper to validate the stability window of the Hill estimator.
    Returns (is_valid, alpha_estimate).
    """
    if not hill_stats or len(hill_stats) == 0:
        return False, None
    
    # Simple heuristic: check if the last 10% of the curve is relatively flat
    # In a real implementation, this would use variance minimization
    vals = np.array([h['alpha'] for h in hill_stats])
    if len(vals) < 10:
        return False, None
    
    tail_vals = vals[int(len(vals) * 0.9):]
    std_dev = np.std(tail_vals)
    
    # If std dev is low, we assume stability
    is_valid = std_dev < 0.5
    alpha_est = np.mean(vals[-10:]) if is_valid else None
    
    return is_valid, alpha_est