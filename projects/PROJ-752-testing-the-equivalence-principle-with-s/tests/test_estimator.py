import pytest
import numpy as np
from models.estimator import OrbitSolution, extract_joint_parameters, AnalysisError

def test_extract_joint_parameters_success():
    """
    Test successful extraction of ac and g from a converged solution.
    """
    # Mock solution data
    r_vec = np.array([6771000.0, 0.0, 0.0]) # ~6771 km (LAGEOS orbit ~ 12200km, but just for test)
    params = np.array([1.5e-10]) # ac = 1.5e-10 m/s^2
    cov = np.array([[1.0e-20]]) # Covariance
    
    solution = OrbitSolution(
        state={'r': r_vec, 'v': np.zeros(3)},
        parameters=params,
        covariance=cov,
        converged=True,
        message="Optimization converged",
        cost=0.1
    )
    
    result = extract_joint_parameters(solution)
    
    assert 'ac' in result
    assert 'g' in result
    assert 'covariance' in result
    
    # Verify g calculation: GM = 3.986e14, r = 6.771e6
    # g = 3.986e14 / (6.771e6)^2
    expected_g = 3.986004418e14 / (6771000.0 ** 2)
    assert np.isclose(result['g'], expected_g)
    assert np.isclose(result['ac'], 1.5e-10)
    assert isinstance(result['covariance'], np.ndarray)

def test_extract_joint_parameters_non_converged():
    """
    Test extraction from a non-converged solution (should still work but log warning).
    """
    r_vec = np.array([6771000.0, 0.0, 0.0])
    params = np.array([2.0e-10])
    cov = np.array([[2.0e-20]])
    
    solution = OrbitSolution(
        state={'r': r_vec},
        parameters=params,
        covariance=cov,
        converged=False,
        message="Max iterations reached",
        cost=5.0
    )
    
    # Should not raise an error, just a warning
    result = extract_joint_parameters(solution)
    
    assert result['ac'] == 2.0e-10
    assert result['g'] > 0

def test_extract_joint_parameters_missing_keys():
    """
    Test extraction when 'r' is missing from solution.state.
    """
    solution = OrbitSolution(
        state={'v': np.zeros(3)}, # Missing 'r'
        parameters=np.array([1.0e-10]),
        covariance=np.array([[1.0e-20]]),
        converged=True,
        message="Done",
        cost=0.0
    )
    
    with pytest.raises(AnalysisError) as exc_info:
        extract_joint_parameters(solution)
    
    assert "Missing 'r'" in str(exc_info.value)

def test_extract_joint_parameters_zero_position():
    """
    Test extraction when position vector magnitude is zero.
    """
    solution = OrbitSolution(
        state={'r': np.array([0.0, 0.0, 0.0])},
        parameters=np.array([1.0e-10]),
        covariance=np.array([[1.0e-20]]),
        converged=True,
        message="Done",
        cost=0.0
    )
    
    with pytest.raises(AnalysisError) as exc_info:
        extract_joint_parameters(solution)
    
    assert "magnitude is zero" in str(exc_info.value)

def test_extract_joint_parameters_empty_params():
    """
    Test extraction when parameters array is empty.
    """
    solution = OrbitSolution(
        state={'r': np.array([6771000.0, 0.0, 0.0])},
        parameters=np.array([]),
        covariance=np.array([[1.0e-20]]),
        converged=True,
        message="Done",
        cost=0.0
    )
    
    with pytest.raises(AnalysisError) as exc_info:
        extract_joint_parameters(solution)
    
    assert "parameters are empty" in str(exc_info.value)