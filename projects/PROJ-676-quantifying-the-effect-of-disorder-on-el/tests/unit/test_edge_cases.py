import pytest
import numpy as np
from code.analyze_pr import compute_eigenstates, compute_participation_ratio
from code.logger import NumericalLogger

def test_W_zero_delocalized():
    """
    Test edge case: W=0 (delocalized states).
    PR should scale extensively with system size.
    """
    L = 100
    W = 0.0
    eps = np.zeros(L)
    H = np.diag(eps) + np.diag(np.ones(L-1), k=1) + np.diag(np.ones(L-1), k=-1)
    
    logger_instance = NumericalLogger()
    eigenvalues, eigenvectors = compute_eigenstates(H, W, 0, logger_instance)
    
    pr_values = compute_participation_ratio(eigenvectors, eigenvalues)
    
    # For delocalized states, PR should be proportional to L
    # We check that the average PR is significant (not saturating to 1)
    if pr_values:
        avg_pr = np.mean(list(pr_values.values()))
        assert avg_pr > 10, f"Expected delocalized PR > 10, got {avg_pr}"
    else:
        pytest.skip("No states in energy window")
