"""
Run Experiment Script for DOPD vs Uniform Supervision Analysis.

This script orchestrates 50 independent seeds, training both DOPD and Uniform
distillation regimes, and logging the results to data/raw/.

It ensures distinct seeds for training and evaluation as per FR-007.
"""
import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np

from utils.seeding import seed_everything, generate_seed_sequence
from utils.logging import TrainingLogger
from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from training.uniform_distillation import train_uniform
from training.dopd_distillation import train_dopd
from analysis.generalization_test import run_generalization_analysis
from analysis.stats import load_accuracy_logs, calculate_coefficient_of_variation

# Constants
NUM_SEEDS = 50
NUM_TRAINING_STEPS = 10000
NUM_EVAL_STEPS = 1000
EVAL_SEED_OFFSET = 100000  # Ensure distinct seeds for evaluation

def run_single_seed(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a single experiment iteration for a given seed.

    Args:
        seed: The random seed for this iteration.
        config: Configuration dictionary containing hyperparameters.

    Returns:
        Dictionary containing training and evaluation metrics.
    """
    # Initialize RNG for this seed
    seed_everything(seed)

    # Create environment
    env = PrivilegeMDP(
        grid_size=config['grid_size'],
        reward_scale=config['reward_scale'],
        noise_level=config['noise_level'],
        seed=seed
    )

    # Create Teacher and Student
    teacher = TeacherOracle(env, seed=seed)
    student = TabularQStudent(env, seed=seed)

    # Setup logger
    logger = TrainingLogger(
        run_id=f"seed_{seed}",
        output_dir=os.path.join(config['output_dir'], 'logs'),
        seed=seed
    )

    # Train DOPD Student
    dopd_config = {
        'num_steps': NUM_TRAINING_STEPS,
        'learning_rate': config['learning_rate'],
        'epsilon_start': config['epsilon_start'],
        'epsilon_end': config['epsilon_end'],
        'gamma': config['gamma'],
        'advantage_threshold': config['advantage_threshold'],
        'weight_decay': config['weight_decay'],
        'batch_size': config['batch_size']
    }

    dopd_metrics = train_dopd(
        env=env,
        teacher=teacher,
        student=student,
        config=dopd_config,
        logger=logger
    )

    # Train Uniform Student (fresh instance)
    student_uniform = TabularQStudent(env, seed=seed)
    uniform_config = {
        'num_steps': NUM_TRAINING_STEPS,
        'learning_rate': config['learning_rate'],
        'epsilon_start': config['epsilon_start'],
        'epsilon_end': config['epsilon_end'],
        'gamma': config['gamma'],
        'batch_size': config['batch_size']
    }

    uniform_metrics = train_uniform(
        env=env,
        teacher=teacher,
        student=student_uniform,
        config=uniform_config,
        logger=logger
    )

    # Evaluate both students (using distinct seeds for evaluation)
    eval_seed_train = seed
    eval_seed_test = seed + EVAL_SEED_OFFSET

    # DOPD Evaluation
    dopd_eval_seed = eval_seed_test
    seed_everything(dopd_eval_seed)
    dopd_eval_results = run_generalization_analysis(
        student=student,
        env=env,
        num_steps=NUM_EVAL_STEPS,
        seed=dopd_eval_seed
    )

    # Uniform Evaluation
    uniform_eval_seed = eval_seed_test + 1
    seed_everything(uniform_eval_seed)
    uniform_eval_results = run_generalization_analysis(
        student=student_uniform,
        env=env,
        num_steps=NUM_EVAL_STEPS,
        seed=uniform_eval_seed
    )

    # Compile results
    results = {
        'seed': seed,
        'dopd': {
            'training': dopd_metrics,
            'evaluation': dopd_eval_results
        },
        'uniform': {
            'training': uniform_metrics,
            'evaluation': uniform_eval_results
        }
    }

    return results

def main():
    parser = argparse.ArgumentParser(description='Run DOPD vs Uniform Experiment')
    parser.add_argument('--num-seeds', type=int, default=NUM_SEEDS,
                        help=f'Number of seeds to run (default: {NUM_SEEDS})')
    parser.add_argument('--output-dir', type=str, default='data/raw',
                        help='Output directory for logs and results')
    parser.add_argument('--config-file', type=str, default=None,
                        help='Path to JSON config file (optional)')
    args = parser.parse_args()

    # Default configuration
    config = {
        'grid_size': 5,
        'reward_scale': 1.0,
        'noise_level': 0.1,
        'learning_rate': 0.1,
        'epsilon_start': 1.0,
        'epsilon_end': 0.01,
        'gamma': 0.99,
        'advantage_threshold': 0.1,
        'weight_decay': 0.0,
        'batch_size': 1,
        'output_dir': args.output_dir
    }

    # Load custom config if provided
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            custom_config = json.load(f)
            config.update(custom_config)

    # Ensure output directory exists
    os.makedirs(config['output_dir'], exist_ok=True)
    os.makedirs(os.path.join(config['output_dir'], 'logs'), exist_ok=True)

    # Generate seed sequence
    base_seed = 42
    seed_sequence = generate_seed_sequence(base_seed, args.num_seeds)

    print(f"Starting experiment with {args.num_seeds} seeds...")
    print(f"Base seed: {base_seed}")
    print(f"Output directory: {config['output_dir']}")

    all_results = []

    for i, seed in enumerate(seed_sequence):
        print(f"\n--- Running seed {i+1}/{args.num_seeds} (seed={seed}) ---")
        try:
            results = run_single_seed(seed, config)
            all_results.append(results)

            # Save individual seed results
            seed_output_path = os.path.join(
                config['output_dir'],
                f'seed_{seed}.json'
            )
            with open(seed_output_path, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"Completed seed {seed}. Results saved to {seed_output_path}")

        except Exception as e:
            print(f"ERROR: Failed to complete seed {seed}: {str(e)}")
            # Log error but continue with other seeds
            error_result = {
                'seed': seed,
                'error': str(e),
                'dopd': None,
                'uniform': None
            }
            all_results.append(error_result)

    # Save aggregated results
    aggregated_path = os.path.join(config['output_dir'], 'experiment_results.json')
    with open(aggregated_path, 'w') as f:
        json.dump({
            'metadata': {
                'num_seeds': args.num_seeds,
                'base_seed': base_seed,
                'config': config,
                'timestamp': datetime.now().isoformat()
            },
            'results': all_results
        }, f, indent=2)

    print(f"\n--- Experiment Complete ---")
    print(f"All results saved to {aggregated_path}")

    # Quick summary
    successful_seeds = [r for r in all_results if r.get('dopd') is not None]
    print(f"Successful seeds: {len(successful_seeds)}/{args.num_seeds}")

    if len(successful_seeds) > 0:
        dopd_accs = [r['dopd']['evaluation']['accuracy'] for r in successful_seeds if 'evaluation' in r['dopd']]
        uniform_accs = [r['uniform']['evaluation']['accuracy'] for r in successful_seeds if 'evaluation' in r['uniform']]

        if dopd_accs and uniform_accs:
            print(f"DOPD Mean Accuracy: {np.mean(dopd_accs):.4f} (+/- {np.std(dopd_accs):.4f})")
            print(f"Uniform Mean Accuracy: {np.mean(uniform_accs):.4f} (+/- {np.std(uniform_accs):.4f})")

if __name__ == '__main__':
    main()
