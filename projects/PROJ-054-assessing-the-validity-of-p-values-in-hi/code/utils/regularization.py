import numpy as np
from typing import Tuple, Optional
from .exceptions import HighDimensionalInstabilityError

def is_condition_number_acceptable(condition_number: float, threshold: float = 1e12) -> bool:
    return condition_number < threshold

def regularize_covariance(cov_matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """
    Regularize a covariance matrix by adding epsilon to the diagonal.
    Raises HighDimensionalInstabilityError if condition number is too high after regularization.
    """
    reg_cov = cov_matrix + epsilon * np.eye(cov_matrix.shape[0])
    
    # Check condition number
    try:
        cond = np.linalg.cond(reg_cov)
        if not is_condition_number_acceptable(cond):
            raise HighDimensionalInstabilityError(f"Condition number {cond} exceeds threshold after regularization")
    except np.linalg.LinAlgError:
        raise HighDimensionalInstabilityError("Singular matrix after regularization")
    
    return reg_cov
