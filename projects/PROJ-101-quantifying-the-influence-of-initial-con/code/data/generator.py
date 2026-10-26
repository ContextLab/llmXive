"""
Generator module for coupled Lorenz oscillators.

Implements:
- Coupled Lorenz ODE system definition (N oscillators, coupling topology)
- Trajectory integration using scipy.integrate.solve_ivp (DOP853)
- Additive Gaussian white noise injection
- Two‑tier noise validation (HighNoiseWarning, UnphysicalTrajectoryError)
- Stability guards from ``code.utils.stability`` (raise_if_unphysical,
  check_noise_level) to satisfy task T007.
"""
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass, field
from scipy.integrate import solve_ivp
import warnings
import json
from pathlib import Path

from ..config import NumericalSettings, SimulationConfig, AnalysisConfig, get_full_config
from ..utils.stability import (
    NumericalStabilityError,
    DivergenceError,
    NonConvergenceError,
    check_boundedness,
    detect_divergence_rate,
    raise_if_unphysical,
    check_noise_level,
)

# ----------------------------------------------------------------------
# Constants for Lorenz system
# ----------------------------------------------------------------------
LORENZ_SIGMA = 10.0
LORENZ_RHO = 28.0
LORENZ_BETA = 8.0 / 3.0

# ----------------------------------------------------------------------
# Exceptions / warnings (project‑wide definitions)
# ----------------------------------------------------------------------
class HighNoiseWarning(UserWarning):
    """Warning raised when noise level exceeds physical realism threshold."""
    pass


class UnphysicalTrajectoryError(RuntimeError):
    """Error raised when any state vector norm exceeds the allowed bound (20.0)."""
    pass


# ----------------------------------------------------------------------
# Data container
# ----------------------------------------------------------------------
@dataclass
class TrajectoryData:
    """Container for generated trajectory data."""
    time: np.ndarray
    state: np.ndarray  # Shape: (time_steps, N_oscillators * 3)
    noise_level: float
    N_oscillators: int
    coupling_strength: float
    seed: int
    is_clean: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "time": self.time.tolist(),
            "state": self.state.tolist(),
            "noise_level": self.noise_level,
            "N_oscillators": self.N_oscillators,
            "coupling_strength": self.coupling_strength,
            "seed": self.seed,
            "is_clean": self.is_clean,
        }

# ----------------------------------------------------------------------
# Core ODE definitions
# ----------------------------------------------------------------------
def lorenz_ode_single(t: float, state: np.ndarray) -> np.ndarray:
    """Derivatives for a single Lorenz oscillator."""
    x, y, z = state
    dxdt = LORENZ_SIGMA * (y - x)
    dydt = x * (LORENZ_RHO - z) - y
    dzdt = x * y - LORENZ_BETA * z
    return np.array([dxdt, dydt, dzdt])


def coupled_lorenz_ode(t: float, state: np.ndarray, N: int,
                      coupling_strength: float,
                      coupling_topology: str = "ring") -> np.ndarray:
    """
    Derivatives for N coupled Lorenz oscillators.

    Parameters
    ----------
    t : float
        Current time (unused – autonomous system).
    state : np.ndarray
        Flattened state vector of shape ``(N*3,)``.
    N : int
        Number of oscillators.
    coupling_strength : float
        Diffusive coupling coefficient.
    coupling_topology : str, optional
        Currently only ``'ring'`` is supported.

    Returns
    -------
    np.ndarray
        Flattened derivative vector of shape ``(N*3,)``.
    """
    # Reshape to (N, 3) for vectorised operations
    y = state.reshape(N, 3)
    dxdt = np.empty_like(y)

    # Uncoupled Lorenz dynamics
    dxdt[:, 0] = LORENZ_SIGMA * (y[:, 1] - y[:, 0])
    dxdt[:, 1] = y[:, 0] * (LORENZ_RHO - y[:, 2]) - y[:, 1]
    dxdt[:, 2] = y[:, 0] * y[:, 1] - LORENZ_BETA * y[:, 2]

    # Add diffusive coupling on *all* three components
    if coupling_strength != 0.0:
        if coupling_topology != "ring":
            raise ValueError("Only 'ring' topology is implemented.")
        left = np.roll(y, shift=1, axis=0)
        right = np.roll(y, shift=-1, axis=0)
        dxdt += coupling_strength * (left - 2 * y + right)

    return dxdt.ravel()


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _generate_initial_conditions(N: int, rng: np.random.Generator) -> np.ndarray:
    """
    Produce a random initial condition for ``N`` coupled Lorenz oscillators.

    Small random perturbations around the canonical point (1, 1, 1)
    keep the trajectory inside the attractor for a reasonable time.
    """
    base = np.array([1.0, 1.0, 1.0])
    init = rng.normal(loc=base, scale=0.5, size=(N, 3))
    return init.ravel()


def _inject_noise(state: np.ndarray, sigma_noise: float,
                 rng: np.random.Generator) -> np.ndarray:
    """Additive Gaussian noise; bypasses noise generation when sigma_noise==0."""
    if sigma_noise == 0.0:
        return state
    noise = rng.normal(loc=0.0, scale=sigma_noise, size=state.shape)
    return state + noise

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def generate_coupled_lorenz_trajectory(
    N: int,
    t_start: float = 0.0,
    t_end: float = 1000.0,
    dt: float = 0.01,
    sigma_noise: float = 0.0,
    coupling_strength: float = 0.01,
    coupling_topology: str = "ring",
    seed: Optional[int] = None,
    numerical_settings: Optional[NumericalSettings] = None,
) -> TrajectoryData:
    """
    Generate a complete trajectory of coupled Lorenz oscillators with optional noise.

    The function now wires the stability guards from ``code.utils.stability``:
    * ``check_noise_level`` emits ``HighNoiseWarning`` when ``sigma_noise > 0.1``.
    * ``raise_if_unphysical`` raises ``UnphysicalTrajectoryError`` when the
      Euclidean norm of any state vector exceeds ``20.0`` (both for the
      deterministic part and after noise injection).

    Parameters
    ----------
    N : int
        Number of coupled oscillators.
    t_start, t_end : float
        Integration interval.
    dt : float
        Desired output time step.
    sigma_noise : float, optional
        Standard deviation of the additive Gaussian observation noise.
    coupling_strength : float, optional
        Linear coupling coefficient between neighbours.
    coupling_topology : str, optional
        Only ``'ring'`` is supported.
    seed : int, optional
        Random seed for reproducibility.
    numerical_settings : NumericalSettings, optional
        Overrides the global numerical configuration.

    Returns
    -------
    TrajectoryData
        Dataclass instance containing time, state, and metadata.
    """
    if seed is None:
        seed = np.random.SeedSequence().entropy
    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # 1️⃣  Noise‑level guard (warning only)
    # ------------------------------------------------------------------
    check_noise_level(sigma_noise)  # may emit HighNoiseWarning

    # ------------------------------------------------------------------
    # 2️⃣  Initial condition
    # ------------------------------------------------------------------
    y0 = _generate_initial_conditions(N, rng)

    # ------------------------------------------------------------------
    # 3️⃣  Deterministic integration
    # ------------------------------------------------------------------
    t_eval = np.arange(t_start, t_end + dt, dt)

    sol = solve_ivp(
        fun=lambda t, y: coupled_lorenz_ode(
            t,
            y,
            N=N,
            coupling_strength=coupling_strength,
            coupling_topology=coupling_topology,
        ),
        t_span=(t_start, t_end),
        y0=y0,
        method="DOP853",
        t_eval=t_eval,
        rtol=1e-9,
        atol=1e-12,
    )

    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    state_det = sol.y.T  # shape (n_steps, 3*N)

    # ------------------------------------------------------------------
    # 4️⃣  Guard against unphysical deterministic trajectory
    # ------------------------------------------------------------------
    raise_if_unphysical(state_det, threshold=20.0)

    # ------------------------------------------------------------------
    # 5️⃣  Noise injection (if requested)
    # ------------------------------------------------------------------
    noisy_state = _inject_noise(state_det, sigma_noise, rng)

    # ------------------------------------------------------------------
    # 6️⃣  Guard against unphysical noisy trajectory
    # ------------------------------------------------------------------
    raise_if_unphysical(noisy_state, threshold=20.0)

    return TrajectoryData(
        time=sol.t,
        state=noisy_state,
        noise_level=sigma_noise,
        N_oscillators=N,
        coupling_strength=coupling_strength,
        seed=seed,
        is_clean=sigma_noise == 0.0,
    )
