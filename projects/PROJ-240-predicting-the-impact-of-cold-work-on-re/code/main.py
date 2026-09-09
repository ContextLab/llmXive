"""
Main orchestration script for the llmXive project.

This script coordinates the execution of all pipeline steps:
1. Generate synthetic data
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

from generate_synthetic import main as run_generate
from ingest import main as run_ingest
from engineer import main as run_engineer
from finalize_dataset import main as run_finalize
from train import main as run_train
from evaluate import main as run_evaluate

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Orchestrate the llmXive pipeline")
    parser.add_argument(
        "--step",
        type=str,
        choices=["generate", "ingest", "engineer", "finalize", "train", "evaluate", "all"],
        default="all",
        help="Which step to run (default: all)"
    )
    return parser.parse_args()

def run_generate_step():
    """Run the data generation step."""
    print("Running data generation step...")
    return run_generate()

def run_ingest_step():
    """Run the data ingestion step."""
    print("Running data ingestion step...")
    return run_ingest()

def run_engineer_step():
    """Run the feature engineering step."""
    print("Running feature engineering step...")
    return run_engineer()

def run_finalize_step():
    """Run the dataset finalization step."""
    print("Running dataset finalization step...")
    return run_finalize()

def run_train_step():
    """Run the model training step."""
    print("Running model training step...")
    return run_train()

def run_evaluate_step():
    """Run the model evaluation step."""
    print("Running model evaluation step...")
    return run_evaluate()

def run_all_steps():
    """Run all pipeline steps in sequence."""
    steps = [
        ("generate", run_generate_step),
        ("ingest", run_ingest_step),
        ("engineer", run_engineer_step),
        ("finalize", run_finalize_step),
        ("train", run_train_step),
        ("evaluate", run_evaluate_step),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"Executing step: {step_name}")
        print(f"{'='*60}")
        try:
            result = step_func()
            if result != 0:
                print(f"Step {step_name} failed with exit code {result}")
                return result
        except Exception as e:
            print(f"Step {step_name} raised an exception: {e}")
            return 1
    
    print("\nPipeline completed successfully!")
    return 0

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.step == "all":
        return run_all_steps()
    
    step_map = {
        "generate": run_generate_step,
        "ingest": run_ingest_step,
        "engineer": run_engineer_step,
        "finalize": run_finalize_step,
        "train": run_train_step,
        "evaluate": run_evaluate_step,
    }
    
    if args.step not in step_map:
        print(f"Unknown step: {args.step}")
        return 1
    
    return step_map[args.step]()

if __name__ == "__main__":
    sys.exit(main())