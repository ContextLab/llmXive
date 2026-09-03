import pytest
import numpy as np
from models.estimator import OrbitSolution, extract_joint_parameters, AnalysisError

def test_extract_joint_parameters_success():
    """Test successful extraction of joint parameters."""
    # Create a mock OrbitSolution
    cov = np.array([[1e-24, 0.0], [0.0, 1e-6]])
    params = {'ac': 1.5e-13, 'g': 9.81}
    
    solution = OrbitSolution(
        states=np.array([]),
        residuals=np.array([]),
        covariance=cov,
        parameters=params,
        success=True,
        message="Converged",
        cost=0.0
    )
    
    result = extract_joint_parameters(solution)
    
    assert result['ac'] == params['ac']
    assert result['g'] == params['g']
    assert np.allclose(result['covariance'], cov)

def test_extract_joint_parameters_non_converged():
    """Test extraction fails for non-converged solution."""
    solution = OrbitSolution(
        states=np.array([]),
        residuals=np.array([]),
        covariance=np.eye(2),
        parameters={'ac': 0.0, 'g': 0.0},
        success=False,
        message="Max iterations reached",
        cost=1.0
    )
    
    with pytest.raises(AnalysisError, match="non-converged solution"):
        extract_joint_parameters(solution)

def test_extract_joint_parameters_missing_keys():
    """Test extraction fails if required parameters are missing."""
    solution = OrbitSolution(
        states=np.array([]),
        residuals=np.array([]),
        covariance=np.eye(2),
        parameters={'ac': 1.0}, # Missing 'g'
        success=True,
        message="Converged",
        cost=0.0
    )
    
    with pytest.raises(AnalysisError, match="missing required parameters"):
        extract_joint_parameters(solution)