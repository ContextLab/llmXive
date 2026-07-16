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

    Parameters:
    -----------
    t : float
        Current time (unused, but required by solve_ivp).
    state : array_like
        Current state [x, y, z].
    sigma : float
        Prandtl number.
    rho : float
        Rayleigh number.
    beta : float
        Geometric factor.

    Returns:
    --------
    list
        Derivatives [dx/dt, dy/dt, dz/dt].
    """
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

def rossler_system(t, state, a=0.2, b=0.2, c=5.7):
    """
    Computes the derivatives for the Rössler system.

    Parameters:
    -----------
    t : float
        Current time (unused, but required by solve_ivp).
    state : array_like
        Current state [x, y, z].
    a : float
        System parameter a.
    b : float
        System parameter b.
    c : float
        System parameter c.

    Returns:
    --------
    list
        Derivatives [dx/dt, dy/dt, dz/dt].
    """
    x, y, z = state
    dxdt = -y - z
    dydt = x + a * y
    dzdt = b + z * (x - c)
    return [dxdt, dydt, dzdt]

def integrate_system(system_func, initial_state, t_span, dt=0.01, **params):
    """
    Integrates a dynamical system using scipy.integrate.solve_ivp.

    Parameters:
    -----------
    system_func : callable
        The system function (e.g., lorenz_system).
    initial_state : array_like
        Initial conditions [x0, y0, z0].
    t_span : tuple
        Time interval (t_start, t_end).
    dt : float
        Time step for output points.
    **params : dict
        Additional parameters for the system function.

    Returns:
    --------
    Trajectory
        A Trajectory object containing time, state, and metadata.
    """
    t_eval = np.arange(t_span[0], t_span[1], dt)
    
    try:
        sol = solve_ivp(
            system_func,
            t_span,
            initial_state,
            t_eval=t_eval,
            args=tuple(params.values()) if params else (),
            method='RK45',
            rtol=1e-9,
            atol=1e-9
        )
    except Exception as e:
        logger.error(f"Integration failed for system {system_func.__name__}: {e}")
        raise

    if not sol.success:
        msg = f"Integration overflow or failure: {sol.message}"
        logger.warning(msg)
        # Log detailed metadata about the failure context
        logger.warning(f"Integration metadata: t_span={t_span}, initial_state={initial_state}, params={params}")
        # Raise an error to ensure the pipeline fails loudly rather than returning garbage
        raise RuntimeError(msg)

    if len(sol.t) < 10:
        msg = "Integration produced too few points (< 10). Likely overflow or instability."
        logger.warning(msg)
        logger.warning(f"Integration metadata: t_span={t_span}, initial_state={initial_state}")
        raise RuntimeError(msg)

    logger.info(f"Integration successful: {len(sol.t)} points generated.")
    logger.info(f"Trajectory bounds: t=[{sol.t[0]:.2f}, {sol.t[-1]:.2f}], "
                f"state_range=[{sol.y.min():.4f}, {sol.y.max():.4f}]")

    return Trajectory(
        time=sol.t,
        state=sol.y.T,
        metadata={
            'system_name': system_func.__name__,
            't_start': t_span[0],
            't_end': t_span[1],
            'dt': dt,
            'n_points': len(sol.t),
            'params': params,
            'initial_state': initial_state,
            'success': True
        }
    )

def validate_trajectory(trajectory: Trajectory, min_length: int = 1000) -> bool:
    """
    Validates a trajectory for NaNs, infinities, and minimum length.

    Parameters:
    -----------
    trajectory : Trajectory
        The trajectory to validate.
    min_length : int
        Minimum required number of time points.

    Returns:
    --------
    bool
        True if valid, raises ValueError otherwise.
    """
    if np.any(np.isnan(trajectory.state)):
        msg = "Trajectory contains NaN values."
        logger.error(msg)
        logger.error(f"Validation metadata: shape={trajectory.state.shape}, t_span={trajectory.time[0]}-{trajectory.time[-1]}")
        raise ValueError(msg)

    if np.any(np.isinf(trajectory.state)):
        msg = "Trajectory contains Inf values."
        logger.error(msg)
        logger.error(f"Validation metadata: shape={trajectory.state.shape}, t_span={trajectory.time[0]}-{trajectory.time[-1]}")
        raise ValueError(msg)

    if len(trajectory.time) < min_length:
        msg = f"Trajectory too short: {len(trajectory.time)} < {min_length}."
        logger.error(msg)
        logger.error(f"Validation metadata: shape={trajectory.state.shape}")
        raise ValueError(msg)

    logger.info("Trajectory validation passed.")
    return True

def generate_lorenz_trajectory(initial_state=None, t_span=(0.0, 100.0), dt=0.01, seed=None) -> Trajectory:
    """
    Generates a Lorenz attractor trajectory.

    Parameters:
    -----------
    initial_state : array_like, optional
        Initial conditions. Defaults to [1.0, 1.0, 1.0].
    t_span : tuple
        Time interval.
    dt : float
        Time step.
    seed : int, optional
        Random seed for reproducibility (mostly for initial state if generated).

    Returns:
    --------
    Trajectory
        The generated trajectory.
    """
    if seed is not None:
        np.random.seed(seed)
    
    params = get_system_params('lorenz')
    sigma = params.get('sigma', 10.0)
    rho = params.get('rho', 28.0)
    beta = params.get('beta', 8.0/3.0)

    if initial_state is None:
        initial_state = [1.0, 1.0, 1.0]

    logger.info(f"Generating Lorenz trajectory with seed={seed}, t_span={t_span}, dt={dt}")
    logger.info(f"System params: sigma={sigma}, rho={rho}, beta={beta}")
    
    trajectory = integrate_system(
        lorenz_system,
        initial_state,
        t_span,
        dt=dt,
        sigma=sigma,
        rho=rho,
        beta=beta
    )
    
    validate_trajectory(trajectory)
    return trajectory

def generate_rossler_trajectory(initial_state=None, t_span=(0.0, 100.0), dt=0.01, seed=None) -> Trajectory:
    """
    Generates a Rössler attractor trajectory.

    Parameters:
    -----------
    initial_state : array_like, optional
        Initial conditions. Defaults to [1.0, 1.0, 1.0].
    t_span : tuple
        Time interval.
    dt : float
        Time step.
    seed : int, optional
        Random seed for reproducibility.

    Returns:
    --------
    Trajectory
        The generated trajectory.
    """
    if seed is not None:
        np.random.seed(seed)

    params = get_system_params('rossler')
    a = params.get('a', 0.2)
    b = params.get('b', 0.2)
    c = params.get('c', 5.7)

    if initial_state is None:
        initial_state = [1.0, 1.0, 1.0]

    logger.info(f"Generating Rössler trajectory with seed={seed}, t_span={t_span}, dt={dt}")
    logger.info(f"System params: a={a}, b={b}, c={c}")

    trajectory = integrate_system(
        rossler_system,
        initial_state,
        t_span,
        dt=dt,
        a=a,
        b=b,
        c=c
    )

    validate_trajectory(trajectory)
    return trajectory

def get_generation_functions() -> Dict[str, callable]:
    """
    Returns a dictionary of available generation functions.

    Returns:
    --------
    dict
        Mapping of system name to generation function.
    """
    return {
        'lorenz': generate_lorenz_trajectory,
        'rossler': generate_rossler_trajectory
    }
