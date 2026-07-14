"""
Simulation Runner Script.

Orchestrates the full batch of simulations across sample sizes,
distributions, and test types, saving intermediate results.
"""
import os
import sys
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Import from sibling modules
from config import get_simulation_grid, SimulationConfig
from data_generator import generate_data
from simulation_engine import run_adaptive_simulation

logger = logging.getLogger(__name__)

def run_full_batch(
    output_dir: str = "data/processed",
    save_raw_pvalues: bool = True
) -> List[Dict[str, Any]]:
    """
    Execute the full simulation grid.
    
    Args:
        output_dir: Directory to save results.
        save_raw_pvalues: Whether to save raw p-values for regression analysis.
        
    Returns:
        List of result dictionaries.
    """
    grid = get_simulation_grid()
    results = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    if save_raw_pvalues:
        pval_path = os.path.join(output_dir, "raw_pvalues.csv")
        # Write header
        with open(pval_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "sample_size", "distribution", "test_type", 
                "effect_size", "replicate_id", "p_value"
            ])
    
    logger.info(f"Starting simulation batch. Total scenarios: {len(grid)}")
    
    for i, scenario in enumerate(grid):
        logger.info(f"Scenario {i+1}/{len(grid)}: n={scenario['sample_size']}, "
                    f"dist={scenario['distribution']}, test={scenario['test_type']}, "
                    f"effect={scenario['effect_size']}")
                    
        # Generate data
        s1, s2 = generate_data(
            n=scenario['sample_size'],
            distribution=scenario['distribution'],
            effect_size=scenario['effect_size'],
            seed=scenario['seed']
        )
        
        # Run simulation
        sim_result = run_adaptive_simulation(
            sample1=s1,
            sample2=s2,
            test_type=scenario['test_type'],
            alpha=scenario['alpha'],
            min_reps=scenario['n_replicates']
        )
        
        # Store aggregated result
        result_record = {
            "sample_size": scenario['sample_size'],
            "distribution": scenario['distribution'],
            "test_type": scenario['test_type'],
            "effect_size": scenario['effect_size'],
            "error_rate": sim_result['error_rate'],
            "ci_lower": sim_result['ci_lower'],
            "ci_upper": sim_result['ci_upper'],
            "n_reps": sim_result['n_reps']
        }
        results.append(result_record)
        
        # Save raw p-values if requested
        if save_raw_pvalues:
            with open(pval_path, 'a', newline='') as f:
                writer = csv.writer(f)
                for idx, p_val in enumerate(sim_result['p_values']):
                    writer.writerow([
                        scenario['sample_size'],
                        scenario['distribution'],
                        scenario['test_type'],
                        scenario['effect_size'],
                        idx,
                        p_val
                    ])
                    
    return results

def save_intermediate_results(results: List[Dict[str, Any]], filepath: str):
    """Save current results to a CSV file."""
    if not results:
        return
        
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
def main():
    """Entry point for the simulation runner."""
    logging.basicConfig(level=logging.INFO)
    
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    results = run_full_batch(output_dir=output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = os.path.join(output_dir, f"simulation_results_{timestamp}.csv")
    save_intermediate_results(results, final_path)
    
    logger.info(f"Simulation complete. Results saved to {final_path}")

if __name__ == "__main__":
    main()
