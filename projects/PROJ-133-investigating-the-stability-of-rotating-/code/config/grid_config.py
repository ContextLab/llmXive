"""
Grid configuration management for rotating Bose-Einstein condensate simulations.

This module handles environment-based configuration for simulation grid parameters,
including grid resolution, physical domain size, and runtime flags. It supports
conditional grid sizing based on the RUN_FULL_GRID environment variable to
balance computational feasibility with verification requirements.
"""

import os
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GridConfig:
    """
    Configuration container for simulation grid parameters.

    Attributes:
        resolution: Tuple of (N_x, N_y) grid points.
        domain_size: Physical size of the simulation domain in harmonic oscillator
                    units (default: 12.0 for both x and y).
        run_full_grid: If True, uses high-resolution grid (256x256) for verification.
                      If False, uses low-resolution grid (64x64) for full batch scans.
        dt: Time step for integration (default: 0.0005).
        t_max: Maximum simulation time in harmonic oscillator units (default: 50.0).
        physical_params: Dictionary of physical parameters (Ω, ε_dd, N, etc.).
    """
    resolution: Tuple[int, int]
    domain_size: float = 12.0
    run_full_grid: bool = False
    dt: float = 0.0005
    t_max: float = 50.0
    physical_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "resolution": self.resolution,
            "domain_size": self.domain_size,
            "run_full_grid": self.run_full_grid,
            "dt": self.dt,
            "t_max": self.t_max,
            "physical_params": self.physical_params
        }


def get_grid_resolution(run_full_grid: Optional[bool] = None) -> Tuple[int, int]:
    """
    Determine grid resolution based on environment configuration.

    Per spec amendment T017b:
    - If RUN_FULL_GRID=true (or run_full_grid=True): 256x256 for verification.
    - If RUN_FULL_GRID=false (or run_full_grid=False): 64x64 for full batch scan.

    Args:
        run_full_grid: Optional override for the environment variable.

    Returns:
        Tuple of (N_x, N_y) grid dimensions.
    """
    if run_full_grid is None:
        env_val = os.getenv("RUN_FULL_GRID", "false").lower()
        run_full_grid = env_val in ("true", "1", "yes")

    if run_full_grid:
        logger.info("RUN_FULL_GRID enabled: Using 256x256 verification grid.")
        return (256, 256)
    else:
        logger.info("RUN_FULL_GRID disabled: Using 64x64 batch scan grid.")
        return (64, 64)


def get_domain_size() -> float:
    """
    Get the physical domain size from environment or default.

    Returns:
        Domain size in harmonic oscillator units.
    """
    try:
        val = float(os.getenv("GRID_DOMAIN_SIZE", "12.0"))
        if val <= 0:
            raise ValueError("Domain size must be positive.")
        return val
    except ValueError as e:
        logger.warning(f"Invalid GRID_DOMAIN_SIZE: {e}. Using default 12.0.")
        return 12.0


def get_time_step() -> float:
    """
    Get the time step from environment or default.

    Returns:
        Time step in harmonic oscillator units.
    """
    try:
        val = float(os.getenv("GRID_DT", "0.0005"))
        if val <= 0:
            raise ValueError("Time step must be positive.")
        return val
    except ValueError as e:
        logger.warning(f"Invalid GRID_DT: {e}. Using default 0.0005.")
        return 0.0005


def get_max_time() -> float:
    """
    Get the maximum simulation time from environment or default.

    Returns:
        Maximum time in harmonic oscillator units.
    """
    try:
        val = float(os.getenv("GRID_T_MAX", "50.0"))
        if val <= 0:
            raise ValueError("Max time must be positive.")
        return val
    except ValueError as e:
        logger.warning(f"Invalid GRID_T_MAX: {e}. Using default 50.0.")
        return 50.0


def load_physical_params() -> Dict[str, Any]:
    """
    Load physical parameters from environment variables.

    Expected environment variables:
        PHYS_OMEGA: Rotation frequency Ω (default: 0.5)
        PHYS_EPS_DD: Dipolar interaction strength ε_dd (default: 0.5)
        PHYS_N: Particle number N (default: 10000)

    Returns:
        Dictionary of physical parameters.
    """
    params = {}

    try:
        params["omega"] = float(os.getenv("PHYS_OMEGA", "0.5"))
    except ValueError:
        logger.warning("Invalid PHYS_OMEGA. Using default 0.5.")
        params["omega"] = 0.5

    try:
        params["eps_dd"] = float(os.getenv("PHYS_EPS_DD", "0.5"))
    except ValueError:
        logger.warning("Invalid PHYS_EPS_DD. Using default 0.5.")
        params["eps_dd"] = 0.5

    try:
        params["N"] = int(os.getenv("PHYS_N", "10000"))
        if params["N"] <= 0:
            raise ValueError("N must be positive.")
    except ValueError:
        logger.warning("Invalid PHYS_N. Using default 10000.")
        params["N"] = 10000

    return params


def create_grid_config(run_full_grid: Optional[bool] = None) -> GridConfig:
    """
    Factory function to create a fully configured GridConfig instance.

    Args:
        run_full_grid: Optional override for the RUN_FULL_GRID environment variable.

    Returns:
        A GridConfig instance with values loaded from environment or defaults.
    """
    resolution = get_grid_resolution(run_full_grid)
    domain_size = get_domain_size()
    dt = get_time_step()
    t_max = get_max_time()
    physical_params = load_physical_params()

    logger.info(
        f"GridConfig created: resolution={resolution}, domain={domain_size}, "
        f"dt={dt}, t_max={t_max}, params={physical_params}"
    )

    return GridConfig(
        resolution=resolution,
        domain_size=domain_size,
        run_full_grid=run_full_grid if run_full_grid is not None else (os.getenv("RUN_FULL_GRID", "false").lower() in ("true", "1", "yes")),
        dt=dt,
        t_max=t_max,
        physical_params=physical_params
    )


def validate_config(config: GridConfig) -> bool:
    """
    Validate the grid configuration for consistency and physical plausibility.

    Args:
        config: The GridConfig instance to validate.

    Returns:
        True if valid, False otherwise.
    """
    if config.resolution[0] <= 0 or config.resolution[1] <= 0:
        logger.error("Grid resolution must be positive.")
        return False

    if config.domain_size <= 0:
        logger.error("Domain size must be positive.")
        return False

    if config.dt <= 0:
        logger.error("Time step must be positive.")
        return False

    if config.t_max <= 0:
        logger.error("Max time must be positive.")
        return False

    if "omega" in config.physical_params and config.physical_params["omega"] >= 1.0:
        logger.warning("Rotation frequency Ω >= 1.0 may lead to instability.")

    if "eps_dd" in config.physical_params and config.physical_params["eps_dd"] < 0:
        logger.warning("Negative dipolar interaction strength may be unphysical.")

    logger.info("Grid configuration validation passed.")
    return True