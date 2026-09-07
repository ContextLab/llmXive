"""
Main orchestration script for the Cold Work Recrystallization pipeline.
This script reconciles the run-book (quickstart.md) with the implementation
by providing a single entry point to execute the pipeline steps.

Usage:
    python code/main.py --step generate
    python code/main.py --step ingest
    python code/main.py --step engineer
    python code/main.py --step train
    python code/main.py --step evaluate
    python code/main.py --step all
"""
import argparse
import sys
import os
from pathlib import Path

# Ensure the code directory is in the path for relative imports if run from project root
# However, since we are importing from sibling modules in 'code/', we rely on the
# execution environment having 'code' in sys.path or running from the project root
# where 'code' is a package. The task assumes 'code' is the package root.
# We explicitly import the main functions from the existing modules.

def run_generate():
    """Execute T007: Generate synthetic baseline data."""
    print("Executing: Generate synthetic baseline data...")
    from code.generate_synthetic import main as gen_main
    gen_main()
    print("Success: data/raw/synthetic_baseline.csv generated.")

def run_ingest():
    """Execute T012-T017: Ingest, validate, and filter data."""
    print("Executing: Ingest and validate data...")
    from code.ingest import main as ingest_main
    ingest_main()
    print("Success: data/processed/validated.csv generated.")

def run_engineer():
    """Execute T018-T019: Engineer interaction features."""
    print("Executing: Engineer interaction features...")
    from code.engineer import main as engineer_main
    engineer_main()
    print("Success: data/processed/engineered_features.csv generated.")

def run_finalize():
    """Execute T020: Finalize dataset (row cap)."""
    print("Executing: Finalize dataset...")
    from code.finalize_dataset import main as finalize_main
    finalize_main()
    print("Success: data/processed/final_dataset.csv generated.")

def run_train():
    """Execute T023-T029: Train model and save metrics."""
    print("Executing: Train model...")
    from code.train import main as train_main
    train_main()
    print("Success: artifacts/models/kinetic_model.pkl and metrics generated.")

def run_evaluate():
    """Execute T032-T039: Statistical evaluation and SHAP."""
    print("Executing: Evaluate model and statistical significance...")
    from code.evaluate import main as eval_main
    eval_main()
    print("Success: Statistical reports and SHAP analysis generated.")

def run_all():
    """Execute the full pipeline."""
    run_generate()
    run_ingest()
    run_engineer()
    run_finalize()
    run_train()
    run_evaluate()
    print("Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate the Cold Work Recrystallization prediction pipeline."
    )
    parser.add_argument(
        "--step",
        type=str,
        required=True,
        choices=["generate", "ingest", "engineer", "finalize", "train", "evaluate", "all"],
        help="The pipeline step to execute."
    )
    args = parser.parse_args()

    try:
        if args.step == "generate":
            run_generate()
        elif args.step == "ingest":
            run_ingest()
        elif args.step == "engineer":
            run_engineer()
        elif args.step == "finalize":
            run_finalize()
        elif args.step == "train":
            run_train()
        elif args.step == "evaluate":
            run_evaluate()
        elif args.step == "all":
            run_all()
    except Exception as e:
        print(f"Error executing step '{args.step}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
