"""
Main experiment runner script.

This script orchestrates the execution of tasks on different agent variants
and logs the results.
"""
import sys
import os
import argparse
from pathlib import Path
from src.analysis.runner import main as run_experiment_main
from src.utils.seeding import set_deterministic_seed


def main():
    """Main entry point for the experiment runner."""
    parser = argparse.ArgumentParser(description='Run EvoMem experiments')
    parser.add_argument('--config', type=str, default='full',
                      choices=['quick', 'full'],
                      help='Configuration to use for the experiment')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set deterministic seed
    set_deterministic_seed(args.seed)
    
    # Run the experiment
    run_experiment_main(args.config)


if __name__ == '__main__':
    main()
