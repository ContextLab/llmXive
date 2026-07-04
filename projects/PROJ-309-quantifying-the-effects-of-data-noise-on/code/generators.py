import numpy as np
from scipy.integrate import solve_ivp
from typing import Tuple, Dict, Any, Optional
import logging
from code.utils.data_models import Trajectory
from code.config import LORENZ_PARAMS, ROSSLER_PARAMS, DT, T_MAX

logger = logging.getLogger(__name__)

def lorenz_system(t, state, sigma=10.0, rho=28.0, beta=8.0/3.0):
    """Lorenz system ODE."""
    x, y, z = state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

def rossler_system(t, state, a=0.2, b=0.2, c=5.7):
    """Rossler system ODE."""
    x, y, z = state
    dxdt = -y - z
    dydt = x + a * y
    dzdt = b + z * (x - c)
    return [dxdt, dydt, dzdt]

def validate_trajectory(traj: Trajectory) -> bool:
    """Validate trajectory data."""
    if traj.state is None:
        return False
    if np.any(np.isnan(traj.state)):
        logger.warning("Trajectory contains NaN values")
        return False
    if len(traj.state) < 100:
        logger.warning("Trajectory too short")
        return False
    return True

def integrate_system(system_func, params: Dict[str, Any], seed: int) -> np.ndarray:
    """Integrate a dynamical system."""
    np.random.seed(seed)
    t_span = (0, T_MAX)
    t_eval = np.arange(0, T_MAX, DT)
    
    sol = solve_ivp(
        system_func,
        t_span,
        params["x0"],
        t_eval=t_eval,
        method='RK45',
        rtol=1e-6,
        atol=1e-9
    )
    
    if not sol.success:
        logger.error(f"Integration failed: {sol.message}")
        return None
        
    return sol.y.T

def generate_lorenz_trajectory(seed: int = 42) -> Trajectory:
    """Generate Lorenz attractor trajectory."""
    state = integrate_system(lorenz_system, LORENZ_PARAMS, seed)
    if state is None:
        raise RuntimeError("Failed to generate Lorenz trajectory")
    return Trajectory(state=state, system_type="lorenz", seed=seed, params=LORENZ_PARAMS)

def generate_rossler_trajectory(seed: int = 42) -> Trajectory:
    """Generate Rossler attractor trajectory."""
    state = integrate_system(rossler_system, ROSSLER_PARAMS, seed)
    if state is None:
        raise RuntimeError("Failed to generate Rossler trajectory")
    return Trajectory(state=state, system_type="rossler", seed=seed, params=ROSSLER_PARAMS)