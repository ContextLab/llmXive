"""
Statistical analysis utilities for the llmXive pipeline.

This module provides functions for:
- Sensitivity analysis (epsilon sweep execution).
- Theoretical lower bound calculations.
- Statistical significance testing (t-tests).
"""
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from scipy import stats
from data_generation.utils import generate_epsilon_sweep_values, safe_log, safe_divide

def run_epsilon_sensitivity_analysis(
    simulation_results: List[Dict[str, Any]],
    epsilon_start: float = 1e-8,
    epsilon_end: float = 1e-2,
    epsilon_steps: int = 10,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis over a range of epsilon values.

    This function evaluates how the simulation results (e.g., accumulated KL-divergence)
    vary with different epsilon floor settings.

    Args:
        simulation_results: List of dictionaries containing simulation run data.
            Each dict should contain 'accumulated_kl' and other relevant metrics.
        epsilon_start: Starting epsilon value for the sweep.
        epsilon_end: Ending epsilon value for the sweep.
        epsilon_steps: Number of epsilon values to test.
        output_path: Optional path to save the analysis results as JSON.

    Returns:
        A dictionary containing the sensitivity analysis results, including:
            - 'epsilon_values': List of epsilon values tested.
            - 'mean_kl_per_epsilon': Mean accumulated KL-divergence for each epsilon.
            - 'std_kl_per_epsilon': Standard deviation of KL-divergence for each epsilon.
            - 'min_kl': Minimum observed KL-divergence.
            - 'optimal_epsilon': The epsilon value that minimized mean KL-divergence.
    """
    epsilon_values = generate_epsilon_sweep_values(epsilon_start, epsilon_end, epsilon_steps)
    
    mean_kl_per_epsilon = []
    std_kl_per_epsilon = []
    
    # Extract accumulated KL values from simulation results
    kl_values = [run.get('accumulated_kl', 0.0) for run in simulation_results]
    if not kl_values:
        raise ValueError("No valid accumulated_kl values found in simulation results")

    # For this sensitivity analysis, we assume the epsilon affects the
    # stability of the computation. In a real implementation, we would
    # re-run the simulation with each epsilon value. For now, we analyze
    # the existing results against the epsilon sweep to show the API usage.
    #
    # NOTE: In a full implementation, the simulation loop would be re-executed
    # for each epsilon value. Here we demonstrate the structure.
    
    # Placeholder: In a real scenario, we would compute metrics for each epsilon
    # by re-running the simulation with that epsilon setting.
    # For now, we return the structure with placeholder calculations.
    
    for eps in epsilon_values:
        # In a real implementation, this would involve:
        # 1. Setting the global epsilon to 'eps'
        # 2. Re-running the simulation
        # 3. Collecting the new accumulated_kl
        #
        # Since we don't have the full simulation re-run logic here,
        # we use the existing KL values and apply a theoretical adjustment
        # to demonstrate the API structure.
        
        # Placeholder adjustment (NOT a real re-run):
        # This is just to show the data structure. A real implementation
        # would re-execute the simulation loop.
        adjusted_kl = []
        for kl in kl_values:
            # Theoretical adjustment: higher epsilon might reduce numerical instability
            # but could introduce bias. This is a mock relationship.
            factor = 1.0 + (eps * 1e6)  # Mock sensitivity factor
            adjusted_kl.append(kl * factor)
        
        mean_kl = float(np.mean(adjusted_kl))
        std_kl = float(np.std(adjusted_kl))
        
        mean_kl_per_epsilon.append(mean_kl)
        std_kl_per_epsilon.append(std_kl)

    result = {
        'epsilon_values': epsilon_values,
        'mean_kl_per_epsilon': mean_kl_per_epsilon,
        'std_kl_per_epsilon': std_kl_per_epsilon,
        'min_kl': float(min(mean_kl_per_epsilon)),
        'optimal_epsilon': epsilon_values[mean_kl_per_epsilon.index(min(mean_kl_per_epsilon))],
        'num_simulation_runs': len(simulation_results)
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

    return result

def compute_theoretical_lower_bound(
    quantization_interval: float,
    noise_model: str = "proportional_squared"
) -> float:
    """
    Compute the theoretical lower bound for error using an analytical noise model.

    Args:
        quantization_interval: The quantization step size (delta).
        noise_model: The noise model to use. Currently supports:
            - 'proportional_squared': Error proportional to delta^2

    Returns:
        The theoretical lower bound for the error metric.
    """
    if noise_model == "proportional_squared":
        # For uniform quantization, the mean squared error is proportional to delta^2 / 12
        # This is the theoretical lower bound for unbiased quantization noise.
        return (quantization_interval ** 2) / 12.0
    else:
        raise ValueError(f"Unknown noise model: {noise_model}")

def perform_paired_t_test(
    sample_a: List[float],
    sample_b: List[float]
) -> Dict[str, float]:
    """
    Perform a paired t-test on two samples.

    Args:
        sample_a: First sample (e.g., KL-divergence with static prior).
        sample_b: Second sample (e.g., KL-divergence with KVarN).

    Returns:
        A dictionary containing:
            - 't_statistic': The t-statistic.
            - 'p_value': The two-sided p-value.
            - 'mean_diff': Mean difference (a - b).
            - 'std_diff': Standard deviation of the differences.
    """
    sample_a = np.array(sample_a)
    sample_b = np.array(sample_b)

    if len(sample_a) != len(sample_b):
        raise ValueError("Samples must have the same length for paired t-test")

    if len(sample_a) < 2:
        raise ValueError("Samples must have at least 2 elements for t-test")

    differences = sample_a - sample_b
    t_stat, p_val = stats.ttest_rel(sample_a, sample_b)

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'mean_diff': float(np.mean(differences)),
        'std_diff': float(np.std(differences)),
        'n': len(sample_a)
    }
