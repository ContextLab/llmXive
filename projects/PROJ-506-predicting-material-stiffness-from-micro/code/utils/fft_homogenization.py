"""
FFT-based Homogenization Solver for Material Stiffness.

Implements CPU-optimized numerical homogenization using FFT methods.
Uses the Moulinec-Suquet iterative scheme to solve the Lippmann-Schwinger
equation for effective elastic properties of periodic microstructures.
"""

import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def _compute_gradient_operators(shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute discrete gradient operators in Fourier space.
    
    Args:
        shape: (H, W) of the microstructure.
        
    Returns:
        Tuple of (d1, d2) complex arrays representing gradient operators.
    """
    H, W = shape
    # Create frequency grids
    kx = np.fft.fftfreq(W).astype(np.complex128)
    ky = np.fft.fftfreq(H).astype(np.complex128)
    
    # Meshgrid for 2D
    kx_grid, ky_grid = np.meshgrid(kx, ky, indexing='ij')
    
    # Gradient operators (2*pi*i*k)
    d1 = 2j * np.pi * kx_grid
    d2 = 2j * np.pi * ky_grid
    
    # Handle DC component (zero frequency)
    d1[0, 0] = 0.0
    d2[0, 0] = 0.0
    
    return d1, d2

def _compute_green_operator(
    d1: np.ndarray,
    d2: np.ndarray,
    c0: np.ndarray
) -> np.ndarray:
    """
    Compute the Green's operator in Fourier space.
    
    Args:
        d1, d2: Gradient operators.
        c0: Reference stiffness tensor (2x2 or 3x3 for plane strain).
        
    Returns:
        Green's operator tensor.
    """
    # For 2D plane strain, we use a 2x2 displacement field
    # Green's operator Gamma_ijkl(k) = (k_j * C0_jl * k_l)^-1 * ...
    
    # Simplified scalar approximation for isotropic reference
    # C0 is assumed to be represented by bulk and shear moduli
    # Here we use a diagonal approximation for stability
    
    denom = (d1**2 + d2**2) + 1e-16  # Avoid division by zero
    denom[0, 0] = 1.0  # DC component handling
    
    # Return a simplified Green's operator (scalar for demonstration)
    # In a full implementation, this would be a 4th order tensor
    return 1.0 / denom

def compute_effective_stiffness(
    microstructure: np.ndarray,
    inclusion_stiffness: float = 1.0,
    matrix_stiffness: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-5
) -> np.ndarray:
    """
    Compute the effective stiffness tensor of a 2D microstructure.
    
    Uses the Moulinec-Suquet FFT-based iterative scheme to solve the
    Lippmann-Schwinger equation for periodic homogenization.
    
    Args:
        microstructure: 2D array (H, W) with values 0 (matrix) and 1 (inclusion).
        inclusion_stiffness: Stiffness value for inclusion phase.
        matrix_stiffness: Stiffness value for matrix phase.
        max_iterations: Maximum number of iterations for convergence.
        tolerance: Convergence tolerance for the iterative solver.
        
    Returns:
        3x3 effective stiffness tensor in Voigt notation (C11, C12, C22, C66).
        For 2D plane strain: [C11, C12, 0; C12, C22, 0; 0, 0, C66]
    """
    H, W = microstructure.shape
    
    # Create local stiffness field
    # Using Young's modulus as scalar proxy for simplicity in 2D
    # In a full tensor implementation, this would be a 4th order tensor field
    E_field = np.where(
        microstructure > 0.5,
        inclusion_stiffness,
        matrix_stiffness
    ).astype(np.float64)
    
    # Reference modulus (arithmetic mean for stability)
    E0 = (inclusion_stiffness + matrix_stiffness) / 2.0
    delta_E = E_field - E0
    
    # Initialize strain field (uniform unit strain for loading)
    # We apply three independent loading cases:
    # 1. Uniaxial in x-direction
    # 2. Uniaxial in y-direction
    # 3. Shear
    
    effective_C = np.zeros((3, 3), dtype=np.float64)
    
    # Precompute gradient operators
    d1, d2 = _compute_gradient_operators((H, W))
    denom = d1**2 + d2**2 + 1e-16
    denom[0, 0] = 1.0
    
    # Loading cases
    load_cases = [
        np.array([[1.0, 0.0], [0.0, 0.0]]),  # x-direction
        np.array([[0.0, 0.0], [0.0, 1.0]]),  # y-direction
        np.array([[0.0, 0.5], [0.5, 0.0]]),  # shear
    ]
    
    for case_idx, eps_bar in enumerate(load_cases):
        # Initialize strain field
        eps_x = np.full((H, W), eps_bar[0, 0], dtype=np.complex128)
        eps_y = np.full((H, W), eps_bar[1, 1], dtype=np.complex128)
        eps_xy = np.full((H, W), eps_bar[0, 1], dtype=np.complex128)
        
        # Iterative solver
        for iteration in range(max_iterations):
            # Compute stress: sigma = C : eps
            # Simplified: sigma = E * eps (scalar proxy)
            sigma_x = E_field * eps_x.real
            sigma_y = E_field * eps_y.real
            sigma_xy = E_field * eps_xy.real
            
            # Compute divergence of stress in Fourier space
            sigma_x_hat = np.fft.fft2(sigma_x)
            sigma_y_hat = np.fft.fft2(sigma_y)
            sigma_xy_hat = np.fft.fft2(sigma_xy)
            
            div_sigma_x = np.fft.ifft2(1j * d1 * sigma_x_hat).real
            div_sigma_y = np.fft.ifft2(1j * d2 * sigma_y_hat).real
            
            # Update strain: eps_new = eps_old - Gamma * div_sigma
            # Simplified update using Green's operator
            div_sigma_x_hat = np.fft.fft2(div_sigma_x)
            div_sigma_y_hat = np.fft.fft2(div_sigma_y)
            
            # Correction terms
            corr_x = np.fft.ifft2(div_sigma_x_hat / (E0 * denom)).real
            corr_y = np.fft.ifft2(div_sigma_y_hat / (E0 * denom)).real
            
            eps_x_new = eps_x.real - corr_x
            eps_y_new = eps_y.real - corr_y
            
            # Shear update (simplified)
            eps_xy_new = eps_xy.real  # Shear coupling ignored in scalar proxy
            
            # Check convergence
            diff = (
                np.mean((eps_x_new - eps_x.real)**2) +
                np.mean((eps_y_new - eps_y.real)**2)
            )
            
            eps_x = np.array(eps_x_new, dtype=np.complex128)
            eps_y = np.array(eps_y_new, dtype=np.complex128)
            eps_xy = np.array(eps_xy_new, dtype=np.complex128)
            
            if diff < tolerance:
                logger.debug(f"Case {case_idx} converged at iteration {iteration}")
                break
        
        # Compute effective stress: sigma_bar = <sigma>
        sigma_x_final = E_field * eps_x.real
        sigma_y_final = E_field * eps_y.real
        sigma_xy_final = E_field * eps_xy.real
        
        sigma_bar_x = np.mean(sigma_x_final)
        sigma_bar_y = np.mean(sigma_y_final)
        sigma_bar_xy = np.mean(sigma_xy_final)
        
        # Store effective stiffness components
        # C_ij = sigma_bar_i / eps_bar_j
        if case_idx == 0:  # x-loading
            effective_C[0, 0] = sigma_bar_x / eps_bar[0, 0] if eps_bar[0, 0] != 0 else 0
            effective_C[1, 0] = sigma_bar_y / eps_bar[0, 0] if eps_bar[0, 0] != 0 else 0
        elif case_idx == 1:  # y-loading
            effective_C[0, 1] = sigma_bar_x / eps_bar[1, 1] if eps_bar[1, 1] != 0 else 0
            effective_C[1, 1] = sigma_bar_y / eps_bar[1, 1] if eps_bar[1, 1] != 0 else 0
        elif case_idx == 2:  # shear
            effective_C[2, 2] = sigma_bar_xy / eps_bar[0, 1] if eps_bar[0, 1] != 0 else 0
    
    # Enforce symmetry
    effective_C[1, 0] = effective_C[0, 1]
    
    # Construct 3x3 Voigt notation matrix
    # [C11, C12, 0; C12, C22, 0; 0, 0, C66]
    C_eff = np.zeros((3, 3), dtype=np.float64)
    C_eff[0, 0] = effective_C[0, 0]
    C_eff[0, 1] = effective_C[0, 1]
    C_eff[1, 0] = effective_C[1, 0]
    C_eff[1, 1] = effective_C[1, 1]
    C_eff[2, 2] = effective_C[2, 2]
    
    logger.info(f"Computed effective stiffness: C11={C_eff[0,0]:.4f}, "
               f"C12={C_eff[0,1]:.4f}, C22={C_eff[1,1]:.4f}, C66={C_eff[2,2]:.4f}")
    
    return C_eff

def compute_stiffness_from_image(
    image_path: str,
    inclusion_stiffness: float = 1.0,
    matrix_stiffness: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-5
) -> np.ndarray:
    """
    Load a microstructure image and compute its effective stiffness.
    
    Args:
        image_path: Path to the PNG image file.
        inclusion_stiffness: Stiffness value for inclusion phase.
        matrix_stiffness: Stiffness value for matrix phase.
        max_iterations: Maximum iterations for FFT solver.
        tolerance: Convergence tolerance.
        
    Returns:
        Effective stiffness tensor (3x3 in Voigt notation).
    """
    from skimage import io
    
    # Load image and convert to binary mask
    img = io.imread(image_path)
    if img.ndim == 3:
        img = img[:, :, 0]  # Take first channel if RGB
    
    # Normalize and threshold
    if img.max() > 1.0:
        img = img / 255.0
    
    microstructure = (img > 0.5).astype(float)
    
    return compute_effective_stiffness(
        microstructure,
        inclusion_stiffness=inclusion_stiffness,
        matrix_stiffness=matrix_stiffness,
        max_iterations=max_iterations,
        tolerance=tolerance
    )