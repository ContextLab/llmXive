"""
Main orchestration script for the cold work recrystallization pipeline.

This script coordinates the execution of all pipeline steps:
1. Generate synthetic data (if needed)
2. Ingest and validate data
3. Engineer features
4. Finalize dataset
5. Train model
6. Evaluate model
"""
import argparse
import sys
import os
from pathlib import Path

# Import step functions
from generate_synthetic import main as run_generate
from ingest import main as run_ingest
from engineer import main as run_engineer
from finalize_dataset import main as run_finalize
from train import main as run_train
from evaluate import main as run_evaluate
from config import get_project_root

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Cold Work Recrystallization Pipeline")
    parser.add_argument(
        "--step",
        type=str,
        choices=["generate", "ingest", "engineer", "finalize", "train", "evaluate", "all"],
        default="all",
        help="Which step(s) to run. Default: all"
    )
    return parser.parse_args()

def run_generate_step():
    """Run the data generation step."""
    print("Running generate step...")
    exit_code = run_generate()
    if exit_code != 0:
        print("Generate step failed.")
        sys.exit(exit_code)
    print("Generate step completed.")

def run_ingest_step():
    """Run the ingestion step."""
    print("Running ingest step...")
    exit_code = run_ingest()
    if exit_code != 0:
        print("Ingest step failed.")
        sys.exit(exit_code)
    print("Ingest step completed.")

def run_engineer_step():
    """Run the feature engineering step."""
    print("Running engineer step...")
    exit_code = run_engineer()
    if exit_code != 0:
        print("Engineer step failed.")
        sys.exit(exit_code)
    print("Engineer step completed.")

def run_finalize_step():
    """Run the finalize dataset step."""
    print("Running finalize step...")
    exit_code = run_finalize()
    if exit_code != 0:
        print("Finalize step failed.")
        sys.exit(exit_code)
    print("Finalize step completed.")

def run_train_step():
    """Run the training step."""
    print("Running train step...")
    exit_code = run_train()
    if exit_code != 0:
        print("Train step failed.")
        sys.exit(exit_code)
    print("Train step completed.")

def run_evaluate_step():
    """Run the evaluation step."""
    print("Running evaluate step...")
    exit_code = run_evaluate()
    if exit_code != 0:
        print("Evaluate step failed.")
        sys.exit(exit_code)
    print("Evaluate step completed.")

def run_all_steps():
    """Run all pipeline steps in order."""
    run_generate_step()
    run_ingest_step()
    run_engineer_step()
    run_finalize_step()
    run_train_step()
    run_evaluate_step()
    print("All steps completed successfully.")

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.step == "all":
        run_all_steps()
    elif args.step == "generate":
        run_generate_step()
    elif args.step == "ingest":
        run_ingest_step()
    elif args.step == "engineer":
        run_engineer_step()
    elif args.step == "finalize":
        run_finalize_step()
    elif args.step == "train":
        run_train_step()
    elif args.step == "evaluate":
        run_evaluate_step()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
