"""Configuration utilities for grid and physical parameters.

The module defines the :class:`GridConfig` dataclass and a collection of
helper functions that read environment variables, apply defaults, and
validate the resulting configuration.  All public objects are documented
with NumPy‑style docstrings.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from utils.logger import get_logger

_log = get_logger(__name__)

@dataclass
class GridConfig:
    """Configuration container for the simulation grid and physical parameters.

    Attributes
    ----------
    nx : int
        Number of grid points along the x‑axis.
    ny : int
        Number of grid points along the y‑axis.
    domain_size : float
        Physical size of the simulation box (in harmonic‑oscillator units).
    dt : float
        Time step for the split‑step integration.
    max_time : float
        Maximum simulation time.
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

def get_grid_resolution(run_full_grid: Optional[bool] = None) -> Tuple[int, int]:
    """Determine grid resolution based on the ``RUN_FULL_GRID`` flag.

    The function respects an explicit ``run_full_grid`` argument; if it is
    ``None`` the environment variable ``RUN_FULL_GRID`` is consulted.  The
    resolution is:

    * ``64 × 64`` when ``RUN_FULL_GRID`` is ``true`` (full parameter scan).
    * ``256 × 256`` otherwise (verification runs).

    Parameters
    ----------
    run_full_grid : bool, optional
        Override the environment variable.

    Returns
    -------
    tuple of int
        ``(nx, ny)`` grid dimensions.
    """
    if run_full_grid is None:
        env_val = os.getenv("RUN_FULL_GRID", "false").lower()
        run_full_grid = env_val == "true"
    if run_full_grid:
        return (64, 64)
    else:
        return (256, 256)

def get_domain_size() -> float:
    """Return the physical domain size.

    The size can be overridden via the ``DOMAIN_SIZE`` environment variable.
    If the variable is not set, a default value of ``20.0`` is used.

    Returns
    -------
    float
        Domain size in harmonic‑oscillator units.
    """
    return float(os.getenv("DOMAIN_SIZE", "20.0"))

def get_time_step() -> float:
    """Return the simulation time step.

    The step size can be overridden via the ``TIME_STEP`` environment
    variable; otherwise ``0.001`` is used.

    Returns
    -------
    float
        Time step in harmonic‑oscillator units.
    """
    return float(os.getenv("TIME_STEP", "0.001"))

def get_max_time() -> float:
    """Return the maximum simulation time.

    The value can be overridden via the ``MAX_TIME`` environment variable;
    otherwise ``200.0`` (arbitrary units) is used.

    Returns
    -------
    float
        Maximum simulation time.
    """
    return float(os.getenv("MAX_TIME", "200.0"))

def load_physical_params() -> Dict[str, Any]:
    """Load physical parameters from environment variables.

    Expected variables are:

    * ``PHYS_OMEGA`` – rotation frequency (default ``0.5``)
    * ``PHYS_EPS_DD`` – dipolar interaction strength (default ``0.5``)
    * ``PHYS_N`` – particle number (default ``10000``)

    Returns
    -------
    dict
        Mapping of parameter names to their float/int values.
    """
    return {
        "omega": float(os.getenv("PHYS_OMEGA", "0.5")),
        "epsilon_dd": float(os.getenv("PHYS_EPS_DD", "0.5")),
        "n_particles": int(os.getenv("PHYS_N", "10000")),
    }

def create_grid_config(run_full_grid: Optional[bool] = None) -> GridConfig:
    """Factory function that creates a fully populated :class:`GridConfig`.

    Parameters
    ----------
    run_full_grid : bool, optional
        Override the ``RUN_FULL_GRID`` environment variable.

    Returns
    -------
    GridConfig
        Instance with all fields initialised from environment variables or
        defaults.
    """
    nx, ny = get_grid_resolution(run_full_grid)
    domain = get_domain_size()
    dt = get_time_step()
    max_t = get_max_time()
    phys = load_physical_params()
    return GridConfig(
        nx=nx,
        ny=ny,
        domain_size=domain,
        dt=dt,
        max_time=max_t,
        omega=phys["omega"],
        epsilon_dd=phys["epsilon_dd"],
        n_particles=phys["n_particles"],
    )

def validate_config(config: GridConfig) -> bool:
    """Validate a :class:`GridConfig` instance.

    The function checks for physically plausible values (positive grid
    sizes, non‑negative time step, etc.).  It logs warnings for any
    anomalies and returns ``True`` if the configuration passes all checks.

    Parameters
    ----------
    config : GridConfig
        Configuration object to validate.

    Returns
    -------
    bool
        ``True`` if the configuration is valid, ``False`` otherwise.
    """
    valid = True
    if config.nx <= 0 or config.ny <= 0:
        _log.error("Grid dimensions must be positive.")
        valid = False
    if config.dt <= 0:
        _log.error("Time step must be positive.")
        valid = False
    if config.max_time <= 0:
        _log.error("Maximum time must be positive.")
        valid = False
    if config.domain_size <= 0:
        _log.error("Domain size must be positive.")
        valid = False
    return valid
