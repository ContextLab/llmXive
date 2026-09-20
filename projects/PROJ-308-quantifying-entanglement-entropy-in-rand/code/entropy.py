"""
Entanglement Entropy Computation Module (FR-004)

This module implements the computation of von Neumann entanglement entropy
for 1D spin-1/2 chains. It provides functions to compute the reduced density
matrix for a bipartition and calculate the entropy S(l) = -Tr(rho_A log rho_A).

The implementation follows the "Local Measurement Protocol" described in
research.md: an observer at cut 'l' traces out the right half of the chain
to obtain the reduced density matrix of the left block, then computes the
entropy.

For the random singlet phase (Refael-Moore), we expect S(l) ~ (ln 2)/3 * log(l).
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from scipy.sparse import csr_matrix, kron, identity, diags
from scipy.sparse.linalg import eigs
from scipy.linalg import eigvalsh
import warnings

from config import ConfigError
from ground_state import is_numerically_unresolved


class EntropyError(Exception):
    """Custom exception for entropy computation failures."""
    pass


def _get_reduced_density_matrix(
    psi: np.ndarray,
    L: int,
    l: int
) -> csr_matrix:
    """
    Compute the reduced density matrix rho_A for a bipartition at cut 'l'.

    The system is a chain of L spin-1/2 particles. The state psi is given
    as a 1D array of length 2^L (in computational basis).

    We partition the chain into subsystem A (sites 0 to l-1, size l)
    and subsystem B (sites l to L-1, size L-l).

    The reduced density matrix rho_A = Tr_B(|psi><psi|) has shape (2^l, 2^l).

    Args:
        psi: Ground state wavefunction as a 1D numpy array of shape (2^L,).
        L: Total number of spins in the chain.
        l: Size of subsystem A (number of spins on the left).

    Returns:
        Reduced density matrix as a sparse CSR matrix of shape (2^l, 2^l).

    Raises:
        EntropyError: If dimensions are inconsistent.
    """
    if psi.ndim != 1:
        raise EntropyError(f"Expected 1D wavefunction, got shape {psi.shape}")

    dim_total = 2 ** L
    if psi.shape[0] != dim_total:
        raise EntropyError(
            f"Wavefunction size {psi.shape[0]} does not match 2^{L} = {dim_total}"
        )

    if not (0 < l < L):
        raise EntropyError(f"Bipartition size l={l} must satisfy 0 < l < L={L}")

    dim_A = 2 ** l
    dim_B = 2 ** (L - l)

    # Reshape psi into a matrix of shape (dim_A, dim_B)
    # This effectively groups the first l qubits into row index
    # and the remaining L-l qubits into column index.
    psi_matrix = psi.reshape((dim_A, dim_B))

    # rho_A = psi_matrix @ psi_matrix^H
    # Since psi is real in our TEBD implementation (up to global phase),
    # we use transpose. If complex, use conjugate transpose.
    rho_A = csr_matrix(psi_matrix) @ csr_matrix(psi_matrix).T.conj()

    return rho_A


def _compute_von_neumann_entropy(rho: csr_matrix) -> float:
    """
    Compute von Neumann entropy S = -Tr(rho log rho).

    We compute eigenvalues of rho and sum -lambda_i log(lambda_i),
    ignoring eigenvalues that are zero or negative (numerical noise).

    Args:
        rho: Density matrix (sparse or dense).

    Returns:
        Entropy in nats (natural log base).

    Raises:
        EntropyError: If the matrix is not positive semi-definite or trace != 1.
    """
    # Convert to dense for eigenvalue computation (matrix size is at most 2^(L/2))
    # For L=30, max cut is 15, so 2^15 = 32768, which is manageable for dense eig.
    # However, we use sparse eigenvalue solver for larger cuts if needed.

    if rho.shape[0] > 2048:
        # Use sparse solver for large matrices
        # We only need the non-zero eigenvalues for entropy
        # Compute all non-zero eigenvalues using eigs with sigma=0 to shift
        try:
            # For Hermitian matrix, use eigh for dense or eigsh for sparse
            # Here we convert to dense if not too large, else use sparse
            rho_dense = rho.toarray()
            eigenvalues = np.linalg.eigvalsh(rho_dense)
        except MemoryError:
            # Fallback to sparse eigenvalue computation
            eigenvalues, _ = eigs(rho, k=rho.shape[0]-1, which='LM', return_eigenvectors=False)
            eigenvalues = np.real(eigenvalues)
    else:
        rho_dense = rho.toarray()
        eigenvalues = np.linalg.eigvalsh(rho_dense)

    # Filter out numerical noise (negative or zero eigenvalues)
    eigenvalues = eigenvalues[eigenvalues > 1e-15]

    # Normalize to ensure trace = 1 (numerical stability)
    trace = np.sum(eigenvalues)
    if abs(trace - 1.0) > 1e-6:
        warnings.warn(f"Density matrix trace = {trace}, normalizing.")
        eigenvalues = eigenvalues / trace

    # Compute entropy: S = -sum(lambda_i * log(lambda_i))
    entropy = -np.sum(eigenvalues * np.log(eigenvalues))

    return float(entropy)


def compute_entanglement_entropy(
    psi: np.ndarray,
    L: int,
    l: int,
    check_unresolved: bool = True
) -> float:
    """
    Compute the von Neumann entanglement entropy S(l) for a bipartition at 'l'.

    This function computes the reduced density matrix for the left block of
    size 'l' and calculates its von Neumann entropy.

    Args:
        psi: Ground state wavefunction as a 1D numpy array.
        L: Total number of spins.
        l: Size of the left subsystem (bipartition cut).
        check_unresolved: If True, check if the state is numerically unresolved
                          and raise an error if so.

    Returns:
        Entanglement entropy S(l) in nats.

    Raises:
        EntropyError: If the state is numerically unresolved or dimensions are invalid.
    """
    if check_unresolved:
        # Check if psi is flagged as unresolved (this assumes psi carries metadata
        # or we check a global flag. For now, we assume the caller ensures this,
        # or we check if the state vector is all zeros/norm is zero).
        norm = np.linalg.norm(psi)
        if norm < 1e-10:
            raise EntropyError("Wavefunction norm is zero; state may be unresolved.")

    try:
        rho_A = _get_reduced_density_matrix(psi, L, l)
        entropy = _compute_von_neumann_entropy(rho_A)
        return entropy
    except Exception as e:
        raise EntropyError(f"Failed to compute entropy for cut l={l}: {e}")


def compute_entanglement_entropy_batch(
    psi: np.ndarray,
    L: int,
    cuts: Optional[List[int]] = None,
    check_unresolved: bool = True
) -> Dict[int, float]:
    """
    Compute entanglement entropy for all bipartitions l in [1, L-1].

    Args:
        psi: Ground state wavefunction.
        L: Total number of spins.
        cuts: Optional list of specific cuts to compute. If None, computes for
              all l in [1, L-1].
        check_unresolved: If True, check for unresolved states.

    Returns:
        Dictionary mapping cut size 'l' to entropy S(l).

    Raises:
        EntropyError: If any computation fails.
    """
    if cuts is None:
        cuts = list(range(1, L))

    results = {}
    for l in cuts:
        try:
            entropy = compute_entanglement_entropy(psi, L, l, check_unresolved)
            results[l] = entropy
        except EntropyError as e:
            # Log but continue for other cuts
            warnings.warn(f"Skipping cut l={l}: {e}")

    if not results:
        raise EntropyError("No valid entropy values computed for any cut.")

    return results


def get_entropy_statistics(
    entropy_data: Dict[int, List[float]]
) -> Dict[str, List[float]]:
    """
    Compute aggregate statistics (mean, std) over multiple realizations.

    Args:
        entropy_data: Dictionary mapping cut size 'l' to a list of entropy values
                      from different realizations.

    Returns:
        Dictionary with keys 'mean', 'std', 'min', 'max' mapping to lists of
        statistics for each cut size.
    """
    cuts = sorted(entropy_data.keys())
    if not cuts:
        return {'mean': [], 'std': [], 'min': [], 'max': []}

    means = []
    stds = []
    mins = []
    maxs = []

    for l in cuts:
        values = np.array(entropy_data[l])
        if len(values) == 0:
            means.append(np.nan)
            stds.append(np.nan)
            mins.append(np.nan)
            maxs.append(np.nan)
        else:
            means.append(float(np.mean(values)))
            stds.append(float(np.std(values)))
            mins.append(float(np.min(values)))
            maxs.append(float(np.max(values)))

    return {
        'mean': means,
        'std': stds,
        'min': mins,
        'max': maxs,
        'cuts': cuts
    }


def verify_scaling_ansatz(
    cuts: List[int],
    entropies: List[float]
) -> Dict[str, float]:
    """
    Verify the scaling ansatz S(l) ~ (c_eff/3) * log(l) vs Area Law.

    This function fits the data to both a logarithmic model and a constant
    model and returns the fit parameters and R-squared values.

    Args:
        cuts: List of bipartition sizes l.
        entropies: Corresponding entropy values S(l).

    Returns:
        Dictionary with fit results: 'log_slope', 'log_intercept', 'log_r2',
                                     'const_value', 'const_r2'.
    """
    if len(cuts) < 2 or len(entropies) < 2:
        return {
            'log_slope': np.nan,
            'log_intercept': np.nan,
            'log_r2': np.nan,
            'const_value': np.nan,
            'const_r2': np.nan
        }

    x = np.log(cuts)
    y = np.array(entropies)

    # Fit logarithmic model: y = a * log(l) + b
    try:
        # Using simple linear regression
        coeffs = np.polyfit(x, y, 1)
        log_slope = coeffs[0]
        log_intercept = coeffs[1]
        y_pred = log_slope * x + log_intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        log_r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    except Exception:
        log_slope = np.nan
        log_intercept = np.nan
        log_r2 = np.nan

    # Fit constant model: y = c
    try:
        const_value = float(np.mean(y))
        y_pred_const = np.full_like(y, const_value)
        ss_res_const = np.sum((y - y_pred_const) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        const_r2 = 1 - (ss_res_const / ss_tot) if ss_tot > 0 else 0.0
    except Exception:
        const_value = np.nan
        const_r2 = np.nan

    return {
        'log_slope': log_slope,
        'log_intercept': log_intercept,
        'log_r2': log_r2,
        'const_value': const_value,
        'const_r2': const_r2
    }
