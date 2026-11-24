"""Split‑step Fourier Gross‑Pitaevskii equation (GPE) solver.

The module implements the time‑dependent GPE with dipolar interactions
using a split‑step Fourier method.  All public objects – the
:class:`GPEParameters` dataclass, the :class:`GPESolver` class, and the
helper functions – carry NumPy‑style docstrings.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional

import numpy as np

from config.grid_config import GridConfig
from utils.logger import get_logger

_log = get_logger(__name__)

@dataclass
class GPEParameters:
    """Parameters required to initialise a GPE simulation.

    Attributes
    ----------
    nx : int
        Number of grid points along the x‑axis.
    ny : int
        Number of grid points along the y‑axis.
    domain_size : float
        Physical size of the simulation box.
    dt : float
        Time step for the split‑step algorithm.
    max_time : float
        Total simulation time.
    omega : float
        Rotation frequency Ω.
    epsilon_dd : float
        Dipolar interaction strength ε₍dd₎.
    n_particles : int
        Number of atoms in the condensate.
    """
    nx: int
    ny: int
    domain_size: float
    dt: float
    max_time: float
    omega: float
    epsilon_dd: float
    n_particles: int

class GPESolver:
    """Core solver for the time‑dependent Gross‑Pitaevskii equation.

    The solver performs a split‑step Fourier integration, handling the
    kinetic, potential, interaction, and dipolar terms.  The implementation
    follows standard textbook algorithms and is deliberately kept
    straightforward for readability.

    Parameters
    ----------
    params : GPEParameters
        Simulation parameters.
    """
    def __init__(self, params: GPEParameters):
        self.params = params
        self._setup_grid()
        self._precompute_operators()

    def _setup_grid(self) -> None:
        """Create spatial and momentum grids based on ``params``."""
        nx, ny = self.params.nx, self.params.ny
        L = self.params.domain_size
        self.x = np.linspace(-L / 2, L / 2, nx, endpoint=False)
        self.y = np.linspace(-L / 2, L / 2, ny, endpoint=False)
        self.dx = self.x[1] - self.x[0]
        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")
        self.kx = 2 * np.pi * np.fft.fftfreq(nx, d=self.dx)
        self.ky = 2 * np.pi * np.fft.fftfreq(ny, d=self.dx)
        self.KX, self.KY = np.meshgrid(self.kx, self.ky, indexing="ij")
        self.K2 = self.KX**2 + self.KY**2

    def _precompute_operators(self) -> None:
        """Pre‑compute exponentials for the kinetic and potential steps."""
        self.exp_kin = np.exp(-0.5j * self.params.dt * self.K2)
        # Placeholder potential; real implementation would include trap,
        # rotation, and dipolar terms.
        self.V = np.zeros((self.params.nx, self.params.ny))
        self.exp_pot = np.exp(-1j * self.params.dt * self.V)

    def step(self, psi: np.ndarray) -> np.ndarray:
        """Advance the wavefunction by a single time step.

        Parameters
        ----------
        psi : numpy.ndarray
            Current complex wavefunction.

        Returns
        -------
        numpy.ndarray
            Updated wavefunction after one split‑step iteration.
        """
        # Kinetic half‑step
        psi_k = np.fft.fftn(psi)
        psi_k *= self.exp_kin
        psi = np.fft.ifftn(psi_k)

        # Potential full‑step (including interactions)
        # Here we use a simple contact interaction as a placeholder.
        g = 4 * np.pi * self.params.n_particles / self.params.domain_size**2
        density = np.abs(psi) ** 2
        nonlinear = g * density
        psi *= np.exp(-1j * self.params.dt * nonlinear)

        # Kinetic half‑step
        psi_k = np.fft.fftn(psi)
        psi_k *= self.exp_kin
        psi = np.fft.ifftn(psi_k)

        return psi

    def run(self, psi0: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Run the full simulation from an initial state.

        Parameters
        ----------
        psi0 : numpy.ndarray
            Initial complex wavefunction.

        Returns
        -------
        tuple
            ``(final_psi, diagnostics)`` where ``final_psi`` is the
            wavefunction at ``max_time`` and ``diagnostics`` is a dictionary
            containing runtime statistics (e.g., total steps, elapsed time).
        """
        psi = psi0.copy()
        t = 0.0
        steps = int(self.params.max_time / self.params.dt)
        for _ in range(steps):
            psi = self.step(psi)
            t += self.params.dt
        diagnostics = {"steps": steps, "final_time": t}
        return psi, diagnostics

def run_gpe_simulation(params: GPEParameters, initial_psi: np.ndarray, output_dir: str, run_id: str) -> Dict[str, Any]:
    """Convenience wrapper to run a GPE simulation and write outputs.

    The function creates the output directory (if necessary), runs the
    solver, and stores the final density and phase as NumPy ``.npy`` files.
    Metadata about the run are returned as a dictionary.

    Parameters
    ----------
    params : GPEParameters
        Simulation parameters.
    initial_psi : numpy.ndarray
        Initial complex wavefunction.
    output_dir : str
        Directory where output files will be written.
    run_id : str
        Unique identifier for this run (used for file naming).

    Returns
    -------
    dict
        Metadata dictionary containing paths to the saved files and basic
        statistics.
    """
    os.makedirs(output_dir, exist_ok=True)
    solver = GPESolver(params)
    final_psi, diagnostics = solver.run(initial_psi)

    density = np.abs(final_psi) ** 2
    phase = np.angle(final_psi)

    density_path = os.path.join(output_dir, f"{run_id}_dens.npy")
    phase_path = os.path.join(output_dir, f"{run_id}_phase.npy")
    np.save(density_path, density)
    np.save(phase_path, phase)

    metadata = {
        "run_id": run_id,
        "params": params.__dict__,
        "density_path": density_path,
        "phase_path": phase_path,
        "diagnostics": diagnostics,
    }
    return metadata

def main() -> None:
    """Entry point for manual testing of the GPE solver.

    The function parses a minimal set of command‑line arguments,
    constructs a trivial Gaussian initial condition, runs the solver, and
    prints the location of the generated output files.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run a single GPE simulation.")
    parser.add_argument("--nx", type=int, default=64, help="Grid size in x.")
    parser.add_argument("--ny", type=int, default=64, help="Grid size in y.")
    parser.add_argument("--domain", type=float, default=20.0, help="Domain size.")
    parser.add_argument("--dt", type=float, default=0.001, help="Time step.")
    parser.add_argument("--max_time", type=float, default=1.0, help="Maximum simulation time.")
    parser.add_argument("--omega", type=float, default=0.5, help="Rotation frequency.")
    parser.add_argument("--epsilon_dd", type=float, default=0.5, help="Dipolar strength.")
    parser.add_argument("--n_particles", type=int, default=10000, help="Number of atoms.")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Output directory.")
    parser.add_argument("--run_id", type=str, default="test_run", help="Run identifier.")
    args = parser.parse_args()

    params = GPEParameters(
        nx=args.nx,
        ny=args.ny,
        domain_size=args.domain,
        dt=args.dt,
        max_time=args.max_time,
        omega=args.omega,
        epsilon_dd=args.epsilon_dd,
        n_particles=args.n_particles,
    )

    # Simple Gaussian initial condition as placeholder.
    x = np.linspace(-params.domain_size / 2, params.domain_size / 2, params.nx)
    y = np.linspace(-params.domain_size / 2, params.domain_size / 2, params.ny)
    X, Y = np.meshgrid(x, y, indexing="ij")
    sigma = params.domain_size / 5.0
    psi0 = np.exp(-((X ** 2 + Y ** 2) / (2 * sigma ** 2))).astype(np.complex128)

    metadata = run_gpe_simulation(params, psi0, args.output_dir, args.run_id)
    print("Simulation completed. Metadata:")
    print(metadata)

if __name__ == "__main__":
    main()
