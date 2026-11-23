"""
Unified training script for the molecular dipole prediction pipeline.
Orchestrates GNN and Random Forest training across multiple seeds.

This script fulfills the run-book requirement to invoke `python code/train.py`.
It delegates to the existing training modules (T028, T029) while ensuring
all outputs (checkpoints, metrics) are written to disk.
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

# Add code root to path to resolve relative imports if run as script
code_root = Path(__file__).parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from training.train_gnn import main as train_gnn_main, parse_args as parse_gnn_args
from training.train_rf import main as train_rf_main, parse_args as parse_rf_args
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Configuration
TIME_LIMIT_HOURS = 6
MEMORY_LIMIT_BYTES = 8 * 1024**3
CPU_LIMIT = 4

@time_limit(TIME_LIMIT_HOURS * 3600)
@memory_limit(MEMORY_LIMIT_BYTES)
@cpu_limit(CPU_LIMIT)
def run_training_pipeline(seeds: list[int], verbose: bool = True):
    """
    Orchestrates the training of both GNN and RF models for the given seeds.
    """
    if verbose:
        print(f"Starting training pipeline for seeds: {seeds}")
        print(f"Time limit: {TIME_LIMIT_HOURS}h, Memory limit: {MEMORY_LIMIT_BYTES / (1024**3):.1f}GB")

    # 1. Train GNN Models
    if verbose:
        print("\n--- Training SchNet GNN Models ---")
    
    # Prepare args for GNN
    gnn_args = argparse.Namespace(
        seeds=seeds,
        epochs=50,
        patience=10,
        batch_size=64,
        lr=0.001,
        hidden_dim=128,
        num_layers=3,
        verbose=verbose
    )
    
    try:
        train_gnn_main(gnn_args)
        if verbose:
            print("GNN training completed successfully.")
    except Exception as e:
        print(f"ERROR: GNN training failed: {e}")
        raise

    # 2. Train Random Forest Models
    if verbose:
        print("\n--- Training Random Forest Baseline ---")
    
    # Prepare args for RF
    rf_args = argparse.Namespace(
        seeds=seeds,
        epochs=50, # RF doesn't use epochs in the same way, but kept for interface consistency
        patience=10,
        n_estimators=100,
        max_depth=None,
        verbose=verbose
    )

    try:
        train_rf_main(rf_args)
        if verbose:
            print("Random Forest training completed successfully.")
    except Exception as e:
        print(f"ERROR: Random Forest training failed: {e}")
        raise

    if verbose:
        print("\n--- Pipeline Completed ---")
        print("All models trained. Checkpoints and metrics saved.")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Unified training script for molecular dipole prediction."
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="List of random seeds to use for training (default: 0 1 2 3 4)"
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Suppress verbose output"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    verbose = not args.no_verbose
    
    # Set global seed for reproducibility before starting
    if args.seeds:
        set_seed(args.seeds[0])
    
    run_training_pipeline(args.seeds, verbose=verbose)

if __name__ == "__main__":
    main()