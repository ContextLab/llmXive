import numpy as np
from scipy.integrate import solve_ivp
from typing import Tuple, Optional, Dict, Any, List
import logging
from config import get_system_params, NoiseType
from utils.data_models import Trajectory

logger = logging.getLogger(__name__)

def lorenz_system(t, state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    """
    Computes the derivatives for the Lorenz system.

    dx/dt = sigma * (y - x)
    dy/dt = x * (rho - z) - y
    dz/dt = x * y - beta * z
    """
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

def rossler_system(t, state, a=0.2, b=0.2, c=5.7):
    """
    Computes the derivatives for the Rössler system.

    dx/dt = -y - z
    dy/dt = x + a * y
    dz/dt = b + z * (x - c)
    """
    x, y, z = state
    dxdt = -y - z
    dydt = x + a * y
    dzdt = b + z * (x - c)
    return [dxdt, dydt, dzdt]

def integrate_system(
    system_func,
    initial_state: np.ndarray,
    t_span: Tuple[float, float],
    dt: float = 0.01,
    params: Optional[Dict[str, float]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Integrates a dynamical system using scipy.integrate.solve_ivp.

    Args:
        system_func: Function defining the system derivatives.
        initial_state: Initial condition vector.
        t_span: Tuple (t_start, t_end).
        dt: Time step for output sampling.
        params: Optional dictionary of parameters to pass to system_func.

    Returns:
        Tuple of (time_array, state_array).
    """
    t_eval = np.arange(t_span[0], t_span[1], dt)
    args = tuple(params.values()) if params else ()

    sol = solve_ivp(
        system_func,
        t_span,
        initial_state,
        t_eval=t_eval,
        args=args,
        method='RK45',
        rtol=1e-9,
        atol=1e-9
    )

    if not sol.success:
        logger.warning(f"Integration failed: {sol.message}")
        raise RuntimeError(f"Integration failed: {sol.message}")

    return sol.t, sol.y.T

def validate_trajectory(trajectory: Trajectory, min_length: int = 1000) -> bool:
    """
    Validates a trajectory object.

    Checks:
        - No NaN or Inf values.
        - Minimum length threshold.

    Args:
        trajectory: The trajectory to validate.
        min_length: Minimum required number of time steps.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    if np.any(np.isnan(trajectory.state)) or np.any(np.isinf(trajectory.state)):
        raise ValueError("Trajectory contains NaN or Inf values.")
    if len(trajectory.t) < min_length:
        raise ValueError(f"Trajectory length ({len(trajectory.t)}) is below minimum ({min_length}).")
    return True

def generate_lorenz_trajectory(
    seed: int,
    t_end: float = 100.0,
    dt: float = 0.01,
    initial_state: Optional[np.ndarray] = None,
    params: Optional[Dict[str, float]] = None
) -> Trajectory:
    """
    Generates a clean Lorenz attractor trajectory.

    Args:
        seed: Random seed for reproducibility (used for initial state if not provided).
        t_end: End time of integration.
        dt: Time step.
        initial_state: Optional initial state. Defaults to random small perturbation.
        params: Optional system parameters (sigma, rho, beta).

    Returns:
        Trajectory object.
    """
    np.random.seed(seed)
    if initial_state is None:
        initial_state = np.random.rand(3) * 0.1
    else:
        initial_state = np.array(initial_state)

    default_params = get_system_params('lorenz')
    if params:
        default_params.update(params)

    t, state = integrate_system(
        lorenz_system,
        initial_state,
        (0, t_end),
        dt,
        params=default_params
    )

    trajectory = Trajectory(
        system_type='lorenz',
        seed=seed,
        t=t,
        state=state,
        params=default_params
    )

    validate_trajectory(trajectory)
    logger.info(f"Generated Lorenz trajectory (seed={seed}, length={len(t)})")
    return trajectory

def generate_rossler_trajectory(
    seed: int,
    t_end: float = 100.0,
    dt: float = 0.01,
    initial_state: Optional[np.ndarray] = None,
    params: Optional[Dict[str, float]] = None
) -> Trajectory:
    """
    Generates a clean Rössler attractor trajectory.

    Args:
        seed: Random seed for reproducibility.
        t_end: End time of integration.
        dt: Time step.
        initial_state: Optional initial state.
        params: Optional system parameters (a, b, c).

    Returns:
        Trajectory object.
    """
    np.random.seed(seed)
    if initial_state is None:
        initial_state = np.random.rand(3) * 0.1
    else:
        initial_state = np.array(initial_state)

    default_params = get_system_params('rossler')
    if params:
        default_params.update(params)

    t, state = integrate_system(
        rossler_system,
        initial_state,
        (0, t_end),
        dt,
        params=default_params
    )

    trajectory = Trajectory(
        system_type='rossler',
        seed=seed,
        t=t,
        state=state,
        params=default_params
    )

    validate_trajectory(trajectory)
    logger.info(f"Generated Rössler trajectory (seed={seed}, length={len(t)})")
    return trajectory

def get_generation_functions() -> Dict[str, callable]:
    """Returns a mapping of system names to their generation functions."""
    return {
        'lorenz': generate_lorenz_trajectory,
        'rossler': generate_rossler_trajectory
    }