"""Initial‑condition generators for the GPE solver.

The module provides functions to create Thomas‑Fermi and Gaussian
condensate profiles, both of which are fully documented.
"""

import os
import numpy as np
from typing import Optional, Tuple

from utils.logger import get_logger
from utils.seed_manager import get_global_seed

_log = get_logger(__name__)

def create_thomas_fermi_initial_condition(
    Nx: int,
    Ny: int,
    x: np.ndarray,
    y: np.ndarray,
    N: int,
    omega_trap: float,
    a_s: float,
    rotation: float = 0.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Create a Thomas‑Fermi initial wavefunction.

    The Thomas‑Fermi approximation yields a parabolic density profile
    within the region where the chemical potential exceeds the trap
    potential.  A small random phase perturbation can be added to seed
    vortex formation.

    Parameters
    ----------
    Nx, Ny : int
        Grid dimensions.
    x, y : np.ndarray
        1‑D coordinate arrays defining the spatial grid.
    N : int
        Total atom number.
    omega_trap : float
        Harmonic trap frequency.
    a_s : float
        s‑wave scattering length.
    rotation : float, optional
        Rotation frequency (default ``0.0``).
    seed : int, optional
        Random seed for phase perturbations.

    Returns
    -------
    np.ndarray
        Complex wavefunction array of shape ``(Nx, Ny)``.
    """
    if seed is not None:
        np.random.seed(seed)
    X, Y = np.meshgrid(x, y, indexing="ij")
    R2 = X ** 2 + Y ** 2
    mu = (15 * N * a_s * omega_trap ** 2) ** (2 / 5)  # Simplified estimate
    V = 0.5 * omega_trap ** 2 * R2
    density = np.maximum(mu - V, 0) / (4 * np.pi * a_s)
    phase = rotation * np.arctan2(Y, X)
    psi = np.sqrt(density) * np.exp(1j * phase)
    return psi

def create_gaussian_initial_condition(
    Nx: int,
    Ny: int,
    x: np.ndarray,
    y: np.ndarray,
    N: int,
    sigma: float = 1.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Create a Gaussian initial wavefunction.

    Parameters
    ----------
    Nx, Ny : int
        Grid dimensions.
    x, y : np.ndarray
        1‑D coordinate arrays.
    N : int
        Number of atoms (used to scale the amplitude).
    sigma : float, optional
        Width of the Gaussian (default ``1.0``).
    seed : int, optional
        Random seed for optional perturbations.

    Returns
    -------
    np.ndarray
        Complex Gaussian wavefunction.
    """
    if seed is not None:
        np.random.seed(seed)
    X, Y = np.meshgrid(x, y, indexing="ij")
    amplitude = np.sqrt(N) * np.exp(-((X ** 2 + Y ** 2) / (2 * sigma ** 2)))
    psi = amplitude.astype(np.complex128)
    return psi

def main() -> None:
    """Simple sanity‑check that generates and saves a Thomas‑Fermi profile."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Thomas‑Fermi profile.")
    parser.add_argument("--Nx", type=int, default=64)
    parser.add_argument("--Ny", type=int, default=64)
    parser.add_argument("--N", type=int, default=10000)
    parser.add_argument("--omega_trap", type=float, default=1.0)
    parser.add_argument("--a_s", type=float, default=0.01)
    parser.add_argument("--rotation", type=float, default=0.5)
    parser.add_argument("--output", type=str, default="data/raw/tf_initial.npy")
    args = parser.parse_args()

    x = np.linspace(-10, 10, args.Nx)
    y = np.linspace(-10, 10, args.Ny)
    psi = create_thomas_fermi_initial_condition(
        args.Nx,
        args.Ny,
        x,
        y,
        args.N,
        args.omega_trap,
        args.a_s,
        rotation=args.rotation,
    )
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    np.save(args.output, psi)
    print(f"Saved Thomas‑Fermi initial condition to {args.output}")

if __name__ == "__main__":
    main()
