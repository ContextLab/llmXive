"""
Simulation metrics module for energy propagation analysis.

This module provides functions to calculate various metrics from spin system simulations,
including energy density profiles, spatial variance, and transient phase characteristics.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from code.src.simulation.stability import check_numerical_stability

logger = logging.getLogger(__name__)


def calculate_energy_density_profile(energy_history: List[float], 
                                     time_steps: List[int]) -> Dict[str, Any]:
    """
    Calculate the energy density profile over time.
    
    Args:
        energy_history: List of total energy values at each time step.
        time_steps: List of time step indices.
        
    Returns:
        Dictionary containing:
            - 'time_steps': list of time steps
            - 'energy_density': list of energy density values (energy / num_spins)
            - 'mean_energy': mean energy over the simulation
            - 'std_energy': standard deviation of energy
            - 'initial_energy': energy at t=0
            - 'final_energy': energy at final time step
    """
    if not energy_history or not time_steps:
        logger.warning("Empty energy history or time steps provided")
        return {
            'time_steps': [],
            'energy_density': [],
            'mean_energy': 0.0,
            'std_energy': 0.0,
            'initial_energy': 0.0,
            'final_energy': 0.0,
            'num_spins': 0
        }
    
    num_spins = len(energy_history[0]) if isinstance(energy_history[0], (list, np.ndarray)) else 1
    if num_spins == 1 and len(energy_history) > 1:
        # If energy_history is a list of scalars, num_spins is 1
        num_spins = 1
    elif isinstance(energy_history[0], (list, np.ndarray)):
        num_spins = len(energy_history[0])
    
    # Calculate energy density (energy per spin)
    if num_spins > 1:
        energy_density = [e / num_spins for e in energy_history]
    else:
        energy_density = energy_history
    
    return {
        'time_steps': time_steps,
        'energy_density': energy_density,
        'mean_energy': float(np.mean(energy_history)),
        'std_energy': float(np.std(energy_history)),
        'initial_energy': float(energy_history[0]),
        'final_energy': float(energy_history[-1]),
        'num_spins': num_spins
    }


def calculate_spatial_variance(spins_history: List[np.ndarray], 
                               adjacency_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Calculate spatial variance of spin configurations over time.
    
    Spatial variance measures how much the spin values vary across the network
    at each time step, indicating the degree of order/disorder in the system.
    
    Args:
        spins_history: List of spin configurations (1D arrays) at each time step.
        adjacency_matrix: Network adjacency matrix.
        
    Returns:
        Dictionary containing:
            - 'time_steps': list of time steps
            - 'spatial_variance': list of variance values
            - 'mean_variance': mean spatial variance
            - 'max_variance': maximum spatial variance
            - 'min_variance': minimum spatial variance
            - 'is_monotonic': whether variance generally increases (for stability check)
    """
    if not spins_history:
        logger.warning("Empty spins history provided")
        return {
            'time_steps': [],
            'spatial_variance': [],
            'mean_variance': 0.0,
            'max_variance': 0.0,
            'min_variance': 0.0,
            'is_monotonic': True
        }
    
    variances = []
    for spins in spins_history:
        if isinstance(spins, np.ndarray):
            variance = float(np.var(spins))
        else:
            variance = float(np.var(np.array(spins)))
        variances.append(variance)
    
    # Check monotonicity (variance should generally increase or stay stable)
    # Allow small decreases due to numerical noise
    monotonic_violations = 0
    for i in range(1, len(variances)):
        if variances[i] < variances[i-1] - 1e-6:  # Small tolerance
            monotonic_violations += 1
    
    is_monotonic = monotonic_violations <= max(1, len(variances) * 0.1)  # Allow 10% violations
    
    return {
        'time_steps': list(range(len(spins_history))),
        'spatial_variance': variances,
        'mean_variance': float(np.mean(variances)),
        'max_variance': float(np.max(variances)),
        'min_variance': float(np.min(variances)),
        'is_monotonic': is_monotonic,
        'monotonic_violations': monotonic_violations
    }


def extract_transient_phase_metrics(energy_history: List[float],
                                    spins_history: List[np.ndarray],
                                    time_steps: List[int],
                                    adjacency_matrix: Optional[np.ndarray] = None,
                                    transient_threshold: float = 0.1,
                                    min_transient_steps: int = 5) -> Dict[str, Any]:
    """
    Extract metrics characterizing the transient phase of the simulation.
    
    The transient phase is the initial period where the system evolves from its
    initial state toward equilibrium. This function identifies the transient
    phase and calculates key metrics about it.
    
    Args:
        energy_history: List of total energy values at each time step.
        spins_history: List of spin configurations at each time step.
        time_steps: List of time step indices.
        adjacency_matrix: Network adjacency matrix (optional, for spatial analysis).
        transient_threshold: Threshold for detecting when transient phase ends
                           (fraction of total energy change).
        min_transient_steps: Minimum number of steps considered as transient.
        
    Returns:
        Dictionary containing:
            - 'transient_start': index where transient phase starts
            - 'transient_end': index where transient phase ends
            - 'transient_duration': number of steps in transient phase
            - 'transient_energy_change': total energy change during transient
            - 'transient_energy_rate': average rate of energy change
            - 'transient_variance_change': change in spatial variance during transient
            - 'equilibrium_detected': whether equilibrium was reached
            - 'equilibrium_time': time step when equilibrium was detected
            - 'pre_transient_metrics': metrics before transient
            - 'transient_metrics': metrics during transient
            - 'post_transient_metrics': metrics after transient
    """
    if not energy_history or not spins_history or not time_steps:
        logger.warning("Empty history provided for transient phase extraction")
        return {
            'transient_start': 0,
            'transient_end': 0,
            'transient_duration': 0,
            'transient_energy_change': 0.0,
            'transient_energy_rate': 0.0,
            'transient_variance_change': 0.0,
            'equilibrium_detected': False,
            'equilibrium_time': None,
            'pre_transient_metrics': {},
            'transient_metrics': {},
            'post_transient_metrics': {},
            'num_steps': 0
        }
    
    num_steps = len(energy_history)
    
    # Calculate energy changes
    energy_changes = np.diff(energy_history)
    total_energy_change = abs(energy_history[-1] - energy_history[0])
    
    if total_energy_change == 0:
        # No energy change, entire simulation is equilibrium
        return {
            'transient_start': 0,
            'transient_end': 0,
            'transient_duration': 0,
            'transient_energy_change': 0.0,
            'transient_energy_rate': 0.0,
            'transient_variance_change': 0.0,
            'equilibrium_detected': True,
            'equilibrium_time': 0,
            'pre_transient_metrics': {},
            'transient_metrics': {},
            'post_transient_metrics': {},
            'num_steps': num_steps
        }
    
    # Detect transient phase end: when energy change rate drops below threshold
    # Use a rolling window to smooth the change rate
    window_size = min(5, num_steps // 2) if num_steps > 2 else 1
    if window_size < 1:
        window_size = 1
    
    smoothed_changes = []
    for i in range(num_steps - 1):
        start = max(0, i - window_size // 2)
        end = min(num_steps - 1, i + window_size // 2 + 1)
        if end > start:
            avg_change = np.mean(np.abs(energy_changes[start:end]))
        else:
            avg_change = abs(energy_changes[i]) if i < len(energy_changes) else 0
        smoothed_changes.append(avg_change)
    
    # Find when the smoothed change rate drops below threshold
    threshold_value = transient_threshold * (total_energy_change / num_steps)
    transient_end = num_steps - 1  # Default to end if not detected
    
    for i, change_rate in enumerate(smoothed_changes):
        if change_rate < threshold_value:
            transient_end = i + min_transient_steps
            break
    
    # Ensure transient_end is within bounds
    transient_end = min(transient_end, num_steps - 1)
    transient_start = 0
    
    # Calculate transient duration
    transient_duration = max(min_transient_steps, transient_end - transient_start)
    
    # Extract metrics for each phase
    pre_transient_end = transient_start
    post_transient_start = transient_end + 1
    
    # Pre-transient metrics (usually just initial state)
    pre_transient_metrics = {}
    if pre_transient_end > 0:
        pre_transient_metrics = {
            'energy_mean': float(np.mean(energy_history[:pre_transient_end+1])),
            'energy_std': float(np.std(energy_history[:pre_transient_end+1])),
            'num_steps': pre_transient_end + 1
        }
    
    # Transient metrics
    transient_energy = energy_history[transient_start:transient_end+1]
    transient_energy_change = abs(transient_energy[-1] - transient_energy[0]) if len(transient_energy) > 1 else 0.0
    transient_energy_rate = transient_energy_change / transient_duration if transient_duration > 0 else 0.0
    
    transient_metrics = {
        'energy_mean': float(np.mean(transient_energy)) if transient_energy else 0.0,
        'energy_std': float(np.std(transient_energy)) if transient_energy else 0.0,
        'energy_change': transient_energy_change,
        'energy_rate': transient_energy_rate,
        'num_steps': transient_duration
    }
    
    # Post-transient metrics
    post_transient_metrics = {}
    if post_transient_start < num_steps:
        post_energy = energy_history[post_transient_start:]
        post_transient_metrics = {
            'energy_mean': float(np.mean(post_energy)),
            'energy_std': float(np.std(post_energy)),
            'num_steps': num_steps - post_transient_start
        }
    
    # Calculate spatial variance change during transient if adjacency matrix provided
    transient_variance_change = 0.0
    if adjacency_matrix is not None and len(spins_history) > transient_end:
        # Calculate variance at start and end of transient
        start_spins = spins_history[transient_start] if isinstance(spins_history[transient_start], np.ndarray) else np.array(spins_history[transient_start])
        end_spins = spins_history[transient_end] if isinstance(spins_history[transient_end], np.ndarray) else np.array(spins_history[transient_end])
        
        start_variance = float(np.var(start_spins))
        end_variance = float(np.var(end_spins))
        transient_variance_change = end_variance - start_variance
    
    # Check if equilibrium was detected
    equilibrium_detected = transient_end < num_steps - 1
    equilibrium_time = transient_end if equilibrium_detected else None
    
    return {
        'transient_start': transient_start,
        'transient_end': transient_end,
        'transient_duration': transient_duration,
        'transient_energy_change': transient_energy_change,
        'transient_energy_rate': transient_energy_rate,
        'transient_variance_change': transient_variance_change,
        'equilibrium_detected': equilibrium_detected,
        'equilibrium_time': equilibrium_time,
        'pre_transient_metrics': pre_transient_metrics,
        'transient_metrics': transient_metrics,
        'post_transient_metrics': post_transient_metrics,
        'num_steps': num_steps
    }


def calculate_relaxation_time(energy_history: List[float], 
                              time_steps: List[int],
                              threshold_fraction: float = 0.05) -> Dict[str, Any]:
    """
    Calculate the relaxation time of the system.
    
    Relaxation time is the time it takes for the system to reach within a certain
    fraction of its final equilibrium value.
    
    Args:
        energy_history: List of total energy values at each time step.
        time_steps: List of time step indices.
        threshold_fraction: Fraction of final value to consider as equilibrium.
        
    Returns:
        Dictionary containing:
            - 'relaxation_time': time step when equilibrium is reached
            - 'final_energy': final energy value
            - 'initial_energy': initial energy value
            - 'equilibrium_threshold': the threshold value used
            - 'reached_equilibrium': whether equilibrium was reached
    """
    if not energy_history or not time_steps:
        logger.warning("Empty history for relaxation time calculation")
        return {
            'relaxation_time': None,
            'final_energy': 0.0,
            'initial_energy': 0.0,
            'equilibrium_threshold': 0.0,
            'reached_equilibrium': False
        }
    
    initial_energy = energy_history[0]
    final_energy = energy_history[-1]
    total_change = abs(final_energy - initial_energy)
    
    if total_change == 0:
        return {
            'relaxation_time': 0,
            'final_energy': float(final_energy),
            'initial_energy': float(initial_energy),
            'equilibrium_threshold': 0.0,
            'reached_equilibrium': True
        }
    
    threshold = threshold_fraction * total_change
    equilibrium_threshold = final_energy + np.sign(final_energy - initial_energy) * threshold
    
    relaxation_time = None
    for i, energy in enumerate(energy_history):
        if abs(energy - final_energy) <= threshold:
            relaxation_time = time_steps[i] if i < len(time_steps) else i
            break
    
    return {
        'relaxation_time': relaxation_time,
        'final_energy': float(final_energy),
        'initial_energy': float(initial_energy),
        'equilibrium_threshold': float(equilibrium_threshold),
        'reached_equilibrium': relaxation_time is not None
    }


def aggregate_transient_report(simulation_id: str,
                               transient_metrics: Dict[str, Any],
                               relaxation_metrics: Dict[str, Any],
                               stability_check: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate transient phase metrics into a comprehensive report.
    
    Args:
        simulation_id: Unique identifier for the simulation run.
        transient_metrics: Output from extract_transient_phase_metrics.
        relaxation_metrics: Output from calculate_relaxation_time.
        stability_check: Output from stability checks.
        
    Returns:
        Dictionary containing aggregated transient phase report.
    """
    report = {
        'simulation_id': simulation_id,
        'timestamp': str(np.datetime64('now')),
        'transient_phase': transient_metrics,
        'relaxation': relaxation_metrics,
        'stability': stability_check,
        'summary': {
            'total_steps': transient_metrics.get('num_steps', 0),
            'transient_steps': transient_metrics.get('transient_duration', 0),
            'equilibrium_steps': transient_metrics.get('num_steps', 0) - transient_metrics.get('transient_duration', 0),
            'equilibrium_reached': transient_metrics.get('equilibrium_detected', False),
            'relaxation_time': relaxation_metrics.get('relaxation_time'),
            'numerically_stable': stability_check.get('is_stable', True)
        }
    }
    
    return report


def save_transient_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save transient phase metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing transient phase metrics.
        output_path: Path to save the JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logger.info(f"Transient metrics saved to {output_path}")


def main():
    """
    Main function to demonstrate transient phase metric extraction.
    This is typically called by a script to process simulation results.
    """
    # Example usage with dummy data
    import numpy as np
    
    # Simulate some energy history
    np.random.seed(42)
    num_steps = 100
    energy_history = list(np.cumsum(np.random.randn(num_steps) * 0.1) + 10)
    spins_history = [np.random.choice([-1, 1], 10) for _ in range(num_steps)]
    time_steps = list(range(num_steps))
    
    # Create a simple adjacency matrix (random graph)
    adjacency_matrix = np.random.rand(10, 10)
    adjacency_matrix = (adjacency_matrix + adjacency_matrix.T) / 2
    np.fill_diagonal(adjacency_matrix, 0)
    adjacency_matrix = (adjacency_matrix > 0.5).astype(int)
    
    # Extract transient metrics
    transient_metrics = extract_transient_phase_metrics(
        energy_history, spins_history, time_steps, adjacency_matrix
    )
    
    # Calculate relaxation time
    relaxation_metrics = calculate_relaxation_time(energy_history, time_steps)
    
    # Stability check (dummy)
    stability_check = {'is_stable': True, 'max_value': 1.0}
    
    # Aggregate report
    report = aggregate_transient_metrics(
        "demo_simulation", transient_metrics, relaxation_metrics, stability_check
    )
    
    # Save to file
    save_transient_metrics(report, "data/analysis/transient_phase_report.json")
    
    print("Transient phase metrics extracted and saved successfully.")
    return report


if __name__ == "__main__":
    main()
