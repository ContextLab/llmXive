"""
T013: Pipeline Orchestrator.
Executes the full pipeline: T011 -> T022 -> T024 -> T029 -> T039.
"""
import argparse
import sys
import os
import subprocess
from pathlib import Path

# Import main functions from pipeline steps
from generate_synthetic import main as run_generate
from ingest import main as run_ingest
from engineer import main as run_engineer
from finalize_dataset import main as run_finalize
from train import main as run_train
from evaluate import main as run_evaluate

def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline Orchestrator")
    parser.add_argument("--step", type=str, choices=["generate", "ingest", "engineer", "finalize", "train", "evaluate", "all"],
                        help="Specific step to run. Defaults to 'all'.")
    return parser.parse_args()

def run_generate_step():
    print("Running Generate Step (T011)...")
    run_generate()
    print("Generate Step completed.")

def run_ingest_step():
    print("Running Ingest Step (T022)...")
    run_ingest()
    print("Ingest Step completed.")

def run_engineer_step():
    print("Running Engineer Step (T024)...")
    run_engineer()
    print("Engineer Step completed.")

def run_finalize_step():
    print("Running Finalize Step (T025)...")
    run_finalize()
    print("Finalize Step completed.")

def run_train_step():
    print("Running Train Step (T029, T030, T031, T032, T033, T034)...")
    run_train()
    print("Train Step completed.")

def run_evaluate_step():
    print("Running Evaluate Step (T037, T038, T039, T040, T041)...")
    run_evaluate()
    print("Evaluate Step completed.")

def run_all_steps():
    run_generate_step()
    run_ingest_step()
    run_engineer_step()
    run_finalize_step()
    run_train_step()
    run_evaluate_step()

def main():
    args = parse_args()
    
    if args.step == "all" or args.step is None:
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
    
    print("Pipeline execution finished.")

if __name__ == "__main__":
    main()