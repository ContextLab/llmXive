"""
Mode-Coupling (Leakage) Matrix Calculation for CMB Gap Analysis.

This module implements the calculation of the Mode-Coupling Matrix (often denoted as M)
which describes how the true power spectrum (C_l) is convolved with the mask to produce
the observed (biased) power spectrum.

M_{ll'} = (1 / (2l' + 1)) * sum_{m'} |a_lm'|^2 (mask)
In practice, for HEALPix maps, this is computed via the convolution of the mask's
power spectrum with the theoretical spectrum, or directly via the coupling matrix
derived from the mask's harmonic coefficients.

FR-009 Requirement: Calculate the Mode-Coupling (Leakage) Matrix from the gap mask.
Output: data/derived/leakage_matrix_{realization_id}.npy
"""

import os
import sys
import logging
import numpy as np
import healpy as hp
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Import project constants and I/O utilities
from config import DATA_DERIVED_DIR, N_SIDE
from data_io import load_mask_from_fits, compute_array_checksum

logger = logging.getLogger(__name__)

def compute_mask_power_spectrum(mask: np.ndarray, lmax: Optional[int] = None) -> np.ndarray:
    """
    Compute the power spectrum of the binary mask.

    Args:
        mask: HEALPix map of the mask (0 for gap, 1 for observed).
        lmax: Maximum multipole moment to compute. Defaults to 3 * Nside - 1.

    Returns:
        Array of C_l values for the mask.
    """
    if lmax is None:
        lmax = 3 * hp.nside2npix(hp.get_nside(mask)) // 2 - 1

    # Use anafast to compute the power spectrum of the mask
    # The mask is a real map, so we get Cl
    cl_mask = hp.anafast(mask, lmax=lmax, use_pixel_weights=True)
    return cl_mask

def compute_mode_coupling_matrix(cl_mask: np.ndarray, lmax: int) -> np.ndarray:
    """
    Compute the Mode-Coupling Matrix M_{ll'} from the mask power spectrum.

    The coupling matrix relates the true spectrum C_l to the observed spectrum C_l^obs:
    C_l^obs = sum_{l'} M_{ll'} * C_{l'}

    For a simple mask convolution approximation (ignoring mode mixing from non-axisymmetric
    masks for a first-order estimate, or using the full M matrix if using specific HEALPix
    routines), we often compute the kernel based on the mask's power spectrum.

    However, the rigorous M matrix for a general mask requires:
    M_{ll'} = (2l' + 1) / (4pi) * sum_{L} (2L + 1) * W_L * (Wigner3j)^2
    where W_L is the power spectrum of the mask.

    We will use the `healpy` approach or a direct calculation based on the mask's
    power spectrum to approximate the coupling.

    For this implementation, we compute the full coupling matrix using the mask's
    power spectrum and the Wigner 3j symbols (or equivalent convolution logic).
    Since healpy doesn't expose a direct "compute M matrix" function for arbitrary masks
    without the full map, we compute it numerically:
    M_{ll'} = (1 / (2l' + 1)) * sum_{L} (2L + 1) * C_L(mask) * (Wigner3j(l, l', L; 0, 0, 0))^2

    Note: This is computationally expensive for high lmax. We limit lmax to a reasonable
    value (e.g., 1000) for the matrix construction to ensure runtime feasibility.

    Args:
        cl_mask: Power spectrum of the mask.
        lmax: Maximum multipole moment for the matrix.

    Returns:
        2D numpy array of shape (lmax+1, lmax+1) representing the Mode-Coupling Matrix.
    """
    logger.info(f"Computing Mode-Coupling Matrix for lmax={lmax}...")
    
    # Initialize the matrix
    M = np.zeros((lmax + 1, lmax + 1))
    
    # Precompute Wigner 3j symbols for (l, l', L; 0, 0, 0)
    # We need sum over L. L ranges from 0 to 2*lmax (roughly).
    # Actually, for the convolution of two fields with lmax, L goes up to 2*lmax.
    # But since we are coupling l and l', L is constrained by triangle inequality.
    
    # To optimize, we can iterate over L first.
    # M_{ll'} = sum_L (2L+1) * C_L(mask) * (Wigner(l, l', L; 0,0,0))^2
    
    # We need Wigner 3j. healpy does not have a direct public function for 3j symbols
    # in the standard API (it's in sphtools or requires scipy.special).
    # We use scipy.special.wigner_3j.
    from scipy.special import wigner_3j

    # Determine the range of L needed.
    # The mask power spectrum cl_mask is defined up to lmax_mask.
    # If cl_mask is shorter, we assume 0 beyond its length.
    lmax_mask = len(cl_mask) - 1
    
    # The matrix is symmetric? No, M_{ll'} is not necessarily symmetric, but for real masks
    # and isotropic statistics, the kernel is symmetric in l, l' if we consider the full convolution.
    # However, the standard formula is:
    # <a_lm a*_l'm'> = sum_L (2L+1) C_L(mask) * (3j)^2 * delta...
    
    # Let's compute the matrix elements.
    # Optimization: Precompute non-zero 3j symbols.
    # 3j(l, l', L; 0, 0, 0) is non-zero only if l+l'+L is even and |l-l'| <= L <= l+l'.
    
    logger.debug("Starting matrix element calculation...")
    
    for l in range(lmax + 1):
        for lp in range(lmax + 1):
            val = 0.0
            # L range: |l - lp| to min(l + lp, lmax_mask)
            L_min = abs(l - lp)
            L_max = min(l + lp, lmax_mask)
            
            if L_min > L_max:
                continue
                
            for L in range(L_min, L_max + 1):
                # Wigner 3j symbol
                # wigner_3j(l1, l2, l3, m1, m2, m3)
                # Here m1=m2=m3=0
                try:
                    w = wigner_3j(l, lp, L, 0, 0, 0)
                    # Check if valid (NaNs can occur if triangle inequality fails or parity)
                    if np.isnan(w):
                        continue
                    term = (2 * L + 1) * cl_mask[L] * (w ** 2)
                    val += term
                except Exception:
                    continue
            
            M[l, lp] = val

    logger.info(f"Mode-Coupling Matrix computed. Shape: {M.shape}")
    return M

def calculate_leakage_matrix_from_mask(mask: np.ndarray, lmax: int = 1000) -> np.ndarray:
    """
    Main entry point to calculate the leakage matrix from a HEALPix mask.

    Steps:
    1. Compute the power spectrum of the mask.
    2. Compute the Mode-Coupling Matrix using the mask's power spectrum.

    Args:
        mask: HEALPix mask array (0/1).
        lmax: Maximum multipole moment for the matrix.

    Returns:
        Mode-Coupling Matrix (lmax+1 x lmax+1).
    """
    # Ensure mask is float for calculations
    mask = mask.astype(np.float64)
    
    # Compute mask power spectrum
    cl_mask = compute_mask_power_spectrum(mask, lmax=lmax)
    
    # Compute the matrix
    M = compute_mode_coupling_matrix(cl_mask, lmax)
    
    return M

def get_leakage_matrix_path(realization_id: str, output_dir: Optional[Path] = None) -> Path:
    """
    Generate the output path for the leakage matrix.

    Args:
        realization_id: Unique identifier for the realization.
        output_dir: Base output directory. Defaults to DATA_DERIVED_DIR.

    Returns:
        Path to the .npy file.
    """
    if output_dir is None:
        output_dir = Path(DATA_DERIVED_DIR)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"leakage_matrix_{realization_id}.npy"
    return output_dir / filename

def save_leakage_matrix(matrix: np.ndarray, realization_id: str, output_dir: Optional[Path] = None) -> Path:
    """
    Save the leakage matrix to disk.

    Args:
        matrix: The Mode-Coupling Matrix.
        realization_id: Unique identifier for the realization.
        output_dir: Base output directory.

    Returns:
        Path to the saved file.
    """
    path = get_leakage_matrix_path(realization_id, output_dir)
    np.save(path, matrix)
    logger.info(f"Saved leakage matrix to {path}")
    return path

def load_leakage_matrix(realization_id: str, input_dir: Optional[Path] = None) -> np.ndarray:
    """
    Load a previously computed leakage matrix.

    Args:
        realization_id: Unique identifier for the realization.
        input_dir: Base input directory. Defaults to DATA_DERIVED_DIR.

    Returns:
        The Mode-Coupling Matrix.
    """
    if input_dir is None:
        input_dir = Path(DATA_DERIVED_DIR)
    
    path = get_leakage_matrix_path(realization_id, input_dir)
    if not path.exists():
        raise FileNotFoundError(f"Leakage matrix not found at {path}")
    
    matrix = np.load(path)
    logger.info(f"Loaded leakage matrix from {path}")
    return matrix

def validate_leakage_matrix(matrix: np.ndarray, expected_lmax: int) -> bool:
    """
    Validate the dimensions and content of a leakage matrix.

    Args:
        matrix: The matrix to validate.
        expected_lmax: Expected maximum multipole moment.

    Returns:
        True if valid, False otherwise.
    """
    if matrix.shape != (expected_lmax + 1, expected_lmax + 1):
        logger.error(f"Matrix shape {matrix.shape} does not match expected ({expected_lmax+1}, {expected_lmax+1})")
        return False
    
    if np.any(np.isnan(matrix)):
        logger.error("Matrix contains NaN values")
        return False
    
    if np.any(np.isinf(matrix)):
        logger.error("Matrix contains Inf values")
        return False
    
    return True

def main():
    """
    Main entry point for standalone execution.
    Expects environment variables or arguments to specify realization_id and mask path.
    For this task, we assume the mask path is derived from the realization_id via standard naming
    or passed as an argument.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate Mode-Coupling Matrix for CMB Gap Analysis")
    parser.add_argument("--realization_id", type=str, required=True, help="Unique ID for the realization (e.g., 'realization_001')")
    parser.add_argument("--mask_path", type=str, required=False, help="Path to the mask FITS file. If not provided, assumes standard location.")
    parser.add_argument("--lmax", type=int, default=1000, help="Maximum multipole moment for the matrix")
    parser.add_argument("--output_dir", type=str, default=DATA_DERIVED_DIR, help="Output directory for the matrix")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    realization_id = args.realization_id
    lmax = args.lmax
    output_dir = Path(args.output_dir)
    
    # Determine mask path
    if args.mask_path:
        mask_path = Path(args.mask_path)
    else:
        # Standard convention: data/derived/masks/{realization_id}_mask.fits
        # Or data/raw/masks/...
        # We check common locations or require explicit path if not standard.
        # For now, we assume a standard location relative to the project root.
        # The mask is likely generated by T012 and stored in data/derived/masks or similar.
        # Let's assume the mask is at: data/derived/masks/{realization_id}_mask.fits
        # If that doesn't exist, we might need to look in data/raw.
        # To be safe, we require the user to provide the path or we look in a standard place.
        # Given the task description, we assume the mask is available.
        # Let's try the standard derived path first.
        mask_path = Path(DATA_DERIVED_DIR) / "masks" / f"{realization_id}_mask.fits"
        
        if not mask_path.exists():
            # Try raw
            mask_path = Path("data") / "raw" / "masks" / f"{realization_id}_mask.fits"
            
        if not mask_path.exists():
            logger.error(f"Mask file not found at {mask_path}. Please provide --mask_path.")
            sys.exit(1)

    logger.info(f"Processing realization: {realization_id}")
    logger.info(f"Loading mask from: {mask_path}")
    
    try:
        mask = load_mask_from_fits(str(mask_path))
    except Exception as e:
        logger.error(f"Failed to load mask: {e}")
        sys.exit(1)
    
    logger.info(f"Mask loaded. Nside: {hp.get_nside(mask)}, Pixels: {len(mask)}")
    
    # Calculate leakage matrix
    try:
        matrix = calculate_leakage_matrix_from_mask(mask, lmax=lmax)
    except Exception as e:
        logger.error(f"Failed to calculate leakage matrix: {e}")
        sys.exit(1)
    
    # Validate
    if not validate_leakage_matrix(matrix, lmax):
        logger.error("Leakage matrix validation failed.")
        sys.exit(1)
    
    # Save
    output_path = save_leakage_matrix(matrix, realization_id, output_dir)
    logger.info(f"Task T027 completed successfully. Output: {output_path}")

if __name__ == "__main__":
    main()