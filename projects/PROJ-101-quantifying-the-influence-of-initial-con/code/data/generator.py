"""
Generator module for coupled Lorenz oscillators.

Implements:
- Coupled Lorenz ODE system definition (N oscillators, coupling topology)
- Trajectory integration using scipy.integrate.solve_ivp (DOP853)
- Additive Gaussian white noise injection
- Two-tier noise validation (HighNoiseWarning, UnphysicalTrajectoryError)
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
    detect_divergence_rate
)

# Constants for Lorenz system
LORENZ_SIGMA = 10.0
LORENZ_RHO = 28.0
LORENZ_BETA = 8.0 / 3.0

class HighNoiseWarning(UserWarning):
    """Warning raised when noise level exceeds physical realism threshold."""
    pass

class UnphysicalTrajectoryError(Exception):
    """Error raised when trajectory diverges or exceeds physical bounds."""
    pass

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
        """Convert to dictionary for JSON serialization."""
        return {
            'time': self.time.tolist(),
            'state': self.state.tolist(),
            'noise_level': self.noise_level,
            'N_oscillators': self.N_oscillators,
            'coupling_strength': self.coupling_strength,
            'seed': self.seed,
            'is_clean': self.is_clean,
            'shape': list(self.state.shape)
        }

def lorenz_ode_single(t: float, state: np.ndarray) -> np.ndarray:
    """
    Compute derivatives for a single Lorenz oscillator.
    
    Args:
        t: Time (unused, system is autonomous)
        state: [x, y, z] state vector
        
    Returns:
        dx/dt, dy/dt, dz/dt
    """
    x, y, z = state
    dxdt = LORENZ_SIGMA * (y - x)
    dydt = x * (LORENZ_RHO - z) - y
    dzdt = x * y - LORENZ_BETA * z
    return np.array([dxdt, dydt, dzdt])

def coupled_lorenz_ode(t: float, state: np.ndarray, N: int, 
                      coupling_strength: float, 
                      coupling_topology: str = 'ring') -> np.ndarray:
    """
    Compute derivatives for N coupled Lorenz oscillators.
    
    Args:
        t: Time
        state: Flattened state vector of shape (N*3,)
        N: Number of oscillators
        coupling_strength: Strength of coupling between oscillators
        coupling_topology: 'ring' or 'all-to-all'
        
    Returns:
        Flattened derivative vector of shape (N*3,)
    """
    # Reshape to (N, 3)
    states = state.reshape(N, 3)
    dxdt = np.zeros_like(states)
    
    for i in range(N):
        # Get current oscillator state
        x, y, z = states[i]
        
        # Lorenz dynamics
        dxdt[i, 0] = LORENZ_SIGMA * (y - x)
        dxdt[i, 1] = x * (LORENZ_RHO - z) - y
        dxdt[i, 2] = x * y - LORENZ_BETA * z
        
        # Coupling term (diffusive coupling on x variable)
        if coupling_topology == 'ring':
            # Neighbors: (i-1) and (i+1) mod N
            prev_idx = (i - 1) % N
            next_idx = (i + 1) % N
            coupling = coupling_strength * (
                states[prev_idx, 0] + states[next_idx, 0] - 2 * x
            )
        elif coupling_topology == 'all-to-all':
            # All-to-all coupling
            mean_x = np.mean(states[:, 0])
            coupling = coupling_strength * (mean_x - x)
        else:
            raise ValueError(f"Unknown coupling topology: {coupling_topology}")
        
        dxdt[i, 0] += coupling
    
    return dxdt.flatten()

def generate_initial_conditions(N: int, seed: int, 
                               perturbation_scale: float = 1e-3) -> np.ndarray:
    """
    Generate initial conditions for N coupled Lorenz oscillators.
    
    Each oscillator starts near the attractor with small random perturbations
    to ensure different trajectories while maintaining physical plausibility.
    
    Args:
        N: Number of oscillators
        seed: Random seed for reproducibility
        perturbation_scale: Scale of initial perturbations
        
    Returns:
        Initial state vector of shape (N*3,)
    """
    rng = np.random.default_rng(seed)
    
    # Standard Lorenz attractor fixed points (unstable)
    # We start near one of the non-trivial fixed points
    fixed_point_x = np.sqrt(LORENZ_BETA * (LORENZ_RHO - 1))
    fixed_point_y = np.sqrt(LORENZ_BETA * (LORENZ_RHO - 1))
    fixed_point_z = LORENZ_RHO - 1
    
    initial_states = []
    for i in range(N):
        # Add small random perturbation to each oscillator
        # Each oscillator gets a slightly different starting point
        offset = rng.normal(0, perturbation_scale, 3)
        state = np.array([
            fixed_point_x + offset[0],
            fixed_point_y + offset[1],
            fixed_point_z + offset[2]
        ])
        initial_states.append(state)
    
    return np.concatenate(initial_states)

def inject_gaussian_noise(state: np.ndarray, sigma_noise: float, 
                         seed: Optional[int] = None) -> np.ndarray:
    """
    Inject additive Gaussian white noise into the state vector.
    
    Args:
        state: Clean state vector
        sigma_noise: Standard deviation of Gaussian noise
        seed: Optional random seed for reproducibility
        
    Returns:
        Noisy state vector
    """
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sigma_noise, size=state.shape)
    return state + noise

def integrate_trajectory(
    N: int,
    t_span: Tuple[float, float],
    dt: float,
    initial_state: np.ndarray,
    coupling_strength: float = 0.01,
    coupling_topology: str = 'ring',
    numerical_settings: Optional[NumericalSettings] = None,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Integrate the coupled Lorenz system using scipy's DOP853 solver.
    
    Args:
        N: Number of oscillators
        t_span: (t_start, t_end)
        dt: Output time step
        initial_state: Initial state vector
        coupling_strength: Coupling strength between oscillators
        coupling_topology: 'ring' or 'all-to-all'
        numerical_settings: Numerical integration settings
        seed: Random seed (for reproducibility, though ODE is deterministic)
        
    Returns:
        (time_array, state_array) where state_array has shape (n_points, N*3)
    """
    if numerical_settings is None:
        config = get_full_config()
        numerical_settings = config.numerical
    
    # Create time points for output
    t_eval = np.arange(t_span[0], t_span[1] + dt, dt)
    
    # Define the ODE function with partial arguments
    def ode_func(t, state):
        return coupled_lorenz_ode(
            t, state, N, coupling_strength, coupling_topology
        )
    
    # Solve using DOP853 with strict tolerances
    sol = solve_ivp(
        ode_func,
        t_span,
        initial_state,
        method='DOP853',
        t_eval=t_eval,
        rtol=numerical_settings.rtol,
        atol=numerical_settings.atol,
        dense_output=False
    )
    
    if not sol.success:
        raise NonConvergenceError(f"Integration failed: {sol.message}")
    
    # Check for NaN or Inf in solution
    if np.any(~np.isfinite(sol.y)):
        raise NumericalStabilityError("Integration produced NaN or Inf values")
    
    return sol.t, sol.y.T  # Return as (time, state) where state is (n_points, N*3)

def validate_trajectory(
    trajectory: TrajectoryData,
    max_bound: float = 100.0,
    sigma_threshold_high: float = 0.1,
    sigma_threshold_unphysical: float = 1.0
) -> None:
    """
    Validate trajectory for physical plausibility and noise levels.
    
    Raises:
        HighNoiseWarning: If sigma_noise > 0.1
        UnphysicalTrajectoryError: If sigma_noise > 1.0 OR max(|state|) > 100
    """
    # Check noise level
    if trajectory.noise_level > sigma_threshold_unphysical:
        raise UnphysicalTrajectoryError(
            f"Noise level {trajectory.noise_level} exceeds unphysical threshold {sigma_threshold_unphysical}"
        )
    
    if trajectory.noise_level > sigma_threshold_high:
        warnings.warn(
            f"High noise level detected: {trajectory.noise_level} > {sigma_threshold_high}. "
            "Trajectory may not shadow a true orbit.",
            HighNoiseWarning
        )
    
    # Check state bounds for ALL noise levels (including clean)
    max_state_magnitude = np.max(np.abs(trajectory.state))
    if max_state_magnitude > max_bound:
        raise UnphysicalTrajectoryError(
            f"Trajectory diverged: max(|state|) = {max_state_magnitude:.2f} > {max_bound}. "
            "This indicates an unphysical trajectory."
        )
    
    # Additional check: detect divergence rate
    if not trajectory.is_clean:
        divergence_rate = detect_divergence_rate(trajectory.state)
        if divergence_rate > 10.0:  # Heuristic threshold
            raise UnphysicalTrajectoryError(
                f"Excessive divergence rate detected: {divergence_rate:.2f}. "
                "Trajectory is unphysical."
            )

def generate_coupled_lorenz_trajectory(
    N: int,
    t_start: float = 0.0,
    t_end: float = 1000.0,
    dt: float = 0.01,
    sigma_noise: float = 0.0,
    coupling_strength: float = 0.01,
    coupling_topology: str = 'ring',
    seed: Optional[int] = None,
    numerical_settings: Optional[NumericalSettings] = None
) -> TrajectoryData:
    """
    Generate a complete trajectory of coupled Lorenz oscillators with optional noise.
    
    This is the main entry point for trajectory generation.
    
    Args:
        N: Number of coupled oscillators
        t_start: Start time
        t_end: End time
        dt: Output time step
        sigma_noise: Standard deviation of Gaussian noise (0.0 for clean)
        coupling_strength: Strength of coupling between oscillators
        coupling_topology: 'ring' or 'all-to-all'
        seed: Random seed for initial conditions and noise
        numerical_settings: Numerical integration settings
        
    Returns:
        TrajectoryData object containing time, state, and metadata
        
    Raises:
        HighNoiseWarning: If noise level is high but still physical
        UnphysicalTrajectoryError: If trajectory is unphysical
    """
    if seed is None:
        seed = np.random.randint(0, 2**31)
    
    # Generate initial conditions
    initial_state = generate_initial_conditions(N, seed)
    
    # Integrate clean trajectory
    time, clean_state = integrate_trajectory(
        N=N,
        t_span=(t_start, t_end),
        dt=dt,
        initial_state=initial_state,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        numerical_settings=numerical_settings,
        seed=seed
    )
    
    # Apply noise if requested
    is_clean = (sigma_noise == 0.0)
    if is_clean:
        noisy_state = clean_state.copy()
    else:
        rng = np.random.default_rng(seed + 1)  # Different seed for noise
        noise_samples = rng.normal(0, sigma_noise, size=clean_state.shape)
        noisy_state = clean_state + noise_samples
    
    # Create trajectory object
    trajectory = TrajectoryData(
        time=time,
        state=noisy_state,
        noise_level=sigma_noise,
        N_oscillators=N,
        coupling_strength=coupling_strength,
        coupling_topology=coupling_topology,
        seed=seed,
        is_clean=is_clean
    )
    
    # Validate trajectory (raises warnings/errors as appropriate)
    validate_trajectory(trajectory, sigma_threshold_high=0.1, sigma_threshold_unphysical=1.0)
    
    return trajectory

def generate_batch_trajectories(
    N: int,
    t_start: float = 0.0,
    t_end: float = 1000.0,
    dt: float = 0.01,
    noise_levels: List[float] = [0.0, 0.01, 0.1],
    coupling_strength: float = 0.01,
    coupling_topology: str = 'ring',
    base_seed: int = 42,
    trials_per_level: int = 1
) -> List[TrajectoryData]:
    """
    Generate a batch of trajectories across multiple noise levels and trials.
    
    Args:
        N: Number of oscillators
        t_start: Start time
        t_end: End time
        dt: Output time step
        noise_levels: List of noise levels to generate
        coupling_strength: Coupling strength
        coupling_topology: Coupling topology
        base_seed: Base random seed
        trials_per_level: Number of independent trials per noise level
        
    Returns:
        List of TrajectoryData objects
    """
    trajectories = []
    
    for i, sigma in enumerate(noise_levels):
        for trial in range(trials_per_level):
            seed = base_seed + i * 1000 + trial
            try:
                traj = generate_coupled_lorenz_trajectory(
                    N=N,
                    t_start=t_start,
                    t_end=t_end,
                    dt=dt,
                    sigma_noise=sigma,
                    coupling_strength=coupling_strength,
                    coupling_topology=coupling_topology,
                    seed=seed
                )
                trajectories.append(traj)
            except UnphysicalTrajectoryError as e:
                # Log and skip unphysical trajectories
                warnings.warn(f"Skipping unphysical trajectory (N={N}, sigma={sigma}, trial={trial}): {e}")
                continue
    
    return trajectories
