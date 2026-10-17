import numpy as np

def generate_wigner_matrix(N: int, seed: int) -> np.ndarray:
    """
    Generate a symmetric Wigner matrix with standard scaling (1/sqrt(N)).
    W = (A + A^T) / sqrt(2*N) ensures off-diagonal variance is 1/N,
    leading to a semicircle edge at +/- 2.0.
    """
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((N, N))
    W = (A + A.T) / np.sqrt(2.0 * N)
    return W
