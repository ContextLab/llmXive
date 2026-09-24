"""
Main pipeline orchestrator for the cold work recrystallization project.
Executes tasks in the correct dependency order.
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generate_synthetic import main as run_generate
from calculate_baseline_stats import main as run_baseline_stats
from ingest import main as run_ingest
from engineer import main as run_engineer
from finalize_dataset import main as run_finalize
from train import main as run_train
from evaluate import main as run_evaluate


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Cold Work Recrystallization Pipeline")
    parser.add_argument("--step", type=str, help="Specific step to run (generate, baseline, ingest, engineer, finalize, train, evaluate)")
    parser.add_argument("--all", action="store_true", help="Run all steps in order")
    return parser.parse_args()


def run_generate_step():
    """Run T011: Generate synthetic data."""
    print("Running Generate Step (T011)...")
    run_generate()


def run_baseline_stats_step():
    """Run T012: Calculate baseline statistics."""
    print("Running Baseline Stats Step (T012)...")
    run_baseline_stats()


def run_ingest_step():
    """Run T017-T022: Ingest and clean data."""
    print("Running Ingest Step (T017-T022)...")
    run_ingest()


def run_engineer_step():
    """Run T024: Engineer features."""
    print("Running Engineer Step (T024)...")
    run_engineer()


def run_finalize_step():
    """Run T025: Finalize dataset."""
    print("Running Finalize Step (T025)...")
    run_finalize()


def run_train_step():
    """Run T028-T034: Train model."""
    print("Running Train Step (T028-T034)...")
    run_train()


def run_evaluate_step():
    """Run T037-T042: Evaluate model."""
    print("Running Evaluate Step (T037-T042)...")
    run_evaluate()


def run_all_steps():
    """Run the full pipeline in dependency order."""
    steps = [
        ("Generate", run_generate_step),
        ("Baseline Stats", run_baseline_stats_step),
        ("Ingest", run_ingest_step),
        ("Engineer", run_engineer_step),
        ("Finalize", run_finalize_step),
        ("Train", run_train_step),
        ("Evaluate", run_evaluate_step),
    ]
    
    print("Running full pipeline...")
    for name, func in steps:
        print(f"\n{'='*50}")
        print(f"Step: {name}")
        print(f"{'='*50}")
        try:
            func()
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            sys.exit(1)
    print("\nPipeline completed successfully.")


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.all:
        run_all_steps()
    elif args.step:
        step_map = {
            "generate": run_generate_step,
            "baseline": run_baseline_stats_step,
            "ingest": run_ingest_step,
            "engineer": run_engineer_step,
            "finalize": run_finalize_step,
            "train": run_train_step,
            "evaluate": run_evaluate_step,
        }
        if args.step not in step_map:
            print(f"Unknown step: {args.step}")
            print(f"Available steps: {list(step_map.keys())}")
            sys.exit(1)
        step_map[args.step]()
    else:
        # Default: run full pipeline
        run_all_steps()


if __name__ == "__main__":
    main()