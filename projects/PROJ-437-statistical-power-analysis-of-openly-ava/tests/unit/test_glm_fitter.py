"""
Unit tests for code/analysis/glm_fitter.py
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from analysis.glm_fitter import (
    fit_glm, 
    estimate_effect_size, 
    fit_glm_batch, 
    ConvergenceLogger, 
    GLMFitError
)
from utils.seed_manager import set_global_seed


def test_fit_glm_basic():
    """Test basic GLM fitting with known data."""
    set_global_seed(42)
    n = 50
    x = np.arange(n)
    y = 2 * x + 1 + np.random.normal(0, 1, n)
    
    X = np.column_stack([np.ones(n), x])
    
    results, converged, iterations = fit_glm(y, X, random_seed=42)
    
    assert converged is True
    assert results.params[1] > 1.5  # Slope should be close to 2
    assert results.params[0] > 0    # Intercept should be positive


def test_estimate_effect_size():
    """Test Cohen's d calculation."""
    set_global_seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    y = 2 * x + np.random.normal(0, 1, n)
    
    X = sm.add_constant(x)
    model = sm.GLM(y, X, family=sm.families.Gaussian())
    results = model.fit()
    
    cohens_d = estimate_effect_size(results, beta_index=1)
    
    # Cohen's d for beta=2, sigma=1 is roughly 2
    assert abs(cohens_d - 2.0) < 0.5


def test_convergence_logger(tmp_path):
    """Test ConvergenceLogger writes correct JSON."""
    output_file = tmp_path / "test_convergence.json"
    logger = ConvergenceLogger(str(output_file))
    
    logger.log(1, True, 100, 1e-4)
    logger.log(2, False, 50, 1e-4)
    logger.save()
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['iteration_id'] == 1
    assert data[0]['converged'] is True
    assert data[1]['converged'] is False


def test_fit_glm_batch_subsampling():
    """Test that batch fitting subsamples subjects correctly."""
    set_global_seed(42)
    n_subjects = 50
    n_timepoints = 100
    n_rois = 1
    
    # Create synthetic data
    time = np.arange(n_timepoints)
    signal = np.sin(2 * np.pi * time / 20)
    noise = np.random.normal(0, 1, (n_subjects, n_timepoints, n_rois))
    roi_data = (signal + noise).reshape(n_subjects, n_timepoints, n_rois)
    
    X = np.column_stack([np.ones(n_timepoints), time])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "log.json"
        logger = ConvergenceLogger(str(log_path))
        
        result = fit_glm_batch(
            roi_data=roi_data,
            design_matrix=X,
            sample_size=10,
            random_seed=42,
            convergence_logger=logger,
            iteration_id=1
        )
        
        assert result['sample_size'] == 10
        assert 'cohens_d' in result
        assert 'converged' in result
        
        # Check log file
        logger.save()
        with open(log_path, 'r') as f:
            logs = json.load(f)
        assert len(logs) == 1
        assert logs[0]['iteration_id'] == 1


def test_fit_glm_batch_insufficient_data():
    """Test behavior when requested sample size > available."""
    set_global_seed(42)
    n_subjects = 5
    n_timepoints = 100
    n_rois = 1
    
    time = np.arange(n_timepoints)
    signal = np.sin(2 * np.pi * time / 20)
    noise = np.random.normal(0, 1, (n_subjects, n_timepoints, n_rois))
    roi_data = (signal + noise).reshape(n_subjects, n_timepoints, n_rois)
    
    X = np.column_stack([np.ones(n_timepoints), time])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "log.json"
        logger = ConvergenceLogger(str(log_path))
        
        # Request 20 subjects, only 5 available
        result = fit_glm_batch(
            roi_data=roi_data,
            design_matrix=X,
            sample_size=20,
            random_seed=42,
            convergence_logger=logger,
            iteration_id=1
        )
        
        # Should clamp to 5
        assert result['sample_size'] == 5


def test_fit_glm_nan_error():
    """Test that GLM fitting raises error on NaN data."""
    set_global_seed(42)
    n = 50
    x = np.arange(n)
    y = 2 * x + 1 + np.random.normal(0, 1, n)
    y[10] = np.nan
    
    X = sm.add_constant(x)
    
    with pytest.raises(GLMFitError):
        fit_glm(y, X, random_seed=42)
