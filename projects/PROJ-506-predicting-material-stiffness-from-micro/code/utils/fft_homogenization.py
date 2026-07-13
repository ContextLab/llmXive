"""
FFT-based Homogenization Solver for Effective Stiffness Calculation.

This module implements a CPU-optimized FFT-based numerical homogenization
solver to compute the effective elastic stiffness tensor of heterogeneous
materials based on their microstructure images.

Methodology:
- Uses the Moulinec-Suquet FFT scheme for periodic homogenization.
- Assumes linear elasticity with isotropic phases (matrix and inclusions).
- Input: 2D microstructure image (0=void/matrix, 1=inclusion).
- Output: Effective 2D stiffness tensor (Voigt notation).

References:
- Moulinec, H., & Suquet, P. (1994). A fast numerical method for computing
  the linear and nonlinear mechanical properties of heterogeneous materials.
  Comptes Rendus de l'Académie des Sciences - Series II, 318(11), 1417-1423.
"""

import numpy as np
from typing import Tuple, Optional
import logging

# Configure logging for solver progress
logger = logging.getLogger(__name__)

# Material properties for phases (Elastic Modulus, Poisson's Ratio)
# Matrix (Phase 0): Epoxy-like polymer
E_MATRIX = 3.0  # GPa
NU_MATRIX = 0.35

# Inclusion (Phase 1): Ceramic-like hard particle
E_INCLUSION = 70.0  # GPa
NU_INCLUSION = 0.20

# Void (Phase -1 or specific handling): Effectively 0 stiffness
# For simplicity, we treat 0 in image as Matrix and 1 as Inclusion.
# If voids are needed, they can be modeled as very low stiffness matrix.

def _get_lame_params(E: float, nu: float) -> Tuple[float, float]:
    """Convert Young's modulus and Poisson's ratio to Lame parameters."""
    if nu >= 0.5:
        raise ValueError("Poisson's ratio must be < 0.5 for stability.")
    mu = E / (2 * (1 + nu))  # Shear modulus
    lam = (E * nu) / ((1 + nu) * (1 - 2 * nu))  # First Lame parameter
    return lam, mu

def _compute_stiffness_tensor_2d(lam: float, mu: float) -> np.ndarray:
    """
    Compute the 2D plane-strain stiffness tensor in Voigt notation.
    Returns a 3x3 matrix: [[C11, C12, 0], [C12, C22, 0], [0, 0, C66]]
    """
    C11 = lam + 2 * mu
    C12 = lam
    C66 = mu
    return np.array([
        [C11, C12, 0.0],
        [C12, C11, 0.0],
        [0.0, 0.0, C66]
    ])

def _create_green_operator(shape: Tuple[int, int], dtype=np.complex128) -> np.ndarray:
    """
    Create the Green operator in Fourier space for the reference medium.
    Uses the FFT frequency grid.
    """
    nx, ny = shape
    # Frequency grids
    kx = np.fft.fftfreq(nx) * nx
    ky = np.fft.fftfreq(ny) * ny
    KX, KY = np.meshgrid(kx, ky, indexing='ij')

    # Reference medium properties (using matrix properties)
    lam_ref, mu_ref = _get_lame_params(E_MATRIX, NU_MATRIX)
    C_ref = _compute_stiffness_tensor_2d(lam_ref, mu_ref)
    mu_ref_val = mu_ref

    # Construct Green operator
    # Gamma(k) = [ (k . C_ref . k)^{-1} . k ] ... simplified for 2D
    # We use the standard formulation for the polarization field iteration.

    # Avoid division by zero at k=0
    K2 = KX**2 + KY**2
    K2_safe = np.where(K2 == 0, 1.0, K2)

    # Precompute terms for the Green operator
    # This is a simplified version for isotropic reference medium
    # The full tensor operation is complex; we use the scalar form for efficiency
    # in the iteration loop.

    # We will store the necessary terms for the FFT-based iteration
    # Green function components for plane strain
    # G_ijkl(k) ... simplified to scalar multiplication in frequency domain
    # for the polarization strain update.

    # Return the frequency grid and reference stiffness
    return {
        'kx': KX,
        'ky': KY,
        'k2': K2,
        'k2_safe': K2_safe,
        'mu_ref': mu_ref_val,
        'lam_ref': lam_ref,
        'C_ref': C_ref
    }

def compute_effective_stiffness(
    microstructure: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-4,
    verbose: bool = False
) -> np.ndarray:
    """
    Compute the effective stiffness tensor of a 2D microstructure using FFT.

    Args:
        microstructure: 2D numpy array (Nx, Ny).
            0.0 = Matrix phase
            1.0 = Inclusion phase
            Values should be binary or close to binary.
        max_iter: Maximum number of iterations for convergence.
        tol: Convergence tolerance for the strain field update.
        verbose: If True, log iteration progress.

    Returns:
        effective_stiffness: 3x3 numpy array (Voigt notation: C11, C12, C22, C66).
            For 2D plane strain: [[C11, C12, 0], [C12, C22, 0], [0, 0, C66]]

    Raises:
        ValueError: If input dimensions are invalid or not 2D.
    """
    if microstructure.ndim != 2:
        raise ValueError("Microstructure must be a 2D array.")

    nx, ny = microstructure.shape
    if nx <= 1 or ny <= 1:
        raise ValueError("Microstructure dimensions must be > 1.")

    # Ensure float type
    phase_field = microstructure.astype(np.float64)

    # Reference medium (Matrix)
    lam_ref, mu_ref = _get_lame_params(E_MATRIX, NU_MATRIX)
    C_ref = _compute_stiffness_tensor_2d(lam_ref, mu_ref)

    # Inclusion properties
    lam_inc, mu_inc = _get_lame_params(E_INCLUSION, NU_INCLUSION)
    C_inc = _compute_stiffness_tensor_2d(lam_inc, mu_inc)

    # Stiffness contrast
    # Delta C(x) = C(x) - C_ref
    # C(x) = C_ref + phase_field * (C_inc - C_ref)
    delta_C = C_inc - C_ref

    # Initialize strain field (uniform macroscopic strain)
    # We apply a unit strain in each direction to extract stiffness components
    # Macroscopic strains: eps_bar = [1, 0, 0], [0, 1, 0], [0, 0, 1] (Voigt)
    # But for linear elasticity, we can solve for one load case and superpose,
    # or solve 3 independent load cases. Here we solve 3 cases.

    effective_C = np.zeros((3, 3), dtype=np.float64)

    # Precompute Green operator terms
    # For isotropic reference, the Green operator in Fourier space simplifies
    # to a tensor acting on the polarization.
    # We use the Moulinec-Suquet scheme:
    # eps^{k+1} = eps_bar - Gamma_0 * (sigma^k - C_ref : eps^k)
    # where sigma^k = C(x) : eps^k

    # Precompute Fourier space operators
    kx = np.fft.fftfreq(nx) * nx
    ky = np.fft.fftfreq(ny) * ny
    KX, KY = np.meshgrid(kx, ky, indexing='ij')
    K2 = KX**2 + KY**2
    K2_safe = np.where(K2 == 0, 1.0, K2)

    # Green operator components for plane strain isotropic medium
    # Gamma_0_ijkl(k)
    # We need to apply this to the polarization stress.
    # Simplified implementation for efficiency:
    # We compute the necessary tensor contractions in the loop.

    # Pre-allocate fields
    eps_field = np.zeros((nx, ny, 3), dtype=np.complex128) # 3 components: eps_xx, eps_yy, eps_xy
    # Note: eps_xy is engineering shear strain (2*eps_xy_tensor) in Voigt
    # In tensor notation, shear is eps_xy. In Voigt, it's gamma_xy = 2*eps_xy.
    # We will work with tensor strains and convert to Voigt at the end.
    # Tensor strains: [eps_xx, eps_yy, 2*eps_xy] (Voigt convention for stiffness)
    # Actually, let's stick to Voigt strain: [eps_xx, eps_yy, gamma_xy]
    # where gamma_xy = 2 * eps_xy_tensor.
    # Stiffness C in Voigt: sigma = C * eps_voigt.
    # sigma_xx = C11*eps_xx + C12*eps_yy
    # sigma_yy = C12*eps_xx + C22*eps_yy
    # sigma_xy = C66 * gamma_xy (where gamma_xy = 2*eps_xy_tensor)

    # Re-define for Voigt:
    # Strain vector: [eps_xx, eps_yy, 2*eps_xy]
    # Stiffness matrix:
    # [[C11, C12, 0],
    #  [C12, C22, 0],
    #  [0,   0,   C66]]

    # Initialize macroscopic strains to solve for
    # Case 1: eps_bar = [1, 0, 0]
    # Case 2: eps_bar = [0, 1, 0]
    # Case 3: eps_bar = [0, 0, 1] (shear)

    for load_case in range(3):
        eps_bar = np.zeros(3)
        eps_bar[load_case] = 1.0

        # Initialize strain field with macroscopic strain
        # eps(x) = eps_bar + eps_fluct(x)
        # eps_fluct has zero mean
        eps_current = np.zeros((nx, ny, 3), dtype=np.complex128)
        eps_current[:, :, load_case] = 1.0 # Start with uniform strain for the active component

        # Zero mean fluctuation for other components? No, start from 0.
        # Actually, the initial guess is usually just the macroscopic strain.
        # But since we are solving for the full field, we set eps_current = eps_bar everywhere.
        eps_current = np.zeros((nx, ny, 3), dtype=np.complex128)
        eps_current[:, :, load_case] = 1.0

        # Iteration
        for i_iter in range(max_iter):
            # Compute stress: sigma = C(x) : eps
            # C(x) = C_ref + phase_field * delta_C
            # sigma_xx = (C11_ref + p*dc11)*eps_xx + (C12_ref + p*dc12)*eps_yy
            # sigma_yy = (C12_ref + p*dc12)*eps_xx + (C11_ref + p*dc11)*eps_yy  (assuming isotropy C22=C11)
            # sigma_xy (Voigt) = (C66_ref + p*dc66) * 2*eps_xy_tensor = (C66_ref + p*dc66) * eps_voigt_shear

            # Extract real parts for stress calculation (since eps is complex)
            eps_xx = np.real(eps_current[:, :, 0])
            eps_yy = np.real(eps_current[:, :, 1])
            eps_shear = np.real(eps_current[:, :, 2]) # This is gamma_xy

            # Stiffness at each point
            # C11(x), C12(x), C66(x)
            C11_x = C_ref[0, 0] + phase_field * delta_C[0, 0]
            C12_x = C_ref[0, 1] + phase_field * delta_C[0, 1]
            C66_x = C_ref[2, 2] + phase_field * delta_C[2, 2]

            # Stress components
            sigma_xx = C11_x * eps_xx + C12_x * eps_yy
            sigma_yy = C12_x * eps_xx + C11_x * eps_yy # C22 = C11 for isotropic
            sigma_xy = C66_x * eps_shear

            # Polarization stress: tau = sigma - C_ref : eps
            # tau_xx = sigma_xx - (C11_ref*eps_xx + C12_ref*eps_yy)
            tau_xx = sigma_xx - (C_ref[0, 0]*eps_xx + C_ref[0, 1]*eps_yy)
            tau_yy = sigma_yy - (C_ref[1, 0]*eps_xx + C_ref[1, 1]*eps_yy)
            tau_xy = sigma_xy - C_ref[2, 2]*eps_shear

            # FFT of polarization
            tau_xx_hat = np.fft.fft2(tau_xx)
            tau_yy_hat = np.fft.fft2(tau_yy)
            tau_xy_hat = np.fft.fft2(tau_xy)

            # Apply Green operator in Fourier space
            # eps_fluct_hat(k) = - Gamma_0(k) : tau_hat(k)
            # For isotropic medium, the Green operator components are:
            # G_11 = (K2 - KX^2) / (mu_ref * K2^2) ... simplified
            # We use the explicit form for plane strain:
            # eps_xx_hat = - (1/(2*mu_ref*K2)) * ( (K2 - KX^2) * tau_xx_hat - KX*KY * tau_xy_hat - KX*KY * tau_yy_hat + ... )
            # This is getting complex. Let's use the standard simplified update for isotropic reference:
            # eps_hat = - (1/(2*mu_ref)) * ( tau_hat - (k.k.tau_hat.k.k) / (K2^2) ) ? No.

            # Standard Moulinec-Suquet Green operator for isotropic:
            # eps_hat_ij = - (1/(2*mu_ref)) * ( tau_hat_ij - (k_i k_j / K2) * tau_hat_kk )
            # But we need to be careful with Voigt notation and shear.
            # Let's use the tensor form for tau and convert.
            # tau_tensor = [[tau_xx, tau_xy], [tau_xy, tau_yy]]
            # tau_kk = tau_xx + tau_yy
            # k_i k_j term:
            # kx^2, kx*ky, ky^2

            # Compute k_i k_j / K2
            # Avoid div by zero
            kx_sq = KX**2
            ky_sq = KY**2
            kx_ky = KX * KY

            # Denominator
            denom = 2.0 * mu_ref * K2_safe

            # Update for eps_xx
            # eps_xx_hat += -1/denom * ( (ky_sq * tau_xx_hat - kx_ky * tau_xy_hat - kx_ky * tau_yy_hat + kx_sq * tau_yy_hat) ??? )
            # Let's use the explicit formula for isotropic Green operator in Fourier space:
            # eps_hat = - (1/(2*mu)) * ( tau_hat - (k.k.tau_hat.k.k) / (k.k*k.k) )
            # In index notation: eps_ij = -1/(2mu) * ( tau_ij - k_i k_j tau_kl k_k k_l / (k.k)^2 )
            # tau_kl k_k k_l = tau_xx kx^2 + 2 tau_xy kx ky + tau_yy ky^2

            tau_kk_kk = tau_xx_hat * kx_sq + 2 * tau_xy_hat * kx_ky + tau_yy_hat * ky_sq

            # eps_xx_hat
            term_xx = tau_xx_hat - (kx_sq * tau_kk_kk) / K2_safe
            eps_xx_hat = - term_xx / denom

            # eps_yy_hat
            term_yy = tau_yy_hat - (ky_sq * tau_kk_kk) / K2_safe
            eps_yy_hat = - term_yy / denom

            # eps_xy_hat (tensor shear, so Voigt shear is 2*eps_xy)
            # tau_xy is shear stress.
            # eps_xy_hat = -1/(2mu) * ( tau_xy - (kx*ky * tau_kk_kk) / K2 )
            term_xy = tau_xy_hat - (kx_ky * tau_kk_kk) / K2_safe
            eps_xy_tensor_hat = - term_xy / denom
            eps_shear_hat = 2 * eps_xy_tensor_hat # Voigt shear strain

            # Inverse FFT to get strain fluctuation
            # We only need the real part
            eps_xx_fluct = np.real(np.fft.ifft2(eps_xx_hat))
            eps_yy_fluct = np.real(np.fft.ifft2(eps_yy_hat))
            eps_shear_fluct = np.real(np.fft.ifft2(eps_shear_hat))

            # Update strain field
            # eps_new = eps_bar + eps_fluct
            # But we need to ensure zero mean for fluctuation?
            # The Green operator naturally gives zero mean for k=0 term?
            # k=0 term in tau_hat is the average polarization.
            # We should enforce zero mean for fluctuation.
            # Actually, the Green operator at k=0 is undefined (0/0).
            # We set the k=0 component of fluctuation to 0.
            eps_xx_fluct[0, 0] = 0.0
            eps_yy_fluct[0, 0] = 0.0
            eps_shear_fluct[0, 0] = 0.0

            eps_new = np.zeros((nx, ny, 3), dtype=np.complex128)
            eps_new[:, :, 0] = eps_xx_fluct
            eps_new[:, :, 1] = eps_yy_fluct
            eps_new[:, :, 2] = eps_shear_fluct

            # Add macroscopic strain
            eps_new[:, :, load_case] += eps_bar[load_case]

            # Check convergence
            diff = np.max(np.abs(eps_new - eps_current))
            eps_current = eps_new

            if diff < tol:
                if verbose:
                    logger.info(f"Load case {load_case}: Converged at iteration {i_iter+1}, diff={diff:.2e}")
                break
        else:
            if verbose:
                logger.warning(f"Load case {load_case}: Did not converge within {max_iter} iterations.")

        # Compute average stress
        # sigma_bar = <sigma(x)>
        # sigma_xx, sigma_yy, sigma_xy computed from final eps
        eps_xx_final = np.real(eps_current[:, :, 0])
        eps_yy_final = np.real(eps_current[:, :, 1])
        eps_shear_final = np.real(eps_current[:, :, 2])

        C11_x = C_ref[0, 0] + phase_field * delta_C[0, 0]
        C12_x = C_ref[0, 1] + phase_field * delta_C[0, 1]
        C66_x = C_ref[2, 2] + delta_C[2, 2] * phase_field

        sigma_xx_avg = np.mean(C11_x * eps_xx_final + C12_x * eps_yy_final)
        sigma_yy_avg = np.mean(C12_x * eps_xx_final + C11_x * eps_yy_final)
        sigma_xy_avg = np.mean(C66_x * eps_shear_final)

        # Store in effective stiffness
        # C_eff[load_case, :] = <sigma> / eps_bar[load_case]
        # Since eps_bar is 1 for the active component
        effective_C[load_case, 0] = sigma_xx_avg
        effective_C[load_case, 1] = sigma_yy_avg
        effective_C[load_case, 2] = sigma_xy_avg

    # Symmetrize if necessary (should be symmetric by physics)
    effective_C = (effective_C + effective_C.T) / 2.0

    if verbose:
        logger.info(f"Effective stiffness computed:\n{effective_C}")

    return effective_C

def compute_stiffness_from_image(
    image_path: str,
    max_iter: int = 100,
    tol: float = 1e-4,
    verbose: bool = False
) -> np.ndarray:
    """
    Load a microstructure image and compute its effective stiffness.

    Args:
        image_path: Path to the PNG image (128x128, grayscale or binary).
                    0 = Matrix, 255 (or >0) = Inclusion.
        max_iter: Max iterations for FFT solver.
        tol: Convergence tolerance.
        verbose: Log progress.

    Returns:
        effective_stiffness: 3x3 numpy array (Voigt).
    """
    from PIL import Image
    import numpy as np

    img = Image.open(image_path).convert('L')
    arr = np.array(img, dtype=np.float64)

    # Normalize to 0 and 1
    # Assume 0 is matrix, >0 is inclusion
    phase_field = (arr > 0).astype(np.float64)

    return compute_effective_stiffness(phase_field, max_iter, tol, verbose)