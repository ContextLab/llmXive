"""
Unit tests for Shadowing Lemma Check functionality.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from analysis.shadowing import (
    compute_divergence_rate,
    validate_shadowing_lemma,
    run_shadowing_check_batch,
    gate_for_ftle_calculation,
    ShadowingResult,
    ShadowingCheckError
)
from analysis.baseline import BaselineResult

@pytest.fixture
def mock_trajectories():
    """Create mock clean and noisy trajectories."""
    T = 1000
    N = 2
    D = 3
    shape = (T, N * D)
    
    # Clean trajectory: small random walk with bounded values
    np.random.seed(42)
    clean = np.cumsum(np.random.randn(T, N * D) * 0.01, axis=0)
    clean = np.clip(clean, -10, 10)  # Keep bounded
    
    # Noisy trajectory: clean + small noise
    noise = np.random.randn(T, N * D) * 0.001
    noisy = clean + noise
    
    return clean, noisy

@pytest.fixture
def mock_baseline(tmp_path):
    """Create a mock baseline file."""
    baseline_data = {
        'lambda_max': 0.75,
        'error_estimate': 0.02,
        'N': 2,
        'converged': True
    }
    baseline_file = tmp_path / 'baseline_2.json'
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f)
    return baseline_file

@pytest.fixture
def mock_trajectory_files(tmp_path):
    """Create mock trajectory files."""
    # Create clean trajectory
    T = 1000
    N = 2
    D = 3
    clean = np.cumsum(np.random.randn(T, N * D) * 0.01, axis=0)
    clean = np.clip(clean, -10, 10)
    
    clean_file = tmp_path / 'raw' / 'trajectory_clean_test.npz'
    clean_file.parent.mkdir(parents=True)
    np.savez(clean_file, trajectory=clean)
    
    # Create noisy trajectory
    noise = np.random.randn(T, N * D) * 0.001
    noisy = clean + noise
    
    noisy_file = tmp_path / 'raw' / 'trajectory_noisy_test_0.0010.npz'
    np.savez(noisy_file, trajectory=noisy)
    
    return tmp_path

def test_compute_divergence_rate_basic(mock_trajectories):
    """Test basic divergence rate computation."""
    clean, noisy = mock_trajectories
    dt = 0.01
    
    rate = compute_divergence_rate(clean, noisy, dt)
    
    # Should return a finite number
    assert isinstance(rate, float)
    assert not np.isnan(rate)
    assert not np.isinf(rate)
    
    # For small noise, rate should be close to 0 (trajectories stay close)
    assert abs(rate) < 1.0

def test_compute_divergence_rate_mismatched_shapes(mock_trajectories):
    """Test that mismatched shapes raise an error."""
    clean, noisy = mock_trajectories
    noisy_mismatched = noisy[:500]  # Different length
    
    with pytest.raises(ValueError, match="Trajectory shapes must match"):
        compute_divergence_rate(clean, noisy_mismatched)

def test_compute_divergence_rate_zero_separation():
    """Test handling of zero separation."""
    T = 100
    clean = np.random.randn(T, 6)
    noisy = clean.copy()  # Identical trajectories
    
    rate = compute_divergence_rate(clean, noisy, dt=0.01)
    
    # Should handle gracefully and return a small number
    assert isinstance(rate, float)
    assert not np.isnan(rate)

def test_validate_shadowing_lemma_success(mock_baseline, mock_trajectory_files):
    """Test successful shadowing validation."""
    config = {
        'N': 2,
        'dt': 0.01,
        'data_dir': str(mock_trajectory_files)
    }
    
    result = validate_shadowing_lemma(
        trajectory_id='test',
        noise_level=0.001,
        config=config,
        data_dir=mock_trajectory_files,
        shadowing_tolerance=0.5
    )
    
    assert isinstance(result, ShadowingResult)
    assert result.trajectory_id == 'test'
    assert result.noise_level == 0.001
    assert result.baseline_lambda_max == 0.75
    assert result.is_shadowing in [True, False]  # Depends on actual data
    assert result.message is not None

def test_validate_shadowing_lemma_missing_baseline(mock_trajectory_files):
    """Test error when baseline is missing."""
    config = {
        'N': 99,  # Non-existent baseline
        'dt': 0.01,
        'data_dir': str(mock_trajectory_files)
    }
    
    with pytest.raises(ShadowingCheckError, match="Baseline file not found"):
        validate_shadowing_lemma(
            trajectory_id='test',
            noise_level=0.001,
            config=config,
            data_dir=mock_trajectory_files
        )

def test_validate_shadowing_lemma_missing_trajectories(mock_baseline):
    """Test error when trajectories are missing."""
    config = {
        'N': 2,
        'dt': 0.01,
        'data_dir': str(mock_baseline.parent.parent)
    }
    
    with pytest.raises(ShadowingCheckError, match="Trajectory file not found"):
        validate_shadowing_lemma(
            trajectory_id='nonexistent',
            noise_level=0.001,
            config=config,
            data_dir=mock_baseline.parent.parent
        )

def test_run_shadowing_check_batch(mock_baseline, mock_trajectory_files):
    """Test batch shadowing check."""
    config = {
        'N': 2,
        'dt': 0.01,
        'data_dir': str(mock_trajectory_files)
    }
    
    trajectory_ids = ['test']
    noise_levels = [0.001]
    
    results = run_shadowing_check_batch(
        trajectory_ids=trajectory_ids,
        noise_levels=noise_levels,
        config=config,
        data_dir=mock_trajectory_files
    )
    
    assert 'test' in results
    assert isinstance(results['test'], ShadowingResult)

def test_gate_for_ftle_calculation_pass():
    """Test FTLE gate passes when shadowing rate is sufficient."""
    results = {
        'traj1': ShadowingResult(
            is_shadowing=True,
            divergence_rate=0.74,
            baseline_lambda_max=0.75,
            deviation_ratio=0.013,
            shadowing_tolerance=0.1,
            message="Test",
            trajectory_id='traj1',
            noise_level=0.001
        ),
        'traj2': ShadowingResult(
            is_shadowing=True,
            divergence_rate=0.76,
            baseline_lambda_max=0.75,
            deviation_ratio=0.013,
            shadowing_tolerance=0.1,
            message="Test",
            trajectory_id='traj2',
            noise_level=0.001
        )
    }
    
    assert gate_for_ftle_calculation(results, required_shadowing_rate=0.8) is True

def test_gate_for_ftle_calculation_fail():
    """Test FTLE gate fails when shadowing rate is insufficient."""
    results = {
        'traj1': ShadowingResult(
            is_shadowing=False,
            divergence_rate=0.9,
            baseline_lambda_max=0.75,
            deviation_ratio=0.2,
            shadowing_tolerance=0.1,
            message="Test",
            trajectory_id='traj1',
            noise_level=0.001
        ),
        'traj2': ShadowingResult(
            is_shadowing=False,
            divergence_rate=0.95,
            baseline_lambda_max=0.75,
            deviation_ratio=0.27,
            shadowing_tolerance=0.1,
            message="Test",
            trajectory_id='traj2',
            noise_level=0.001
        )
    }
    
    with pytest.raises(ShadowingCheckError, match="Shadowing check failed"):
        gate_for_ftle_calculation(results, required_shadowing_rate=0.8)

def test_gate_for_ftle_calculation_empty():
    """Test FTLE gate fails with no results."""
    with pytest.raises(ShadowingCheckError, match="No shadowing results"):
        gate_for_ftle_calculation({}, required_shadowing_rate=0.8)

def test_shadowing_result_dataclass():
    """Test ShadowingResult dataclass creation."""
    result = ShadowingResult(
        is_shadowing=True,
        divergence_rate=0.74,
        baseline_lambda_max=0.75,
        deviation_ratio=0.013,
        shadowing_tolerance=0.1,
        message="Test message",
        trajectory_id='test_id',
        noise_level=0.001
    )
    
    assert result.is_shadowing is True
    assert result.trajectory_id == 'test_id'
    assert result.noise_level == 0.001
    assert result.baseline_lambda_max == 0.75
    assert result.divergence_rate == 0.74
    assert result.deviation_ratio == 0.013
    assert result.shadowing_tolerance == 0.1
    assert result.message == "Test message"