import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from agents.baseline_estimator import create_baseline_estimator
from training.dopd_distillation import train_dopd
from training.uniform_distillation import train_uniform
from utils.logging import TrainingLogger
from utils.seed_manager import get_seed_range_for_purpose

def run_single_seed(seed: int, regime: str, steps: int, log_dir: str) -> Dict[str, Any]:
    """
    Run a single experiment seed for a specific regime.
    
    Args:
        seed: The random seed for this run.
        regime: Either 'dopd' or 'uniform'.
        steps: Number of training steps.
        log_dir: Directory to write logs.
        
    Returns:
        Dictionary with results summary.
    """
    # Initialize environment
    env = PrivilegeMDP(grid_size=5, seed=seed)
    
    # Initialize agents
    teacher = TeacherOracle(env)
    student = TabularQStudent(env, seed=seed)
    
    # Initialize baseline estimator
    baseline_estimator = create_baseline_estimator(env, seed=seed)
    
    # Initialize logger
    logger = TrainingLogger(log_dir=log_dir, regime=regime, seed=seed)
    
    # Run training
    if regime == 'dopd':
        results = train_dopd(
            env=env,
            teacher=teacher,
            student=student,
            baseline_estimator=baseline_estimator,
            steps=steps,
            logger=logger
        )
    elif regime == 'uniform':
        results = train_uniform(
            env=env,
            teacher=teacher,
            student=student,
            steps=steps,
            logger=logger
        )
    else:
        raise ValueError(f"Unknown regime: {regime}")
    
    # Log final metrics
    logger.log_metrics({
        'final_accuracy': results.get('final_accuracy', 0.0),
        'convergence_steps': results.get('convergence_steps', steps),
        'regime': regime,
        'seed': seed
    })
    
    return {
        'seed': seed,
        'regime': regime,
        'final_accuracy': results.get('final_accuracy', 0.0),
        'convergence_steps': results.get('convergence_steps', steps),
        'success': True
    }

def main():
    parser = argparse.ArgumentParser(description='Run DOPD vs Uniform experiments')
    parser.add_argument('--seeds', type=int, nargs='+', default=None,
                      help='List of seeds to run. If not provided, uses seed ranges.')
    parser.add_argument('--regimes', type=str, nargs='+', default=['dopd', 'uniform'],
                      help='Regimes to run (dopd, uniform)')
    parser.add_argument('--steps', type=int, default=1000,
                      help='Number of training steps per seed')
    parser.add_argument('--log-dir', type=str, default='data/raw',
                      help='Directory to write logs')
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    os.makedirs(args.log_dir, exist_ok=True)
    
    # Generate seeds if not provided
    if args.seeds is None:
        train_seeds = get_seed_range_for_purpose('train')
        args.seeds = train_seeds[:50]  # Use first 50 for this run
    
    print(f"Running {len(args.seeds)} seeds for regimes: {args.regimes}")
    print(f"Steps per seed: {args.steps}")
    
    all_results = []
    
    for regime in args.regimes:
        print(f"\n--- Running {regime.upper()} regime ---")
        for seed in args.seeds:
            try:
                result = run_single_seed(
                    seed=seed,
                    regime=regime,
                    steps=args.steps,
                    log_dir=args.log_dir
                )
                all_results.append(result)
                print(f"  Seed {seed}: accuracy={result['final_accuracy']:.4f}")
            except Exception as e:
                print(f"  Seed {seed}: FAILED - {str(e)}")
                all_results.append({
                    'seed': seed,
                    'regime': regime,
                    'final_accuracy': 0.0,
                    'convergence_steps': 0,
                    'success': False,
                    'error': str(e)
                })
    
    # Write summary results
    summary_path = os.path.join(args.log_dir, 'experiment_summary.json')
    with open(summary_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'seeds_used': args.seeds,
            'regimes': args.regimes,
            'steps': args.steps,
            'results': all_results
        }, f, indent=2)
    
    print(f"\nExperiment complete. Summary written to {summary_path}")
    print(f"Total successful runs: {sum(1 for r in all_results if r.get('success', False))}")
    
    return all_results

if __name__ == '__main__':
    main()