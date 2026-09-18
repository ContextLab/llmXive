"""
Main entry point for the DOPD experiments.
Orchestrates training runs for Uniform and DOPD regimes.
This script is the canonical entry point referenced in quickstart.md.
"""
import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from agents.baseline_estimator import create_baseline_estimator
from training.dopd_distillation import train_dopd
from training.uniform_distillation import train_uniform
from utils.logging import TrainingLogger
from utils.seed_manager import get_seed_range_for_purpose
from utils.seeding import seed_everything

def parse_args():
    parser = argparse.ArgumentParser(description="Run DOPD experiments")
    parser.add_argument("--seed", type=int, default=42, help="Master seed")
    parser.add_argument("--regime", type=str, default="dopd", choices=["dopd", "uniform"], help="Training regime")
    parser.add_argument("--steps", type=int, default=1000, help="Number of training steps")
    parser.add_argument("--seeds", type=int, default=1, help="Number of seeds to run")
    parser.add_argument("--regimes", type=str, default="dopd", help="Comma-separated list of regimes to run")
    return parser.parse_args()

def run_single_regime_seed(regime: str, master_seed: int, steps: int):
    """Run a single training regime for a specific seed."""
    # Initialize seed
    seed_everything(master_seed)
    
    # Create environment
    env = PrivilegeMDP(seed=master_seed)
    
    # Create agents
    teacher = TeacherOracle(env)
    student = TabularQStudent(env, seed=master_seed)
    baseline_estimator = create_baseline_estimator(env, seed=master_seed)
    
    # Initialize logger
    logger = TrainingLogger(
        run_id=f"{regime}_seed_{master_seed}",
        output_dir="data/raw",
        seed=master_seed
    )
    
    # Train based on regime
    if regime == "dopd":
        trainer_func = train_dopd
    elif regime == "uniform":
        trainer_func = train_uniform
    else:
        raise ValueError(f"Unknown regime: {regime}")
    
    # Run training loop
    # The trainer function handles the actual training steps and logging
    results = trainer_func(
        env=env,
        teacher=teacher,
        student=student,
        baseline_estimator=baseline_estimator,
        logger=logger,
        total_steps=steps,
        seed=master_seed
    )
    
    # Save metrics
    logger.save_metrics()
    
    return results

def main():
    args = parse_args()
    
    # If multiple seeds requested, run loop
    if args.seeds > 1:
        regimes = args.regimes.split(",")
        for regime in regimes:
            regime = regime.strip()
            for i in range(args.seeds):
                # Generate distinct seeds for this run
                # Use a simple offset strategy for demonstration
                seed = args.seed + i * 100
                print(f"Running regime {regime} with seed {seed}")
                run_single_regime_seed(regime, seed, args.steps)
    else:
        # Single run
        print(f"Running regime {args.regime} with seed {args.seed}")
        run_single_regime_seed(args.regime, args.seed, args.steps)

if __name__ == "__main__":
    main()