"""
Unit tests for the Joint Least-Squares Estimator (T024).

These tests verify the interface and basic functionality of the joint fitting
routine without requiring a full data ingestion pipeline.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module under test
from models.estimator import run_joint_fit, OrbitSolution, extract_joint_parameters
from utils.logging import AnalysisError

@pytest.fixture
def mock_observations():
    """Create mock SLR observations for two satellites."""
    # Create dummy dataframes
    n_points = 100
    time_idx = np.arange(n_points)
    
    df_lageos1 = pd.DataFrame({
        'time': time_idx,
        'range': np.random.normal(12270000.0, 0.02, n_points), # ~12270 km
        'weight': np.ones(n_points)
    })
    
    df_lageos2 = pd.DataFrame({
        'time': time_idx,
        'range': np.random.normal(12270000.0, 0.02, n_points),
        'weight': np.ones(n_points)
    })
    
    return {
        'LAGEOS-1': df_lageos1,
        'LAGEOS-2': df_lageos2
    }

@pytest.fixture
def mock_initial_states():
    """Create mock initial state vectors."""
    # State vector: [x, y, z, vx, vy, vz]
    # LAGEOS orbit ~ 12270 km radius
    r = 12270000.0
    v = 3000.0 # Approximate orbital velocity
    
    state1 = np.array([r, 0, 0, 0, v, 0])
    state2 = np.array([0, r, 0, -v, 0, 0])
    
    return {
        'LAGEOS-1': state1,
        'LAGEOS-2': state2
    }

def test_run_joint_fit_interface(mock_observations, mock_initial_states):
    """Test that run_joint_fit returns an OrbitSolution object."""
    # We need to mock the heavy dynamics/integration parts to avoid
    # needing a full physics engine in this unit test.
    
    with patch('models.estimator._build_joint_residual_vector') as mock_residual:
        # Mock the residual function to return a zero vector (perfect fit)
        # to ensure convergence
        total_len = len(mock_observations['LAGEOS-1']) + len(mock_observations['LAGEOS-2'])
        mock_residual.return_value = np.zeros(total_len)
        
        solution = run_joint_fit(mock_observations, mock_initial_states)
        
        assert isinstance(solution, OrbitSolution)
        assert solution.success is True
        assert 'LAGEOS-1' in solution.states
        assert 'LAGEOS-2' in solution.states
        assert 'ac' in solution.params

def test_extract_joint_parameters(mock_observations, mock_initial_states):
    """Test extraction of ac and g from a solution."""
    # Create a mock solution
    solution = OrbitSolution(
        satellite_ids=['LAGEOS-1', 'LAGEOS-2'],
        states=mock_initial_states,
        params={'ac': 1.5e-12},
        covariance=np.eye(13), # 6+6+1 params
        residuals=np.zeros(200),
        cost=0.0,
        success=True,
        message="Optimization terminated successfully",
        iterations=10
    )
    
    result = extract_joint_parameters(solution)
    
    assert 'ac' in result
    assert 'g' in result
    assert 'covariance' in result
    
    assert np.isclose(result['ac'], 1.5e-12)
    assert result['g'] > 0 # Gravity should be positive

def test_run_joint_fit_convergence_failure(mock_observations, mock_initial_states):
    """Test behavior when optimization fails (mocked)."""
    with patch('models.estimator.least_squares') as mock_ls:
        mock_ls.side_effect = Exception("Optimization failed")
        
        with pytest.raises(AnalysisError):
            run_joint_fit(mock_observations, mock_initial_states)

def test_joint_residual_vector_structure(mock_observations):
    """Test that the residual vector is correctly stacked."""
    # This tests the logic inside _build_joint_residual_vector
    # We mock the dynamics and state parts to focus on stacking
    from models.estimator import _build_joint_residual_vector
    from models.dynamics import DynamicsModel
    
    mock_states = {
        'LAGEOS-1': np.array([1.0, 0, 0, 0, 0, 0]),
        'LAGEOS-2': np.array([0, 1.0, 0, 0, 0, 0])
    }
    mock_params = {'ac': 0.0}
    
    with patch('models.estimator._compute_predicted_ranges') as mock_pred:
        # Return zeros to simulate perfect prediction for structure test
        mock_pred.return_value = np.zeros(len(mock_observations['LAGEOS-1']))
        
        model = DynamicsModel()
        time_grid = np.array([])
        
        res = _build_joint_residual_vector(
            mock_states, mock_params, mock_observations, model, time_grid
        )
        
        expected_len = len(mock_observations['LAGEOS-1']) + len(mock_observations['LAGEOS-2'])
        assert len(res) == expected_len
        # Check that it's a numpy array
        assert isinstance(res, np.ndarray)
