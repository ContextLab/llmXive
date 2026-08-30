import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from config import load_config
from simulation_runner import run_simulation
from metrics import calculate_type1_error, clopper_pearson_ci, verify_trend_monotonicity
from data_loader import load_manifest

def main():
    """
    T013 Implementation: Sensitivity Analysis Sweep.
    
    Executes a Monte Carlo sweep over dependency strength 'r' (AR(1) correlation).
    1. Loads configuration and dataset manifest.
    2. Iterates through a range of 'r' values [0.0, 0.1, ..., 0.9].
    3. For each 'r', runs the simulation (t-test under null with injected dependency).
    4. Aggregates results: calculates Type I Error rate and Clopper-Pearson CI.
    5. Verifies trend monotonicity.
    6. Saves aggregated results to results/aggregated.csv.
    """
    print(f"[T013] Starting Sensitivity Analysis Sweep at {datetime.now()}")
    
    # 1. Load Configuration
    config = load_config()
    if not config:
        raise RuntimeError("Failed to load configuration. Ensure code/config.yaml exists.")
    
    seed = config.get('simulation', {}).get('seed', 42)
    np.random.seed(seed)
    
    # Define sweep parameters based on task requirements
    # Sweep r across [0, 0.1, ..., 0.9]
    r_values = [float(x) / 10.0 for x in range(0, 10)]
    alpha = config.get('simulation', {}).get('alpha', 0.05)
    n_replications = config.get('simulation', {}).get('n_replications', 1000)
    
    # Ensure output directory exists
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    print(f"[T013] Configuration loaded. Seed: {seed}, Alpha: {alpha}, Replications: {n_replications}")
    print(f"[T013] Sweeping r values: {r_values}")
    
    aggregated_results = []
    
    # 2. Loop over dependency strength 'r'
    for r in r_values:
        print(f"[T013] Running simulation for r={r:.1f}...")
        
        # Run the simulation for this specific 'r'
        # run_simulation returns a DataFrame of p-values and metadata
        try:
            simulation_data = run_simulation(
                dependency_type="ar1",
                dependency_strength=r,
                n_replications=n_replications,
                config=config
            )
        except Exception as e:
            print(f"[T013] ERROR running simulation for r={r}: {e}")
            # Log failure but continue to other r values if possible, 
            # or fail loudly if critical data is missing.
            # For this task, we record a failure row.
            aggregated_results.append({
                "dependency_type": "ar1",
                "dependency_strength": r,
                "test_type": "t-test",
                "n_replications": 0,
                "observed_error_rate": np.nan,
                "ci_lower": np.nan,
                "ci_upper": np.nan,
                "status": "failed"
            })
            continue

        if simulation_data is None or simulation_data.empty:
            print(f"[T013] WARNING: No data returned for r={r}")
            continue

        # 3. Aggregate Results using functions from metrics.py (T007)
        # Calculate Type I Error Rate (proportion of p < alpha)
        error_rate = calculate_type1_error(simulation_data['p_value'].values, alpha)
        
        # Calculate Clopper-Pearson Confidence Interval
        n_successes = int((simulation_data['p_value'] < alpha).sum())
        ci_lower, ci_upper = clopper_pearson_ci(n_successes, n_replications, alpha)
        
        result_row = {
            "dependency_type": "ar1",
            "dependency_strength": r,
            "test_type": "t-test",
            "n_replications": n_replications,
            "n_successes": n_successes,
            "observed_error_rate": error_rate,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "status": "completed"
        }
        
        # Add raw stats for debugging/verification
        result_row["mean_p_value"] = simulation_data['p_value'].mean()
        result_row["std_p_value"] = simulation_data['p_value'].std()
        
        aggregated_results.append(result_row)
        print(f"[T013] r={r:.1f}: Error Rate = {error_rate:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])")

    # 4. Create DataFrame and Save
    if not aggregated_results:
        raise RuntimeError("No simulation results generated. Check simulation_runner.py.")
        
    df_results = pd.DataFrame(aggregated_results)
    
    # Sort by dependency strength for clean CSV output
    df_results = df_results.sort_values(by="dependency_strength")
    
    output_path = results_dir / "aggregated.csv"
    df_results.to_csv(output_path, index=False)
    print(f"[T013] Aggregated results saved to {output_path}")
    
    # 5. Verify Trend Monotonicity (T014 requirement, done here for completeness of sweep)
    # Filter for completed runs only
    df_valid = df_results[df_results['status'] == 'completed'].copy()
    if len(df_valid) > 1:
        is_monotonic, trend_p_value = verify_trend_monotonicity(
            df_valid['dependency_strength'].values, 
            df_valid['observed_error_rate'].values
        )
        print(f"[T013] Trend Monotonicity Check: Monotonic={is_monotonic}, p-value={trend_p_value:.4f}")
        
        # Append trend status to the dataframe if needed, or log separately.
        # The task asks to output trend_status to aggregated.csv if T014 runs here.
        # We will add a column indicating the overall trend status for the sweep.
        df_results['trend_monotonic'] = is_monotonic
        df_results['trend_p_value'] = trend_p_value
        
        # Re-save with trend info
        df_results.to_csv(output_path, index=False)
        print(f"[T013] Updated {output_path} with trend analysis.")
    else:
        print(f"[T013] Insufficient data for trend analysis.")

    print(f"[T013] Sensitivity Analysis Complete.")
    return df_results

if __name__ == "__main__":
    main()
