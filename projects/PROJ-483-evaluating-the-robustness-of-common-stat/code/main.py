"""
Main entry point for the simulation pipeline.
Implements the sensitivity analysis sweep for User Story 1 (T013)
and aggregation logic for User Story 2 (T021).
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
from metrics import calculate_type1_error, calculate_chi_squared_error_rate, clopper_pearson_ci, verify_trend_monotonicity
from simulation_runner import run_simulation

def main():
    """Run the sensitivity analysis sweep and aggregate results by test type and dependency structure."""
    print("Starting sensitivity analysis sweep and aggregation (T013, T021)...")
    
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
    
    # Define test types and dependency structures for US2 aggregation
    # US1: t-test with AR(1)
    # US2: t-test with Block Bootstrap, Chi-squared with Block Bootstrap
    test_configs = [
        {'test_type': 't-test', 'dependency_structure': 'ar1'},
        {'test_type': 't-test', 'dependency_structure': 'block_bootstrap'},
        {'test_type': 'chi_squared', 'dependency_structure': 'block_bootstrap'}
    ]
    
    # Ensure results directory exists
    os.makedirs('results', exist_ok=True)
    
    # Log start
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'seed': config['random_seed'],
        'datasets_loaded': len(datasets),
        'r_values': r_values,
        'test_configs': test_configs,
        'status': 'started'
    }
    
    perf_log_path = 'results/perf_log.json'
    with open(perf_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    # Run simulation for each r value and test config
    all_results = []
    
    for test_type, dep_structure in [(c['test_type'], c['dependency_structure']) for c in test_configs]:
        print(f"\nRunning simulation for test_type={test_type}, dependency_structure={dep_structure}...")
        
        for r in r_values:
            print(f"  Running simulation for r={r}...")
            
            # Run simulation
            # run_simulation is expected to return a list of p-values or a DataFrame
            raw_p_values = run_simulation(
                datasets=datasets,
                r=r,
                test_type=test_type,
                dependency_structure=dep_structure,
                alpha=alpha_levels[0],
                config=config
            )
            
            print(f"    Generated {len(raw_p_values)} p-values")
            
            # Aggregate results using functions defined in metrics.py
            if test_type == 'chi_squared':
                error_rate = calculate_chi_squared_error_rate(raw_p_values, alpha=alpha_levels[0])
            else:
                error_rate = calculate_type1_error(raw_p_values, alpha=alpha_levels[0])
            
            # Calculate Clopper-Pearson CI
            ci_lower, ci_upper = clopper_pearson_ci(raw_p_values, alpha=alpha_levels[0])
            
            result_row = {
                'dependency_strength': r,
                'test_type': test_type,
                'dependency_structure': dep_structure,
                'alpha': alpha_levels[0],
                'n_replications': len(raw_p_values),
                'observed_error_rate': error_rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            }
            
            all_results.append(result_row)
            print(f"    Observed Error Rate: {error_rate:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])")
    
    # Save aggregated results to CSV
    output_path = 'results/aggregated.csv'
    print(f"\nSaving aggregated results to {output_path}...")
    
    import pandas as pd
    df_results = pd.DataFrame(all_results)
    
    # Group results by test type and dependency structure as per T021
    # This ensures the data is organized for comparative analysis
    df_results = df_results.sort_values(by=['test_type', 'dependency_structure', 'dependency_strength'])
    df_results.to_csv(output_path, index=False)
    
    # Verify trend monotonicity for each test_type/dependency_structure group
    print("Verifying trend monotonicity...")
    trend_results = verify_trend_monotonicity(df_results)
    
    # Add trend_status to the aggregated dataframe if available
    if not trend_results.empty:
        df_results = df_results.merge(trend_results, on=['test_type', 'dependency_structure'], how='left')
        df_results.to_csv(output_path, index=False)
        print(f"Trend verification results saved to {output_path}")
    
    # Update log
    log_entry['status'] = 'completed'
    log_entry['output_file'] = output_path
    with open(perf_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    print("Sensitivity analysis sweep and aggregation complete.")
    return 0

if __name__ == "__main__":
    exit(main())