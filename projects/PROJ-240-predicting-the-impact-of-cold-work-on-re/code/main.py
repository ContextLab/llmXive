"""
Main orchestration script for the pipeline.
Executes steps sequentially: Generate -> Ingest -> Engineer -> Finalize -> Train -> Evaluate.
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

def parse_args():
    parser = argparse.ArgumentParser(description="Run the cold-work recrystallization pipeline.")
    parser.add_argument(
        "--step",
        type=str,
        choices=["generate", "ingest", "engineer", "finalize", "train", "evaluate", "all"],
        default="all",
        help="Which step to run. Default is 'all'."
    )
    return parser.parse_args()

def run_generate_step():
    print("Running Step 1: Generate Synthetic Data...")
    run_generate()

def run_ingest_step():
    print("Running Step 2: Ingest and Validate Data...")
    run_ingest()

def run_engineer_step():
    print("Running Step 3: Engineer Features...")
    run_engineer()

def run_finalize_step():
    print("Running Step 4: Finalize Dataset (T025)...")
    run_finalize()

def run_train_step():
    print("Running Step 5: Train Model...")
    run_train()

def run_evaluate_step():
    print("Running Step 6: Evaluate Model...")
    run_evaluate()

def run_all_steps():
    print("Running full pipeline...")
    run_generate_step()
    run_ingest_step()
    run_engineer_step()
    run_finalize_step()
    run_train_step()
    run_evaluate_step()
    print("Pipeline completed successfully.")

def main():
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
    else:
        print(f"Unknown step: {args.step}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
