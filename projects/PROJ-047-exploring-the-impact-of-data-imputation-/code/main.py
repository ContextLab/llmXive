import argparse
import sys
import os
import json
import logging
import time
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

# Local imports
from simulation.config import get_run_seed, get_experiment_rng, get_simulation_grid
from simulation.scm_generator import generate_scm, regenerate_ground_truth, check_collinearity
from simulation.missingness import inject_mnar, tune_alpha
from simulation.verify_us1 import run_verification_and_save
from analysis.pipeline import run_imputation_and_estimation
from analysis.aggregation import aggregate_results, save_summary_dataframe, calculate_coverage_rate
from analysis.metrics import run_statistical_test, save_statistical_test_results
from analysis.power import generate_power_report
from analysis.oracle import run_oracle_benchmark, save_oracle_results
from analysis.validation import validate_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/run_errors.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run the full causal inference simulation pipeline.")
    parser.add_argument("--beta-sweep", type=str, default="0.0,0.2,0.5,0.8,1.0",
                        help="Comma-separated list of beta values to sweep.")
    parser.add_argument("--runs", type=int, default=200,
                        help="Number of replications per beta value.")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to a custom config file (optional).")
    parser.add_argument("--output", type=str, default="data/results",
                        help="Directory to store output results.")
    parser.add_argument("--parallel", type=bool, default=True,
                        help="Enable parallel execution for beta levels.")
    parser.add_argument("--n-jobs", type=int, default=2,
                        help="Number of parallel jobs for beta levels.")
    return parser.parse_args()

def compute_run_seed(seed: int, beta: float) -> int:
    """Generate a deterministic seed for a specific run based on base seed and beta."""
    h = hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest()
    return int(h, 16) % (2**32)

def run_single_beta_iteration(beta: float, runs: int, base_seed: int, output_dir: str) -> List[Dict[str, Any]]:
    """
    Execute all simulation runs for a single beta value.
    Returns a list of result dictionaries.
    """
    logger.info(f"Starting simulation for beta={beta} with {runs} runs.")
    results = []
    
    # Pre-calculate alpha for this beta to ensure consistent missingness rate
    try:
        alpha = tune_alpha(beta, target_rate=0.3)
        logger.info(f"Tuned alpha for beta={beta}: {alpha:.4f}")
    except Exception as e:
        logger.error(f"Failed to tune alpha for beta={beta}: {e}")
        return []

    for i in range(runs):
        run_seed = compute_run_seed(base_seed + i, beta)
        run_id = f"{base_seed + i}_{beta}"
        
        try:
            # 1. Generate SCM
            dataset = generate_scm(seed=run_seed, n=1000, tau_true=0.5)
            
            # 2. Inject MNAR
            # We need to inject missingness on Y based on the generated Y
            # The inject_mnar function expects a dataframe with Y
            df = pd.DataFrame({
                'X1': dataset.X[:, 0],
                'X2': dataset.X[:, 1],
                'T': dataset.T,
                'Y': dataset.Y
            })
            
            # Inject missingness
            mask, _ = inject_mnar(df, beta=beta, target_rate=0.3)
            df['Y_missing'] = mask # Store mask for verification
            
            # 3. Verify US1 (MNAR correlation)
            # We verify against the COMPLETE Y before masking
            # But inject_mnar already used the complete Y to generate the mask
            # We need to re-calculate correlation between mask and complete Y
            corr, p_val = run_verification_and_save(
                mask=mask, 
                y_complete=df['Y'], 
                run_id=run_id, 
                output_dir=output_dir
            )
            
            # 4. Check Collinearity
            vif = check_collinearity(df[['X1', 'X2']])
            
            # 5. Run Imputation and Estimation
            # Create incomplete dataset
            df_incomplete = df.copy()
            df_incomplete.loc[mask == 1, 'Y'] = np.nan
            
            # Run pipeline
            imputation_results = run_imputation_and_estimation(df_incomplete)
            
            # 6. Aggregate Results for this run
            # We need to calculate coverage rate against the ground truth
            # Ground truth is dataset.ground_truth_ate
            ground_truth_ate = dataset.ground_truth_ate
            
            # Re-generate ground truth to ensure integrity (Constitution VI)
            tau_true_check, beta_check = regenerate_ground_truth(run_seed, beta)
            assert abs(tau_true_check - ground_truth_ate) < 1e-6, "Ground truth mismatch"
            
            run_data = {
                'beta': beta,
                'seed': run_seed,
                'run_id': run_id,
                'ground_truth_ate': ground_truth_ate,
                'vif': vif,
                'mnar_correlation': corr,
                'mnar_p_value': p_val,
                'status': 'success'
            }
            
            # Add results from each imputation/estimation method
            for method, estimates in imputation_results.items():
                for estimator, est_obj in estimates.items():
                    run_data[f'{method}_{estimator}_ate'] = est_obj.ate
                    run_data[f'{method}_{estimator}_se'] = est_obj.se
                    run_data[f'{method}_{estimator}_ci_lower'] = est_obj.ci_lower
                    run_data[f'{method}_{estimator}_ci_upper'] = est_obj.ci_upper
                    
                    # Calculate bias
                    bias = est_obj.ate - ground_truth_ate
                    run_data[f'{method}_{estimator}_bias'] = bias
                    
                    # Check coverage
                    if est_obj.ci_lower <= ground_truth_ate <= est_obj.ci_upper:
                        run_data[f'{method}_{estimator}_covered'] = 1
                    else:
                        run_data[f'{method}_{estimator}_covered'] = 0
            
            results.append(run_data)
            
        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}", exc_info=True)
            results.append({
                'beta': beta,
                'seed': run_seed,
                'run_id': run_id,
                'status': 'failed',
                'error': str(e)
            })
    
    logger.info(f"Completed {len(results)} runs for beta={beta}")
    return results

def main():
    args = parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Parse beta sweep
    beta_values = [float(x) for x in args.beta_sweep.split(',')]
    base_seed = 42 # Fixed base seed for reproducibility
    
    all_results = []
    
    start_time = time.time()
    
    if args.parallel and len(beta_values) > 1:
        logger.info(f"Running {len(beta_values)} beta levels in parallel with n_jobs={args.n_jobs}")
        # Parallel execution over beta levels
        beta_results_list = Parallel(n_jobs=args.n_jobs)(
            delayed(run_single_beta_iteration)(beta, args.runs, base_seed, args.output)
            for beta in beta_values
        )
        for res in beta_results_list:
            all_results.extend(res)
    else:
        logger.info("Running beta levels sequentially")
        for beta in beta_values:
            res = run_single_beta_iteration(beta, args.runs, base_seed, args.output)
            all_results.extend(res)
    
    end_time = time.time()
    logger.info(f"Total simulation time: {end_time - start_time:.2f} seconds")
    
    if not all_results:
        logger.error("No results generated. Exiting.")
        sys.exit(1)
    
    # 1. Aggregate and Save Summary
    logger.info("Aggregating results...")
    df_summary = aggregate_results(all_results)
    save_summary_dataframe(df_summary, os.path.join(args.output, "simulation_summary.csv"))
    
    # 2. Validate Schema
    logger.info("Validating schema...")
    if not validate_schema(df_summary):
        logger.error("Schema validation failed. Exiting.")
        sys.exit(1)
    
    # 3. Run Statistical Tests
    logger.info("Running statistical tests...")
    test_results = run_statistical_test(df_summary)
    save_statistical_test_results(test_results, os.path.join(args.output, "statistical_test_results.json"))
    
    # 4. Run Power Analysis
    logger.info("Running power analysis...")
    power_report = generate_power_report(df_summary)
    with open(os.path.join(args.output, "power_analysis.json"), 'w') as f:
        json.dump(power_report, f, indent=2)
    
    # 5. Run Oracle Benchmark
    logger.info("Running Oracle Benchmark...")
    oracle_results = run_oracle_benchmark(df_summary)
    save_oracle_results(oracle_results, os.path.join(args.output, "oracle_benchmark.json"))
    
    # 6. Verify Bias Trend
    logger.info("Verifying bias trend...")
    from analysis.sensitivity import verify_bias_trend
    trend_results = verify_bias_trend(df_summary)
    with open(os.path.join(args.output, "bias_trend_verification.json"), 'w') as f:
        json.dump(trend_results, f, indent=2)
        
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
