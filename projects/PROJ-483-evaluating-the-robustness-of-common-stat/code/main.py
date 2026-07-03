"""
Main entry point for the simulation pipeline.
Implements the sensitivity analysis sweep for User Story 1 (T013).
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from data_loader import load_datasets
from metrics import calculate_type1_error, clopper_pearson_ci
from simulation_runner import run_simulation

def main():
    """Run the sensitivity analysis sweep."""
    print("Starting sensitivity analysis sweep (T013)...")
    
    # Load configuration
    config = load_config()
    print(f"Configuration loaded with seed: {config['random_seed']}")
    
    # Load datasets
    datasets = load_datasets(config['datasets']['manifest_path'])
    print(f"Loaded {len(datasets)} datasets")
    
    if not datasets:
        print("Error: No datasets loaded. Cannot proceed with simulation.")
        return 1
    
    # Define the sweep parameters
    # Sweep r (dependency strength) across a range including zero and positive increments
    r_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    alpha_levels = [0.05]  # Standard significance level
    
    # Ensure results directory exists
    os.makedirs('results', exist_ok=True)
    
    # Log start
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'seed': config['random_seed'],
        'datasets_loaded': len(datasets),
        'r_values': r_values,
        'status': 'started'
    }
    
    with open('results/perf_log.json', 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    # Run simulation for each r value
    all_results = []
    
    for r in r_values:
        print(f"Running simulation for dependency strength r={r}...")
        
        # Run simulation
        # Note: run_simulation is expected to return a list of p-values or a DataFrame
        # based on the configuration and the current r value
        raw_p_values = run_simulation(
            datasets=datasets,
            r=r,
            test_type='t-test', # Focus on t-test for US1 as per task description
            alpha=alpha_levels[0],
            config=config
        )
        
        print(f"  Generated {len(raw_p_values)} p-values for r={r}")
        
        # Aggregate results using functions defined in T007 (metrics.py)
        # Calculate Type 1 error rate
        type1_error = calculate_type1_error(raw_p_values, alpha=alpha_levels[0])
        
        # Calculate Clopper-Pearson CI
        ci_lower, ci_upper = clopper_pearson_ci(raw_p_values, alpha=alpha_levels[0])
        
        result_row = {
            'dependency_strength': r,
            'test_type': 't-test',
            'alpha': alpha_levels[0],
            'n_replications': len(raw_p_values),
            'observed_error_rate': type1_error,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }
        
        all_results.append(result_row)
        print(f"  Observed Error Rate: {type1_error:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])")
    
    # Save aggregated results to CSV
    output_path = 'results/aggregated.csv'
    print(f"Saving aggregated results to {output_path}...")
    
    import pandas as pd
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(output_path, index=False)
    
    # Update log
    log_entry['status'] = 'completed'
    log_entry['output_file'] = output_path
    with open('results/perf_log.json', 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    print("Sensitivity analysis sweep complete.")
    return 0

if __name__ == "__main__":
    exit(main())
