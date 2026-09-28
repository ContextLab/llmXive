import argparse
import os
import sys
import json
from typing import List, Dict, Any
import numpy as np
from simulation.config import get_simulation_grid, get_run_seed, get_experiment_rng
from simulation.scm_generator import generate_scm, regenerate_ground_truth
from simulation.missingness import tune_alpha, inject_mnar
from simulation.verify_us1 import run_verification_and_save
from analysis.pipeline import run_imputation_and_estimation
from analysis.aggregation import save_summary_dataframe, aggregate_results, load_run_results
import glob

def run_single_simulation(seed: int, beta: float, n: int = 1000) -> Dict[str, Any]:
    """Run a single simulation with given seed and beta."""
    try:
        # Regenerate ground truth for this seed and beta
        tau_true, beta_param = regenerate_ground_truth(seed, beta)
        
        # Generate SCM
        dataset = generate_scm(seed=seed, n=n, tau_true=tau_true)
        
        # Tune alpha for target missingness rate
        target_rate = 0.3  # 30% missingness
        alpha = tune_alpha(beta_param, target_rate)
        
        # Inject missingness
        incomplete_data = inject_mnar(dataset, beta_param, target_rate)
        
        # Run imputation and estimation pipeline
        results = run_imputation_and_estimation(incomplete_data)
        
        # Verify MNAR correlation
        # Extract complete Y and mask from the dataset
        complete_y = dataset.Y.values.flatten() if hasattr(dataset.Y, 'values') else np.array(dataset.Y).flatten()
        mask = incomplete_data['mask'].values.flatten() if 'mask' in incomplete_data.columns else None
        
        if mask is not None:
            run_verification_and_save(
                seed=seed,
                beta=beta,
                mask_data=mask,
                complete_y=complete_y,
                output_path='data/results/us1_verification.json'
            )
        
        return {
            'seed': seed,
            'beta': beta,
            'tau_true': tau_true,
            'ground_truth_ate': tau_true,
            'alpha': alpha,
            'results': results,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error in simulation (seed={seed}, beta={beta}): {e}", file=sys.stderr)
        return {
            'seed': seed,
            'beta': beta,
            'status': 'failed',
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='Run full simulation pipeline')
    parser.add_argument('--runs', type=int, default=200, help='Number of runs per beta level')
    parser.add_argument('--beta-sweep', type=str, default='0.0,0.2,0.5,0.8,1.0',
                      help='Comma-separated beta values')
    parser.add_argument('--output-dir', type=str, default='data/results',
                      help='Directory to store results')
    
    args = parser.parse_args()
    
    # Parse beta values
    beta_values = [float(x) for x in args.beta_sweep.split(',')]
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    all_results = []
    
    print(f"Starting simulation with {args.runs} runs per beta level...")
    print(f"Beta values: {beta_values}")
    
    for beta in beta_values:
        print(f"\nProcessing beta = {beta}")
        
        for i in range(args.runs):
            seed = get_run_seed(beta, i)
            result = run_single_simulation(seed, beta)
            all_results.append(result)
            
            # Save individual run result
            run_id = f"{seed}_{beta}".replace('.', '_')
            output_file = os.path.join(args.output_dir, f'run_{run_id}.json')
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            if (i + 1) % 50 == 0:
                print(f"  Completed {i + 1}/{args.runs} runs for beta={beta}")
    
    # Aggregate results
    print("\nAggregating results...")
    summary_df = aggregate_results(all_results)
    save_summary_dataframe(summary_df, os.path.join(args.output_dir, 'simulation_summary.csv'))
    
    print(f"\nSimulation complete. Results saved to {args.output_dir}")

if __name__ == '__main__':
    main()
