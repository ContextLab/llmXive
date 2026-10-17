import numpy as np

def generate_wigner_matrix(N: int, seed: int) -> np.ndarray:
    """
    Generate a Wigner matrix with standard scaling (1/sqrt(N)).
    The matrix is symmetric: W = (A + A^T) / sqrt(2N) where A is i.i.d. N(0,1).
    """
    np.random.seed(seed)
    A = np.random.randn(N, N)
    W = (A + A.T) / np.sqrt(2 * N)
    return W
