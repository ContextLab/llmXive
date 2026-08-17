import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_epsilon_sweep_values, Config
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver
from data_generation.synthetic_attention import generate_static_attention_matrix, compute_scaling_factor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pilot_analysis(output_path: str, num_matrices: int = 100) -> dict:
    """
    Runs a pilot sensitivity analysis to validate epsilon configuration.
    
    Args:
        output_path: Path to write the JSON results.
        num_matrices: Number of synthetic matrices to generate for the pilot.
        
    Returns:
        Dictionary containing pilot analysis results.
    """
    logger.info(f"Starting pilot sensitivity analysis with {num_matrices} matrices.")
    
    # Get epsilon sweep values from config
    epsilon_values = get_epsilon_sweep_values()
    logger.info(f"Epsilon sweep values: {epsilon_values}")
    
    results = {
        "num_matrices": num_matrices,
        "epsilon_values": epsilon_values,
        "results_by_epsilon": {},
        "validation_status": "unknown"
    }
    
    solver = SingleStepSinkhornSolver()
    
    for eps in epsilon_values:
        logger.info(f"Processing epsilon: {eps}")
        
        kl_deltas = []
        scaling_factors = []
        convergence_failures = 0
        
        for i in range(num_matrices):
            # Generate a synthetic attention matrix
            matrix = generate_static_attention_matrix(seed=i + int(eps * 1e9))
            
            # Compute ground truth scaling factor using the solver
            try:
                sf = solver.solve(matrix, eps)
                if np.isnan(sf) or np.isinf(sf):
                    convergence_failures += 1
                    continue
                scaling_factors.append(sf)
                
                # Compute a simple KL divergence proxy for this step
                # Using a simplified model: KL ~ (1 - scale)^2 for pilot validation
                # In a full run, this would be the actual KL between quantized and full precision
                kl_proxy = (1.0 - sf) ** 2
                kl_deltas.append(kl_proxy)
                
            except Exception as e:
                logger.warning(f"Solver failed for matrix {i} with epsilon {eps}: {e}")
                convergence_failures += 1
                continue
        
        # Calculate metrics for this epsilon
        if len(kl_deltas) > 0:
            avg_kl_delta = float(np.mean(kl_deltas))
            std_kl_delta = float(np.std(kl_deltas))
            min_kl_delta = float(np.min(kl_deltas))
            max_kl_delta = float(np.max(kl_deltas))
            avg_sf = float(np.mean(scaling_factors))
            
            # Check monotonicity or bounds
            # For this pilot, we expect KL delta to generally decrease as epsilon increases
            # (assuming epsilon acts as a regularization term)
            # We flag if the trend is completely inverted or if variance is too high
            is_monotonic = True
            if len(kl_deltas) > 1:
                # Simple check: is the trend generally downward?
                # We allow some noise, so we check if the last 10% is lower than first 10%
                first_part = np.mean(kl_deltas[:max(1, len(kl_deltas)//10)])
                last_part = np.mean(kl_deltas[-max(1, len(kl_deltas)//10):])
                if last_part > first_part * 1.5: # Allow some tolerance
                    is_monotonic = False
            
            results["results_by_epsilon"][str(eps)] = {
                "avg_kl_delta_per_step": avg_kl_delta,
                "std_kl_delta_per_step": std_kl_delta,
                "min_kl_delta_per_step": min_kl_delta,
                "max_kl_delta_per_step": max_kl_delta,
                "avg_scaling_factor": avg_sf,
                "num_convergence_failures": convergence_failures,
                "is_monotonic_or_within_bounds": is_monotonic,
                "sample_size": len(kl_deltas)
            }
            
            logger.info(f"Epsilon {eps}: Avg KL Delta={avg_kl_delta:.6f}, "
                        f"Failures={convergence_failures}, Monotonic={is_monotonic}")
        else:
            logger.warning(f"No valid results for epsilon {eps}")
            results["results_by_epsilon"][str(eps)] = {
                "error": "No valid results",
                "num_convergence_failures": convergence_failures
            }
    
    # Determine overall validation status
    # If any epsilon has high failure rate or non-monotonic behavior, flag for review
    needs_review = False
    for eps_str, data in results["results_by_epsilon"].items():
        if "error" in data:
            needs_review = True
            break
        if data.get("num_convergence_failures", 0) > num_matrices * 0.1: # >10% failure
            needs_review = True
        if not data.get("is_monotonic_or_within_bounds", True):
            needs_review = True
    
    results["validation_status"] = "flag_for_review" if needs_review else "passed"
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pilot analysis complete. Results written to {output_path}")
    logger.info(f"Validation status: {results['validation_status']}")
    
    return results

def main():
    """Main entry point for the pilot sensitivity analysis script."""
    # Default output path
    output_path = "data/analysis/epsilon_pilot.json"
    num_matrices = 100 # Pilot size
    
    # Parse arguments if provided
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    if len(sys.argv) > 2:
        num_matrices = int(sys.argv[2])
    
    run_pilot_analysis(output_path, num_matrices)

if __name__ == "__main__":
    main()
