"""
Phase-Shifted DNS Null Model for algorithm validation.

This module generates synthetic turbulence data using a phase-shifted
approach to decouple geometric thresholding from energetic magnitude.

IMPORTANT: This data is ONLY for algorithm validation and testing.
It should NEVER be used for primary hypothesis testing.
"""
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import h5py

from utils.logging import get_logger

logger = get_logger(__name__)


def generate_phase_shifted_dns(
    re_lambda: int,
    time_step: int = 0,
    grid_size: int = 512,
    seed: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """
    Generate phase-shifted DNS data for validation purposes.
    
    This creates synthetic turbulence fields that preserve statistical
    properties while decoupling geometric and energetic relationships.
    
    Args:
        re_lambda: Taylor-scale Reynolds number
        time_step: Time step index
        grid_size: Grid dimension (default 512³)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary with 'velocity', 'vorticity', and 'strain_rate' arrays
    """
    if seed is not None:
        np.random.seed(seed)
    
    logger.info(f"Generating Phase-Shifted DNS data: Re_λ={re_lambda}, grid={grid_size}³")
    
    # Generate random Fourier modes with appropriate energy spectrum
    # E(k) ~ k^(-5/3) for inertial range
    k_max = grid_size // 2
    k = np.arange(-k_max, k_max)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing='ij')
    K_mag = np.sqrt(KX**2 + KY**2 + KZ**2 + 1e-10)
    
    # Energy spectrum: E(k) ~ k^(-5/3) with exponential cutoff
    spectrum = (K_mag ** (-5/3)) * np.exp(-K_mag / (k_max * 0.8))
    spectrum[K_mag < 2] = 0  # Remove large-scale modes
    
    # Generate random phases
    phases = np.random.uniform(0, 2 * np.pi, (grid_size, grid_size, grid_size))
    
    # Create velocity field in Fourier space
    velocity_fft = np.sqrt(spectrum) * np.exp(1j * phases)
    
    # Ensure divergence-free condition
    # u · k = 0 in Fourier space
    for i in range(grid_size):
        for j in range(grid_size):
            for l in range(grid_size):
                k_vec = np.array([KX[i,j,l], KY[i,j,l], KZ[i,j,l]], dtype=float)
                if np.linalg.norm(k_vec) > 1e-10:
                    # Project out component parallel to k
                    u = velocity_fft[i,j,l]
                    k_norm = k_vec / np.linalg.norm(k_vec)
                    u_parallel = np.dot(u.real, k_norm) + 1j * np.dot(u.imag, k_norm)
                    u_perp = u - u_parallel * k_norm
                    velocity_fft[i,j,l] = u_perp
    
    # Transform to physical space
    velocity_fft = np.fft.ifftshift(velocity_fft)
    velocity_complex = np.fft.ifftn(velocity_fft)
    velocity = np.real(velocity_complex)
    
    # Reshape to (N, N, N, 3) for velocity components
    velocity = velocity.reshape(grid_size, grid_size, grid_size, 1)
    velocity = np.tile(velocity, (1, 1, 1, 3))
    
    # Scale to match target Re_λ approximately
    # This is a rough scaling for validation purposes
    velocity *= np.sqrt(re_lambda / 100.0)
    
    # Compute vorticity: ω = ∇ × u
    vorticity = compute_vorticity(velocity)
    
    # Compute strain rate tensor: S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)
    strain_rate = compute_strain_rate(velocity)
    
    logger.info(f"Phase-Shifted DNS generation complete")
    
    return {
        'velocity': velocity.astype(np.float32),
        'vorticity': vorticity.astype(np.float32),
        'strain_rate': strain_rate.astype(np.float32)
    }


def compute_vorticity(velocity: np.ndarray) -> np.ndarray:
    """
    Compute vorticity field from velocity using central differences.
    
    Args:
        velocity: Velocity field of shape (N, N, N, 3)
    
    Returns:
        Vorticity field of same shape
    """
    # Central differences with periodic boundary conditions
    du_dx = np.gradient(velocity[..., 0], axis=0)
    du_dy = np.gradient(velocity[..., 0], axis=1)
    du_dz = np.gradient(velocity[..., 0], axis=2)
    
    dv_dx = np.gradient(velocity[..., 1], axis=0)
    dv_dy = np.gradient(velocity[..., 1], axis=1)
    dv_dz = np.gradient(velocity[..., 1], axis=2)
    
    dw_dx = np.gradient(velocity[..., 2], axis=0)
    dw_dy = np.gradient(velocity[..., 2], axis=1)
    dw_dz = np.gradient(velocity[..., 2], axis=2)
    
    # ω = ∇ × u
    vorticity_x = dw_dy - dv_dz
    vorticity_y = du_dz - dw_dx
    vorticity_z = dv_dx - du_dy
    
    vorticity = np.stack([vorticity_x, vorticity_y, vorticity_z], axis=-1)
    return vorticity


def compute_strain_rate(velocity: np.ndarray) -> np.ndarray:
    """
    Compute strain rate tensor from velocity.
    
    S_ij = 0.5 * (∂u_i/∂x_j + ∂u_j/∂x_i)
    
    Args:
        velocity: Velocity field of shape (N, N, N, 3)
    
    Returns:
        Strain rate tensor of shape (N, N, N, 3, 3)
    """
    # Compute all velocity gradients
    grads = np.zeros_like(velocity)
    for i in range(3):
        grads[..., i] = np.gradient(velocity[..., i], axis=i)
    
    # Build strain rate tensor
    strain_rate = np.zeros((*velocity.shape[:3], 3, 3))
    
    for i in range(3):
        for j in range(3):
            if i == j:
                strain_rate[..., i, j] = grads[..., i, i]
            else:
                # Get gradient of component i in direction j
                grad_ij = np.gradient(velocity[..., i], axis=j)
                # Get gradient of component j in direction i
                grad_ji = np.gradient(velocity[..., j], axis=i)
                strain_rate[..., i, j] = 0.5 * (grad_ij + grad_ji)
    
    return strain_rate


def save_phase_shifted_dns(
    re_lambda: int,
    output_path: Path,
    time_step: int = 0,
    seed: Optional[int] = None
) -> None:
    """
    Save phase-shifted DNS data to HDF5 file.
    
    Args:
        re_lambda: Taylor-scale Reynolds number
        output_path: Path to output HDF5 file
        time_step: Time step index
        seed: Random seed for reproducibility
    """
    data = generate_phase_shifted_dns(re_lambda, time_step, seed=seed)
    
    with h5py.File(output_path, 'w') as f:
        f.create_dataset('velocity', data=data['velocity'])
        f.create_dataset('vorticity', data=data['vorticity'])
        f.create_dataset('strain_rate', data=data['strain_rate'])
        f.attrs['re_lambda'] = re_lambda
        f.attrs['time_step'] = time_step
        f.attrs['source'] = 'phase_shifted_dns_null_model'
        f.attrs['purpose'] = 'validation_only'
        if seed is not None:
            f.attrs['seed'] = seed
    
    logger.info(f"Phase-Shifted DNS data saved to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Phase-Shifted DNS null model data")
    parser.add_argument('--re-lambda', type=int, default=400, help='Reynolds number')
    parser.add_argument('--output', type=str, required=True, help='Output file path')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    
    args = parser.parse_args()
    
    save_phase_shifted_dns(
        re_lambda=args.re_lambda,
        output_path=Path(args.output),
        seed=args.seed
    )
    
    print(f"Generated Phase-Shifted DNS data for Re_λ={args.re_lambda}")
    print(f"Saved to: {args.output}")
