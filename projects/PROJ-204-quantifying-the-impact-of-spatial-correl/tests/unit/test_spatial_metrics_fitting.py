import numpy as np
import pytest
from scipy.optimize import curve_fit
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.analysis.spatial_metrics import (
    gaussian_decay,
    exponential_decay,
    power_law_decay,
    fit_decay_model,
    compute_radial_distances,
    extract_radial_profile
)

class TestDecayModels:
    def test_gaussian_decay_shape(self):
        r = np.linspace(0, 10, 100)
        A, sigma, offset = 1.0, 2.0, 0.1
        y = gaussian_decay(r, A, sigma, offset)
        assert y[0] == pytest.approx(A + offset, rel=1e-5)
        assert y[-1] < A + offset
        # Check 1/e point
        idx_1e = np.where(y <= offset + A/np.e)[0][0]
        assert r[idx_1e] == pytest.approx(sigma, rel=0.2)

    def test_exponential_decay_shape(self):
        r = np.linspace(0, 10, 100)
        A, tau, offset = 1.0, 2.0, 0.1
        y = exponential_decay(r, A, tau, offset)
        assert y[0] == pytest.approx(A + offset, rel=1e-5)
        # Check 1/e point
        idx_1e = np.where(y <= offset + A/np.e)[0][0]
        assert r[idx_1e] == pytest.approx(tau, rel=0.2)

    def test_power_law_decay_shape(self):
        r = np.linspace(1, 100, 100) # Avoid 0
        A, alpha, offset = 10.0, 1.5, 0.1
        y = power_law_decay(r, A, alpha, offset)
        assert y[0] == pytest.approx(A * (1.0 + 1e-6)**(-alpha) + offset, rel=1e-3)
        assert y[-1] < y[0]

class TestFitDecayModel:
    def test_fit_gaussian(self):
        # Generate synthetic data with known parameters
        r = np.linspace(0, 20, 100)
        true_A, true_sigma, true_offset = 2.0, 3.0, 0.05
        y_true = gaussian_decay(r, true_A, true_sigma, true_offset)
        # Add noise
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.05, size=r.shape)
        
        result = fit_decay_model(r, y_noisy, 'gaussian')
        
        assert result['success'] is True
        assert result['model_type'] == 'gaussian'
        assert result['params']['amplitude'] == pytest.approx(true_A, rel=0.2)
        assert result['params']['scale'] == pytest.approx(true_sigma, rel=0.2)
        assert result['params']['offset'] == pytest.approx(true_offset, rel=0.2)
        assert result['correlation_length'] == pytest.approx(true_sigma, rel=0.2)
        assert result['aic'] < np.inf

    def test_fit_exponential(self):
        r = np.linspace(0, 20, 100)
        true_A, true_tau, true_offset = 2.0, 3.0, 0.05
        y_true = exponential_decay(r, true_A, true_tau, true_offset)
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.05, size=r.shape)
        
        result = fit_decay_model(r, y_noisy, 'exponential')
        
        assert result['success'] is True
        assert result['params']['scale'] == pytest.approx(true_tau, rel=0.2)
        assert result['correlation_length'] == pytest.approx(true_tau, rel=0.2)

    def test_fit_power_law(self):
        r = np.linspace(1, 100, 100)
        true_A, true_alpha, true_offset = 10.0, 1.5, 0.1
        y_true = power_law_decay(r, true_A, true_alpha, true_offset)
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.1, size=r.shape)
        
        result = fit_decay_model(r, y_noisy, 'power_law')
        
        assert result['success'] is True
        # Power law fitting is trickier, just check success and reasonable params
        assert result['params']['amplitude'] > 0
        assert result['params']['scale'] > 0 # alpha
        assert result['correlation_length'] != result['correlation_length'] # NaN check

    def test_fit_undefined_decay(self):
        # Flat line (no decay)
        r = np.linspace(0, 10, 50)
        y = np.ones(50) * 0.5
        
        result = fit_decay_model(r, y, 'gaussian')
        # Should fail or produce very large sigma
        # With our bounds, it might fit a large sigma or fail
        # We assert it doesn't crash
        assert 'success' in result

class TestAICSelection:
    def test_aic_selection_gaussian_better(self):
        # Data generated from Gaussian
        r = np.linspace(0, 20, 100)
        true_A, true_sigma, true_offset = 2.0, 3.0, 0.05
        y_true = gaussian_decay(r, true_A, true_sigma, true_offset)
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.05, size=r.shape)
        
        # Fit both
        res_gauss = fit_decay_model(r, y_noisy, 'gaussian')
        res_exp = fit_decay_model(r, y_noisy, 'exponential')
        
        # Gaussian should have lower AIC
        if res_gauss['success'] and res_exp['success']:
            assert res_gauss['aic'] < res_exp['aic']

    def test_aic_selection_exponential_better(self):
        # Data generated from Exponential
        r = np.linspace(0, 20, 100)
        true_A, true_tau, true_offset = 2.0, 3.0, 0.05
        y_true = exponential_decay(r, true_A, true_tau, true_offset)
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.05, size=r.shape)
        
        res_gauss = fit_decay_model(r, y_noisy, 'gaussian')
        res_exp = fit_decay_model(r, y_noisy, 'exponential')
        
        if res_gauss['success'] and res_exp['success']:
            assert res_exp['aic'] < res_gauss['aic']
