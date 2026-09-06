import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add code root to path if needed, assuming this script is run from project root
# but the imports are relative to 'code/'
# The execution environment usually sets PYTHONPATH.
# We will assume standard imports work as per API surface.
from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from agents.random_policy import RandomPolicyAgent
from training.dopd_distillation import train_dopd, run_generalization_analysis
from training.uniform_distillation import train_uniform
from utils.logging import TrainingLogger
from utils.seeding import seed_everything

def parse_args():
    parser = argparse.ArgumentParser(description="DOPD Experiment Runner")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for single run")
    parser.add_argument('--seeds', type=int, default=50, help="Number of seeds for batch run")
    parser.add_argument('--regime', type=str, default='dopd', 
                        choices=['dopd', 'uniform', 'randomized_weight'], 
                        help="Training regime")
    parser.add_argument('--regimes', type=str, default=None,
                        help="Comma-separated list of regimes for batch run (e.g., uniform,dopd)")
    parser.add_argument('--steps', type=int, default=1000, help="Number of training steps")
    parser.add_argument('--grid-size', type=int, default=5, help="Grid size (NxN)")
    return parser.parse_args()

def run_single_regime_seed(args, regime: str, seed: int, steps: int):
    print(f"Running {regime} regime with seed {seed}, steps {steps}")
    seed_everything(seed)
    
    # Initialize Environment
    env = PrivilegeMDP(grid_size=args.grid_size, seed=seed)
    
    # Initialize Agents
    teacher = TeacherOracle(env)
    student = TabularQStudent(env)
    
    config = {
        'seed': seed,
        'steps': steps,
        'grid_size': args.grid_size,
        'learning_rate': 0.1,
        'discount_factor': 0.99,
        'batch_size': 50,
        'epsilon': 1e-8,
        'range_threshold': 0.1
    }
    
    result = {}
    
    if regime == 'dopd':
        result = train_dopd(env, student, teacher, config, seed, steps)
    elif regime == 'uniform':
        result = train_uniform(env, student, teacher, config, seed, steps)
    elif regime == 'randomized_weight':
        # Placeholder for randomized weight regime if needed, or reuse uniform/dopd logic
        # For now, treat as uniform with noise or skip
        print("Randomized weight regime not fully implemented, skipping or using uniform.")
        result = train_uniform(env, student, teacher, config, seed, steps)
    
    # Run generalization analysis
    gen_result = run_generalization_analysis(env, student, teacher, config, seed, steps)
    result['generalization'] = gen_result
    
    return result

def main():
    args = parse_args()
    
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    results = []
    
    if args.regimes:
        regimes = [r.strip() for r in args.regimes.split(',')]
        seeds = list(range(args.seeds))
        for regime in regimes:
            for seed in seeds:
                try:
                    res = run_single_regime_seed(args, regime, seed, args.steps)
                    results.append({
                        'regime': regime,
                        'seed': seed,
                        'result': res
                    })
                except Exception as e:
                    print(f"Error in regime {regime} seed {seed}: {e}")
                    import traceback
                    traceback.print_exc()
    else:
        # Single run
        res = run_single_regime_seed(args, args.regime, args.seed, args.steps)
        results.append({
            'regime': args.regime,
            'seed': args.seed,
            'result': res
        })
    
    # Save aggregated results
    output_path = 'data/processed/experiment_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Experiment completed. Results saved to {output_path}")

if __name__ == '__main__':
    main()