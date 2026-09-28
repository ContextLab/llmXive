import argparse
import os
import sys
import pandas as pd
from analysis.schema_validator import validate_schema
from analysis.metrics import run_statistical_test, save_statistical_test_results
from analysis.aggregation import load_run_results, aggregate_results, save_summary_dataframe
from simulation.verify_us1 import run_verification_and_save, main as verify_main
from simulation.config import get_simulation_grid
from simulation.scm_generator import generate_scm, regenerate_ground_truth
from simulation.missingness import inject_mnar, tune_alpha
from analysis.pipeline import run_imputation_and_estimation
import numpy as np
import json
import hashlib

def run_full_analysis(args):
    """
    Orchestrates the full analysis pipeline:
    1. Validates schema if requested.
    2. Runs simulation if requested (generating data, imputation, estimation).
    3. Aggregates results into simulation_summary.csv.
    4. Runs statistical tests.
    5. Runs US1 verification.
    """
    # 1. Validate Schema
    if hasattr(args, 'validate_schema') and args.validate_schema:
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        
        expected_columns = {
            'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 
            'coverage_rate', 'seed', 'run_id', 'ground_truth_ate', 
            'beta_value', 'status'
        }
        
        df = pd.read_csv(args.input)
        actual_columns = set(df.columns)
        
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns
        
        if missing:
            print(f"Schema validation FAILED. Missing columns: {missing}", file=sys.stderr)
            sys.exit(1)
        
        if extra:
            print(f"Warning: Extra columns found (ignored): {extra}", file=sys.stderr)
        
        print("Schema validation PASSED.")

    # 2. Run Simulation if requested
    if hasattr(args, 'runs') and args.runs:
        print(f"Starting simulation with {args.runs} runs across beta sweep: {args.beta_sweep}")
        
        betas = [float(b) for b in args.beta_sweep.split(',')]
        n_runs = args.runs
        
        all_results = []
        
        # Ensure output directory exists
        os.makedirs('data/results', exist_ok=True)
        
        for run_idx in range(n_runs):
            # Determine beta for this run (round-robin or random assignment)
            # For reproducibility, we'll cycle through betas
            beta = betas[run_idx % len(betas)]
            seed = run_idx + 42  # Base seed + offset
            
            try:
                # Generate SCM
                dataset = generate_scm(seed=seed, n=1000, tau_true=0.5)
                
                # Tune alpha for target rate (e.g., 0.3)
                target_rate = 0.3
                alpha = tune_alpha(beta=beta, target_rate=target_rate)
                
                # Inject MNAR
                incomplete_data = inject_mnar(dataset, beta=beta, target_rate=target_rate)
                
                # Run Imputation and Estimation
                results = run_imputation_and_estimation(incomplete_data, seed=seed, beta=beta)
                
                # Process results
                for res in results:
                    res_dict = {
                        'beta': beta,
                        'method': res['method'],
                        'estimator': res['estimator'],
                        'ate': res['ate'],
                        'bias': res['bias'],
                        'rmse': res['rmse'],
                        'coverage_rate': res['coverage_rate'],
                        'seed': seed,
                        'run_id': hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest(),
                        'ground_truth_ate': 0.5,
                        'beta_value': beta,
                        'status': res['status']
                    }
                    all_results.append(res_dict)
                    
                # Run US1 verification for this run
                run_verification_and_save(seed, beta, incomplete_data)
                
            except Exception as e:
                print(f"Error in run {run_idx} (seed={seed}, beta={beta}): {e}", file=sys.stderr)
                # Log error but continue
                continue
        
        # Aggregate and save
        if all_results:
            df_summary = pd.DataFrame(all_results)
            save_summary_dataframe(df_summary, 'data/results/simulation_summary.csv')
            print(f"Saved simulation summary to data/results/simulation_summary.csv with {len(all_results)} rows.")
        else:
            print("No results generated.", file=sys.stderr)
            sys.exit(1)

    # 3. Verify Sensitivity / Run Statistical Tests
    if hasattr(args, 'verify_sensitivity') and args.verify_sensitivity:
        summary_path = args.input.replace('sensitivity_analysis.json', 'simulation_summary.csv')
        if not os.path.exists(summary_path):
            print(f"Error: Required summary file not found: {summary_path}", file=sys.stderr)
            sys.exit(1)
        
        df = pd.read_csv(summary_path)
        results = run_statistical_test(df)
        save_statistical_test_results(results)
        print("Statistical tests completed and saved to data/results/statistical_test_results.json")

    # 4. Run US1 Verification (if explicitly requested or as part of full run)
    if hasattr(args, 'verify_us1') and args.verify_us1:
        # This would run verification on existing data if needed
        print("US1 Verification requested. Ensure data/results/us1_verification.json is populated.")
        # The run_simulation loop above already calls run_verification_and_save
        
    print("Analysis pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description='Analysis pipeline commands')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Validate Schema Command
    validate_parser = subparsers.add_parser('validate-schema', help='Validate simulation summary schema')
    validate_parser.add_argument('--input', type=str, required=True, help='Path to simulation_summary.csv')
    validate_parser.set_defaults(validate_schema=True)

    # Verify Sensitivity Command
    verify_parser = subparsers.add_parser('verify-sensitivity', help='Run statistical tests on sensitivity data')
    verify_parser.add_argument('--input', type=str, required=True, help='Path to sensitivity analysis JSON')
    verify_parser.set_defaults(verify_sensitivity=True)
    
    # Run Simulation Command (New, to replace missing run_simulation.py functionality)
    run_parser = subparsers.add_parser('run-simulation', help='Run the full simulation pipeline')
    run_parser.add_argument('--runs', type=int, default=10, help='Number of simulation runs')
    run_parser.add_argument('--beta-sweep', type=str, default='0.0,0.2,0.5,0.8,1.0', help='Comma-separated beta values')
    run_parser.add_argument('--verify-us1', action='store_true', help='Run US1 verification')
    run_parser.set_defaults(runs=10, beta_sweep='0.0,0.2,0.5,0.8,1.0')

    args = parser.parse_args()

    if args.command == 'validate-schema':
        run_full_analysis(args)
    elif args.command == 'verify-sensitivity':
        run_full_analysis(args)
    elif args.command == 'run-simulation':
        run_full_analysis(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()