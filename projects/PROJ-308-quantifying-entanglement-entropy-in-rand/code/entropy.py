"""
Entanglement entropy computation module for 1D quantum spin chains.

This module implements the calculation of von Neumann entanglement entropy
S(l) = -Tr(rho_l * log(rho_l)) for all bipartitions l across a system of size L,
given a ground state wavefunction.

It supports both exact diagonalization (for small systems) and TEBD-derived
matrix product states (for larger systems).

FR-004: Compute von Neumann entropy S(l) for all bipartitions l across the system per realization.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from scipy.sparse import csr_matrix, kron, identity, diags
from scipy.sparse.linalg import eigs
from scipy.linalg import eigvalsh
import warnings


class EntropyError(Exception):
    """Custom exception for entropy computation errors."""
    pass


def _compute_reduced_density_matrix(psi: np.ndarray, L: int, l: int) -> np.ndarray:
    """
    Compute the reduced density matrix for a bipartition at cut l.

    Parameters
    ----------
    psi : np.ndarray
        Ground state wavefunction as a 1D array of length 2^L (for spin-1/2).
    L : int
        Total system size.
    l : int
        Size of the subsystem (cut after site l, so subsystem has sites 0..l-1).

    Returns
    -------
    np.ndarray
        Reduced density matrix of shape (2^l, 2^l).
    """
    if l <= 0 or l >= L:
        raise EntropyError(f"Invalid bipartition size l={l} for system L={L}. Must have 0 < l < L.")

    dim_A = 2 ** l
    dim_B = 2 ** (L - l)

    # Reshape psi into a matrix of shape (dim_A, dim_B)
    psi_matrix = psi.reshape((dim_A, dim_B))

    # rho_A = psi_matrix @ psi_matrix.T (trace out B)
    rho_A = psi_matrix @ psi_matrix.T

    return rho_A


def _compute_entropy_from_densities(eigenvalues: np.ndarray) -> float:
    """
    Compute von Neumann entropy from eigenvalues of the reduced density matrix.

    S = - sum(lambda_i * log(lambda_i)) for lambda_i > 0.

    Parameters
    ----------
    eigenvalues : np.ndarray
        Eigenvalues of the reduced density matrix.

    Returns
    -------
    float
        Von Neumann entropy.
    """
    # Filter out zero or negative eigenvalues (numerical noise)
    pos_eigs = eigenvalues[eigenvalues > 1e-12]

    if len(pos_eigs) == 0:
        warnings.warn("All eigenvalues are zero or negative. Returning 0 entropy.")
        return 0.0

    # S = - sum(p log p)
    entropy = -np.sum(pos_eigs * np.log(pos_eigs))

    return float(entropy)


def compute_entanglement_entropy(
    psi: np.ndarray,
    L: int,
    l: int,
    method: str = "exact"
) -> float:
    """
    Compute the von Neumann entanglement entropy S(l) for a single bipartition.

    Parameters
    ----------
    psi : np.ndarray
        Ground state wavefunction. For exact diagonalization, shape (2^L,).
        For MPS, this would be the full wavefunction reconstructed or accessed via MPS.
    L : int
        Total system size.
    l : int
        Size of the subsystem (cut after site l).
    method : str
        Computation method. Currently only "exact" is supported.

    Returns
    -------
    float
        Von Neumann entropy S(l).

    Raises
    ------
    EntropyError
        If input dimensions are inconsistent or method is unsupported.
    """
    if method != "exact":
        raise EntropyError(f"Unsupported method '{method}'. Only 'exact' is implemented.")

    expected_dim = 2 ** L
    if psi.shape[0] != expected_dim:
        raise EntropyError(
            f"Wavefunction dimension mismatch: expected {expected_dim}, got {psi.shape[0]}"
        )

    rho_A = _compute_reduced_density_matrix(psi, L, l)

    # Compute eigenvalues of the reduced density matrix
    eigenvalues = np.linalg.eigvalsh(rho_A)

    entropy = _compute_entropy_from_densities(eigenvalues)

    return entropy


def compute_entanglement_entropy_batch(
    psi: np.ndarray,
    L: int,
    cuts: Optional[List[int]] = None
) -> Dict[int, float]:
    """
    Compute entanglement entropy for all (or specified) bipartitions.

    Parameters
    ----------
    psi : np.ndarray
        Ground state wavefunction of shape (2^L,).
    L : int
        Total system size.
    cuts : list of int, optional
        List of bipartition sizes l to compute. If None, computes for all 1 <= l < L.

    Returns
    -------
    dict
        Dictionary mapping cut size l to entropy S(l).

    Raises
    ------
    EntropyError
        If psi dimension is invalid.
    """
    expected_dim = 2 ** L
    if psi.shape[0] != expected_dim:
        raise EntropyError(
            f"Wavefunction dimension mismatch: expected {expected_dim}, got {psi.shape[0]}"
        )

    if cuts is None:
        cuts = list(range(1, L))

    results = {}
    for l in cuts:
        try:
            entropy = compute_entanglement_entropy(psi, L, l, method="exact")
            results[l] = entropy
        except EntropyError as e:
            warnings.warn(f"Failed to compute entropy for l={l}: {e}")
            results[l] = np.nan

    return results


def get_entropy_statistics(
    entropy_values: List[float]
) -> Dict[str, float]:
    """
    Compute summary statistics for a list of entropy values.

    Parameters
    ----------
    entropy_values : list of float
        List of entropy values (e.g., from multiple realizations).

    Returns
    -------
    dict
        Dictionary with keys: 'mean', 'std', 'min', 'max', 'count', 'nan_count'.
    """
    arr = np.array(entropy_values)
    non_nan = arr[~np.isnan(arr)]

    if len(non_nan) == 0:
        return {
            'mean': np.nan,
            'std': np.nan,
            'min': np.nan,
            'max': np.nan,
            'count': 0,
            'nan_count': len(arr)
        }

    return {
        'mean': float(np.mean(non_nan)),
        'std': float(np.std(non_nan)),
        'min': float(np.min(non_nan)),
        'max': float(np.max(non_nan)),
        'count': len(non_nan),
        'nan_count': int(np.sum(np.isnan(arr)))
    }


def verify_scaling_ansatz(
    l_values: List[int],
    s_values: List[float],
    model: str = "log"
) -> Dict[str, float]:
    """
    Verify the scaling ansatz S(l) ~ c * log(l) or S(l) ~ constant (area law).

    Parameters
    ----------
    l_values : list of int
        List of bipartition sizes.
    s_values : list of float
        Corresponding entropy values.
    model : str
        Model to fit: 'log' for logarithmic scaling, 'const' for area law.

    Returns
    -------
    dict
        Dictionary with fit parameters and goodness-of-fit metrics.
    """
    l_arr = np.array(l_values)
    s_arr = np.array(s_values)

    # Filter out NaNs
    valid_mask = ~np.isnan(s_arr)
    l_valid = l_arr[valid_mask]
    s_valid = s_arr[valid_mask]

    if len(l_valid) < 2:
        raise EntropyError("Not enough valid data points to fit scaling ansatz.")

    if model == "log":
        # Fit S = c * log(l) + b
        log_l = np.log(l_valid)
        A = np.vstack([log_l, np.ones(len(log_l))]).T
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(A, s_valid, rcond=None)
            c_eff, b = coeffs
            # Compute R^2
            s_pred = c_eff * log_l + b
            ss_res = np.sum((s_valid - s_pred) ** 2)
            ss_tot = np.sum((s_valid - np.mean(s_valid)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        except Exception as e:
            raise EntropyError(f"Log fit failed: {e}")

    elif model == "const":
        # Fit S = b (constant)
        b = np.mean(s_valid)
        s_pred = np.full_like(s_valid, b)
        ss_res = np.sum((s_valid - s_pred) ** 2)
        ss_tot = np.sum((s_valid - np.mean(s_valid)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        c_eff = 0.0
    else:
        raise EntropyError(f"Unknown model '{model}'. Use 'log' or 'const'.")

    return {
        'c_eff': float(c_eff),
        'intercept': float(b),
        'r_squared': float(r_squared),
        'model': model,
        'n_points': len(l_valid)
    }
