"""
Initial condition generators for GPE simulations.

Provides functions to create Thomas-Fermi initial conditions
for rotating Bose-Einstein condensates.
"""
import numpy as np
from typing import Tuple, Optional
import os

from utils.logger import get_logger
from utils.seed_manager import get_global_seed

logger = get_logger(__name__)

def create_thomas_fermi_initial_condition(
    Nx: int, Ny: int, 
    x: np.ndarray, y: np.ndarray,
    N: int, 
    omega_trap: float, 
    a_s: float,
    rotation: float = 0.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Create a Thomas-Fermi initial condition for the GPE.
    
    The Thomas-Fermi approximation gives the density profile:
    n(r) = (μ - V(r)) / g  for μ > V(r), else 0
    
    where:
    - μ is the chemical potential
    - V(r) is the trap potential
    - g is the interaction strength
    
    For a rotating BEC, we add a phase factor exp(i*m*φ) to represent
    vortices, but for the initial condition without vortices, we use
    a simple Gaussian or Thomas-Fermi profile.
    
    Args:
        Nx, Ny: Grid dimensions
        x, y: 1D coordinate arrays
        N: Number of atoms
        omega_trap: Trap frequency (rad/s)
        a_s: s-wave scattering length (m)
        rotation: Rotation frequency (rad/s), default 0
        seed: Random seed for small perturbations
        
    Returns:
        Initial wavefunction array (complex)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Create 2D grid
    X, Y = np.meshgrid(x, y, indexing='ij')
    R2 = X**2 + Y**2
    R = np.sqrt(R2)
    
    # Trap potential
    m = 87.0 * 1.660539e-27  # Mass of Rb-87 in kg
    hbar = 1.0545718e-34
    g = 4 * np.pi * hbar**2 * a_s / m
    
    # Chemical potential from Thomas-Fermi approximation
    # μ = (ħω/2) * (15 * N * a_s / a_ho)^(2/5)
    # where a_ho = sqrt(ħ/(m*ω))
    a_ho = np.sqrt(hbar / (m * omega_trap))
    mu = (hbar * omega_trap / 2) * (15 * N * a_s / a_ho)**(2/5)
    
    # Thomas-Fermi density profile
    # n(r) = (μ - V(r)) / g for μ > V(r), else 0
    V_trap = 0.5 * m * omega_trap**2 * R2
    density = np.maximum(0, (mu - V_trap) / g)
    
    # Wavefunction is sqrt(density) with phase
    # For rotating BEC, add phase exp(i * rotation * t * φ) but at t=0, phase=0
    # If rotation > 0, we might want to add a vortex phase, but for simplicity
    # we start with a non-rotating profile and let the rotation term in the GPE
    # generate vortices dynamically.
    
    psi = np.sqrt(density)
    
    # Add small random perturbation to break symmetry if needed
    if seed is not None:
        perturbation = 0.01 * (np.random.rand(Nx, Ny) - 0.5)
        psi = psi * (1 + perturbation)
    
    # Normalize to N particles
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    norm = np.sqrt(np.sum(np.abs(psi)**2) * dx * dy)
    psi = psi * np.sqrt(N) / norm
    
    logger.debug(f"Thomas-Fermi initial condition created: N={N}, "
                f"μ={mu:.6e}, norm={np.sum(np.abs(psi)**2)*dx*dy:.6f}")
    
    return psi


def create_gaussian_initial_condition(
    Nx: int, Ny: int,
    x: np.ndarray, y: np.ndarray,
    N: int,
    sigma: float = 1.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Create a Gaussian initial condition for the GPE.
    
    Args:
        Nx, Ny: Grid dimensions
        x, y: 1D coordinate arrays
        N: Number of atoms
        sigma: Width of the Gaussian
        seed: Random seed for perturbations
        
    Returns:
        Initial wavefunction array (complex)
    """
    if seed is not None:
        np.random.seed(seed)
    
    X, Y = np.meshgrid(x, y, indexing='ij')
    R2 = X**2 + Y**2
    
    # Gaussian profile
    psi = np.exp(-R2 / (2 * sigma**2))
    
    # Add small random perturbation
    if seed is not None:
        perturbation = 0.01 * (np.random.rand(Nx, Ny) - 0.5)
        psi = psi * (1 + perturbation)
    
    # Normalize
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    norm = np.sqrt(np.sum(np.abs(psi)**2) * dx * dy)
    psi = psi * np.sqrt(N) / norm
    
    return psi


def main():
    """Test initial condition generation."""
    # Create a simple grid
    Nx, Ny = 64, 64
    L = 20.0
    x = np.linspace(-L/2, L/2, Nx, endpoint=False)
    y = np.linspace(-L/2, L/2, Ny, endpoint=False)
    
    # Create Thomas-Fermi initial condition
    psi_tf = create_thomas_fermi_initial_condition(
        Nx, Ny, x, y,
        N=10000,
        omega_trap=2*np.pi*100.0,
        a_s=5.2e-9,  # 5.2 nm
        seed=42
    )
    
    print(f"Thomas-Fermi initial condition shape: {psi_tf.shape}")
    print(f"Norm: {np.sum(np.abs(psi_tf)**2) * (x[1]-x[0]) * (y[1]-y[0]):.6f}")
    print(f"Max density: {np.max(np.abs(psi_tf)**2):.6e}")
    
    # Create Gaussian initial condition
    psi_gauss = create_gaussian_initial_condition(
        Nx, Ny, x, y,
        N=10000,
        sigma=2.0,
        seed=42
    )
    
    print(f"Gaussian initial condition shape: {psi_gauss.shape}")
    print(f"Norm: {np.sum(np.abs(psi_gauss)**2) * (x[1]-x[0]) * (y[1]-y[0]):.6f}")
    
    return psi_tf, psi_gauss


if __name__ == "__main__":
    main()
