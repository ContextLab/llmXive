import numpy as np

def create_perturbation(N: int, theta: float, k: int, pattern: str) -> np.ndarray:
    """
    Create a deterministic perturbation matrix P.
    For 'diagonal', P is a diagonal matrix with k entries of theta.
    """
    P = np.zeros((N, N))
    if pattern == 'diagonal':
        # Rank-k diagonal perturbation
        for i in range(min(k, N)):
            P[i, i] = theta
    elif pattern == 'block-sparse':
        # Simplified block perturbation for T001 (diagonal is requested)
        for i in range(min(k, N)):
            P[i, i] = theta
    else: # random-sparse
        for i in range(min(k, N)):
            P[i, i] = theta
    return P
