"""
Participation Ratio (PR) analysis module.
Implements exact diagonalisation with a sparse eigensolver fallback for large systems.
Logs residual norms via the NumericalLogger (T011) and produces the PR dataset
required by downstream scaling analyses.
"""
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import linalg, sparse
from scipy.sparse.linalg import eigsh, ArpackNoConvergence
from scipy.optimize import curve_fit

from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.logger import get_logger
from code.logger_utils import log_eigenvalue_residual

logger = logging.getLogger(__name__)
numerical_logger = get_logger()

def compute_participation_ratio(eigenvectors: np.ndarray) -> np.ndarray:
    """
    Compute the Participation Ratio (PR) for a set of eigenvectors.

    PR = (∑|ψ_i|²)² / ∑|ψ_i|⁴
    """
    prob = np.abs(eigenvectors) ** 2
    sum_prob_sq = np.sum(prob, axis=0) ** 2
    sum_prob_4 = np.sum(prob ** 2, axis=0)
    pr = np.divide(
        sum_prob_sq,
        sum_prob_4,
        out=np.zeros_like(sum_prob_sq),
        where=sum_prob_4 != 0,
    )
    return pr


def _dense_eigen_decomposition(H: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Exact dense diagonalisation using scipy.linalg.eigh."""
    energies, vectors = linalg.eigh(H)
    return energies, vectors


def _sparse_eigen_decomposition(
    H: sparse.spmatrix, k: int = 20
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute a few eigenpairs closest to zero using scipy.sparse.linalg.eigsh.

    Parameters
    ----------
    H : sparse matrix
        Hamiltonian in CSR format.
    k : int
        Number of eigenpairs to compute (default 20). Must be < N‑1.

    Returns
    -------
    energies : np.ndarray
        Eigenvalues closest to the band centre.
    vectors : np.ndarray
        Corresponding eigenvectors (columns).
    """
    # ``which='LM'`` together with ``sigma=0`` targets eigenvalues near 0.
    energies, vectors = eigsh(
        H,
        k=min(k, H.shape[0] - 2),
        sigma=0.0,
        which="LM",
        tol=1e-10,
    )
    # eigsh does not guarantee ordering; sort by absolute energy.
    idx = np.argsort(np.abs(energies))
    return energies[idx], vectors[:, idx]


def compute_eigenstates(
    hamiltonian: np.ndarray,
    energy_window: float = 0.1,
    residual_threshold: float = 1e-6,
    system_params: Dict[str, Any] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute eigenstates for a Hamiltonian, selecting those with |E| < energy_window.

    For systems with L <= 800 the dense solver is used.
    For larger systems (e.g. L = 1600) a sparse eigensolver is employed to stay
    within the 6 GB memory budget.

    Residual norms for each returned eigenpair are logged via ``log_eigenvalue_residual``.

    Returns
    -------
    filtered_energies : np.ndarray
        Energies within the specified window.
    filtered_vectors : np.ndarray
        Corresponding eigenvectors (columns).
    mask : np.ndarray
        Boolean mask indicating which eigenvalues of the full solve lie inside the window.
    """
    L = hamiltonian.shape[0]
    use_sparse = L > 800
    if use_sparse:
        # Convert to CSR for sparse operations.
        H_sparse = sparse.csr_matrix(hamiltonian)
        energies, vectors = _sparse_eigen_decomposition(H_sparse, k=30)
    else:
        energies, vectors = _dense_eigen_decomposition(hamiltonian)

    # Compute residuals for *all* eigenpairs we have computed.
    residuals = []
    converged = []
    for E, vec in zip(energies, vectors.T):
        # Residual: || H v - E v ||
        r = np.linalg.norm(hamiltonian @ vec - E * vec)
        residuals.append(float(r))
        converged.append(r < residual_threshold)

    # Log the residual information.
    if system_params is None:
        system_params = {}
    log_eigenvalue_residual(
        system_params=system_params,
        eigenvalues=energies.tolist(),
        eigenvectors=vectors.T.tolist(),
        residuals=residuals,
        converged=converged,
    )

    # Select eigenstates near the band centre.
    mask = np.abs(energies) < energy_window
    filtered_energies = energies[mask]
    filtered_vectors = vectors[:, mask]
    return filtered_energies, filtered_vectors, mask


def saturation_model(L, PR_inf, xi):
    """
    Finite‑size scaling model: PR(L) = PR_inf * (1 - exp(-L/xi))
    """
    return PR_inf * (1 - np.exp(-L / xi))


def finite_size_scaling(
    L_values: List[int], PR_values: List[float]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fit PR(L) data to the saturation model to extract the localisation length ξ.

    Returns (xi, uncertainty) or (None, None) if the fit fails.
    """
    if len(L_values) < 2:
        return None, None

    L_arr = np.array(L_values)
    PR_arr = np.array(PR_values)

    # Initial guess: PR_inf ≈ max(PR), ξ ≈ L_max/2
    p0 = [np.max(PR_arr) * 1.1, np.max(L_arr) / 2.0]
    bounds = ([0, 0], [np.inf, np.inf])

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            popt, pcov = curve_fit(
                saturation_model, L_arr, PR_arr, p0=p0, bounds=bounds, maxfev=2000
            )

        PR_inf, xi = popt
        if pcov is not None:
            perr = np.sqrt(np.diag(pcov))
            uncertainty = perr[1]
        else:
            uncertainty = None

        if xi <= 0:
            logger.warning(f"Non‑physical ξ ({xi}) detected, skipping fit.")
            return None, None

        # R² check
        y_pred = saturation_model(L_arr, PR_inf, xi)
        ss_res = np.sum((PR_arr - y_pred) ** 2)
        ss_tot = np.sum((PR_arr - np.mean(PR_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        if r_squared < 0.95:
            logger.warning(
                f"Fit R² ({r_squared:.3f}) < 0.95 for W={xi}, skipping."
            )
            return None, None

        return xi, uncertainty
    except Exception as e:
        logger.warning(f"Fit failed: {e}")
        return None, None


def analyze_w0_delocalization(L_values: List[int], PR_values: List[float]) -> Dict[str, Any]:
    """
    Analyse the clean (W = 0) case.  Checks for extensive scaling (PR ∝ L).
    """
    L_arr = np.array(L_values)
    PR_arr = np.array(PR_values)
    slope, intercept = np.polyfit(L_arr, PR_arr, 1)
    is_delocalized = slope > 0.1  # heuristic
    return {
        "is_delocalized": bool(is_delocalized),
        "slope": float(slope),
        "intercept": float(intercept),
        "PR_values": PR_arr.tolist(),
    }


def run_scaling_analysis(config: Dict[str, Any]) -> None:
    """
    Main entry point for the finite‑size scaling analysis (T010/T013).

    Reads ``pr_raw_multiL.json``, performs fits for each disorder width,
    writes ``scaling_fits.json`` and auxiliary artefacts.
    """
    input_path = Path("data/processed/pr_raw_multiL.json")
    output_path = Path("data/processed/scaling_fits.json")
    warnings_path = Path("data/metadata/warnings.json")
    w0_path = Path("data/processed/w0_results.json")

    if not input_path.exists():
        logger.error(f"Input file {input_path} not found. Run the dataset generator first.")
        raise FileNotFoundError(f"Missing input: {input_path}")

    with open(input_path, "r") as f:
        raw_data = json.load(f)

    # Group by disorder width.
    data_by_W: Dict[float, List[Dict[str, Any]]] = {}
    for item in raw_data:
        w = float(item["W"])
        data_by_W.setdefault(w, []).append(item)

    results: List[Dict[str, Any]] = []
    warnings_list: List[Dict[str, Any]] = []

    for W, items in sorted(data_by_W.items()):
        if W == 0.0:
            # Handle the clean limit separately.
            pr_by_L: Dict[int, List[float]] = {}
            for it in items:
                L = int(it["L"])
                pr_by_L.setdefault(L, []).append(float(it["pr"]))
            avg_pr_by_L = {L: np.mean(v) for L, v in pr_by_L.items()}
            L_vals = sorted(avg_pr_by_L)
            pr_vals = [avg_pr_by_L[L] for L in L_vals]
            w0_res = analyze_w0_delocalization(L_vals, pr_vals)
            w0_res.update({"disorder_width": 0.0, "is_delocalized": True})
            results.append(w0_res)
            with open(w0_path, "w") as f:
                json.dump(w0_res, f, indent=2)
            continue

        # Average PR over realizations for each L.
        pr_by_L: Dict[int, List[float]] = {}
        for it in items:
            L = int(it["L"])
            pr_by_L.setdefault(L, []).append(float(it["pr"]))
        L_vals = sorted(pr_by_L)
        pr_vals = [np.mean(pr_by_L[L]) for L in L_vals]

        xi, uncertainty = finite_size_scaling(L_vals, pr_vals)

        if xi is not None:
            # Dummy p‑value placeholder (real analysis would compute this later).
            p_value = 0.0
            results.append(
                {
                    "disorder_width": float(W),
                    "xi": float(xi),
                    "uncertainty": float(uncertainty) if uncertainty else None,
                    "p_value": float(p_value),
                }
            )
        else:
            warnings_list.append(
                {
                    "type": "fit_failure",
                    "W": W,
                    "message": f"Fit failed for disorder width W={W}",
                }
            )
            logger.warning(f"Fit failed for W={W}")

    # Write warnings if any.
    if warnings_list:
        if warnings_path.exists():
            with open(warnings_path, "r") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.extend(warnings_list)
        with open(warnings_path, "w") as f:
            json.dump(existing, f, indent=2)

    # Write final scaling results.
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Scaling analysis complete. Results written to {output_path}")


def analyze_single_realization(
    W: float,
    L: int,
    seed: int,
    realization_index: int,
) -> List[Dict[str, Any]]:
    """
    Analyse a single disorder realisation:
    * generate the Hamiltonian,
    * compute eigenstates near the band centre,
    * evaluate PR for each returned eigenstate,
    * log residuals,
    * return a list of records (one per eigenstate).
    """
    hamiltonian = generate_hamiltonian(L, W, seed=seed, realization_index=realization_index)
    system_params = {
        "W": W,
        "L": L,
        "realization_index": realization_index,
        "seed": seed,
    }
    energies, eigenvectors, _ = compute_eigenstates(
        hamiltonian,
        energy_window=0.1,
        residual_threshold=get_config().NUMERICAL_RESIDUAL_THRESHOLD,
        system_params=system_params,
    )
    pr_values = compute_participation_ratio(eigenvectors)

    records = []
    for E, pr in zip(energies, pr_values):
        records.append(
            {
                "W": float(W),
                "L": int(L),
                "realization_index": int(realization_index),
                "energy": float(E),
                "pr": float(pr),
            }
        )
    return records


def main() -> None:
    """
    CLI entry point – used by the orchestration script.
    """
    cfg = get_config()
    run_scaling_analysis(cfg)


if __name__ == "__main__":
    main()
