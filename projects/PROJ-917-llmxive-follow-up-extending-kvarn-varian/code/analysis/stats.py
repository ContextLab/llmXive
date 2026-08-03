import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from scipy import stats
from data_generation.utils import generate_epsilon_sweep_values, safe_log, safe_divide
from simulation.state import SimulationState
from simulation.sequential_sinkhorn import SequentialSinkhornSolver
from simulation.autoregressive_loop import run_single_simulation_step
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_epsilon_sensitivity_analysis(
    epsilon_values: List[float],
    num_steps: int = 100,
    num_matrices: int = 10,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run a pilot sensitivity analysis across a sweep of epsilon values.
    
    This function executes a small subset of simulation steps (default 100) 
    across the provided epsilon sweep to validate the configuration before 
    the full batch run.
    
    Args:
        epsilon_values: List of epsilon values to test.
        num_steps: Number of simulation steps to run per epsilon (pilot size).
        num_matrices: Number of synthetic matrices to generate per step.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing results for each epsilon value, including
        accumulated_kl_divergence_error_rate and variation_rate.
    """
    logger.info(f"Starting Pilot Sensitivity Analysis with {len(epsilon_values)} epsilon values.")
    logger.info(f"Configuration: {num_steps} steps, {num_matrices} matrices/step, seed={seed}")
    
    results = []
    
    for eps in epsilon_values:
        logger.info(f"Running pilot for epsilon = {eps}")
        
        # Initialize state for this epsilon run
        current_state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={},
            step_index=0,
            full_trajectory=[]
        )
        
        # Create solver with current epsilon
        solver = SequentialSinkhornSolver(epsilon=eps)
        
        # Run pilot simulation loop
        step_times = []
        accumulated_kl = 0.0
        trajectory = []
        
        for step in range(num_steps):
            # Set seed for this step to ensure reproducibility
            np.random.seed(seed + step)
            
            start_time = time.perf_counter()
            
            # Generate a synthetic matrix for this step
            # Using a simplified generation for the pilot to avoid heavy dependencies
            # In a full run, this would come from the data generation pipeline
            matrix = np.random.rand(128, 128)
            matrix = matrix / (np.sum(matrix, axis=1, keepdims=True) + 1e-9)
            
            # Run one step of the simulation
            try:
                scaling_factor, new_state = solver.solve_step(matrix, current_state)
                
                # Extract KL divergence from the new state
                # The state should have accumulated the KL divergence
                step_kl = new_state.accumulated_kl - current_state.accumulated_kl
                
                # Store trajectory
                trajectory.append(float(step_kl))
                accumulated_kl = new_state.accumulated_kl
                
                # Update state
                current_state = new_state
                
            except Exception as e:
                logger.warning(f"Step {step} failed with epsilon {eps}: {e}")
                trajectory.append(np.nan)
                continue
            
            end_time = time.perf_counter()
            step_times.append((end_time - start_time) * 1000)  # ms
        
        # Calculate metrics
        valid_trajectory = [x for x in trajectory if not np.isnan(x)]
        
        if len(valid_trajectory) == 0:
            logger.error(f"No valid trajectory for epsilon {eps}")
            error_rate = np.nan
            variation_rate = np.nan
        else:
            # Primary metric: accumulated KL divergence error rate
            # Defined as the total accumulated KL divided by the number of steps
            error_rate = accumulated_kl / num_steps
            
            # Secondary metric: variation rate (standard deviation of per-step errors)
            variation_rate = float(np.std(valid_trajectory))
        
        results.append({
            "epsilon": float(eps),
            "accumulated_kl_divergence_error_rate": float(error_rate),
            "variation_rate": float(variation_rate),
            "num_steps_run": len(valid_trajectory),
            "total_accumulated_kl": float(accumulated_kl),
            "avg_step_time_ms": float(np.mean(step_times)) if step_times else 0.0
        })
        
        logger.info(f"Completed epsilon {eps}: error_rate={error_rate:.6f}, variation={variation_rate:.6f}")
    
    output = {
        "pilot_config": {
            "num_steps": num_steps,
            "num_matrices": num_matrices,
            "seed": seed,
            "epsilon_values_tested": epsilon_values
        },
        "results": results,
        "summary": {
            "best_epsilon": None,
            "min_error_rate": float('inf')
        }
    }
    
    # Find best epsilon based on minimum error rate
    valid_results = [r for r in results if not np.isnan(r["accumulated_kl_divergence_error_rate"])]
    if valid_results:
        best = min(valid_results, key=lambda x: x["accumulated_kl_divergence_error_rate"])
        output["summary"]["best_epsilon"] = best["epsilon"]
        output["summary"]["min_error_rate"] = best["accumulated_kl_divergence_error_rate"]
    
    return output

def compute_theoretical_lower_bound(
    quantization_bits: int = 8,
    simulation_horizon: int = 1000
) -> Dict[str, Any]:
    """
    Compute the theoretical lower bound for accumulated KL-divergence.
    
    Formula: Δ^2 / 12, where Δ is the quantization interval.
    For 8-bit quantization over [0, 1], Δ = 1 / (2^8 - 1).
    
    Args:
        quantization_bits: Number of bits used for quantization.
        simulation_horizon: Number of steps in the simulation.
        
    Returns:
        Dictionary containing the lower bound and derivation details.
    """
    # Calculate quantization interval Δ
    delta = 1.0 / (2**quantization_bits - 1)
    
    # Theoretical lower bound per step
    lower_bound_per_step = (delta ** 2) / 12.0
    
    # Accumulated lower bound over the horizon
    accumulated_bound = lower_bound_per_step * simulation_horizon
    
    return {
        "quantization_bits": quantization_bits,
        "quantization_interval_delta": float(delta),
        "lower_bound_per_step": float(lower_bound_per_step),
        "simulation_horizon": simulation_horizon,
        "accumulated_lower_bound": float(accumulated_bound),
        "derivation": "Theoretical lower bound derived from uniform quantization noise model: Δ^2/12 per step, accumulated over simulation_horizon steps."
    }

def perform_paired_t_test(
    static_results: List[float],
    kvarn_results: List[float]
) -> Dict[str, Any]:
    """
    Perform a paired t-test on the final accumulated KL-divergence values.
    
    Args:
        static_results: List of accumulated KL values from static prior runs.
        kvarn_results: List of accumulated KL values from KVarN runs.
        
    Returns:
        Dictionary containing t-statistic, p-value, and test details.
    """
    if len(static_results) != len(kvarn_results):
        raise ValueError("Static and KVarN results must have the same length for paired t-test.")
    
    if len(static_results) < 2:
        raise ValueError("Need at least 2 samples for t-test.")
    
    # Convert to numpy arrays
    static_arr = np.array(static_results)
    kvarn_arr = np.array(kvarn_results)
    
    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(static_arr, kvarn_arr)
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = static_arr - kvarn_arr
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "mean_static": float(np.mean(static_arr)),
        "mean_kvarn": float(np.mean(kvarn_arr)),
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "cohens_d": float(cohens_d),
        "sample_size": len(static_arr),
        "test_type": "paired_t_test",
        "significance_threshold": 0.05,
        "is_significant": bool(p_value < 0.05)
    }

def main():
    """
    Main entry point for the pilot sensitivity analysis.
    Reads configuration, runs the analysis, and saves results.
    """
    from config import get_config
    
    config = get_config()
    
    # Get epsilon sweep values from config or generate default
    epsilon_values = config.get('EPSILON_SWEEP_VALUES', generate_epsilon_sweep_values())
    
    # Pilot configuration
    num_steps = config.get('PILOT_NUM_STEPS', 100)
    num_matrices = config.get('PILOT_NUM_MATRICES', 10)
    seed = config.get('RANDOM_SEED', 42)
    
    logger.info(f"Running pilot sensitivity analysis with config: {config}")
    
    # Run the analysis
    results = run_epsilon_sensitivity_analysis(
        epsilon_values=epsilon_values,
        num_steps=num_steps,
        num_matrices=num_matrices,
        seed=seed
    )
    
    # Save results
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "epsilon_pilot_full.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pilot sensitivity analysis complete. Results saved to {output_path}")
    print(f"Results written to: {output_path}")
    
    # Print summary
    print("\n=== Pilot Sensitivity Analysis Summary ===")
    print(f"Best epsilon: {results['summary']['best_epsilon']}")
    print(f"Min error rate: {results['summary']['min_error_rate']:.6f}")
    print(f"Number of epsilon values tested: {len(results['results'])}")
    
    return results

if __name__ == "__main__":
    main()
