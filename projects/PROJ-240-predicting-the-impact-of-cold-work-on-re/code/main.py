"""
Main pipeline orchestrator for the cold work recrystallization project.
Executes tasks in the correct dependency order, handling step dependencies
and providing a summary of generated artifacts.
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
    parser = argparse.ArgumentParser(
        description="Cold Work Recrystallization Pipeline"
    )
    parser.add_argument(
        "--step",
        type=str,
        help=(
            "Specific step to run. Available steps: generate, baseline, ingest, "
            "engineer, finalize, train, evaluate. All prior steps will be executed "
            "automatically to satisfy dependencies."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all steps in order (default behavior when no arguments are given).",
    )
    return parser.parse_args()


# Individual step wrappers -------------------------------------------------
def run_generate_step():
    """Run T011: Generate synthetic data."""
    print("Running Generate Step (T011)...")
    run_generate()


def run_baseline_stats_step():
    """Run T012: Calculate baseline statistics."""
    print("Running Baseline Stats Step (T012)...")
    run_baseline_stats()


def run_ingest_step():
    """Run T017‑T022: Ingest and clean data."""
    print("Running Ingest Step (T017‑T022)...")
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
    """Run T028‑T034: Train model."""
    print("Running Train Step (T028‑T034)...")
    run_train()


def run_evaluate_step():
    """Run T037‑T042: Evaluate model."""
    print("Running Evaluate Step (T037‑T042)...")
    run_evaluate()


# Ordered list of steps ----------------------------------------------------
STEP_SEQUENCE = [
    ("generate", run_generate_step),
    ("baseline", run_baseline_stats_step),
    ("ingest", run_ingest_step),
    ("engineer", run_engineer_step),
    ("finalize", run_finalize_step),
    ("train", run_train_step),
    ("evaluate", run_evaluate_step),
]


def run_steps_up_to(target_step: str):
    """
    Execute all steps in the pipeline up to and including ``target_step``.
    Steps are run in the order defined in ``STEP_SEQUENCE``.
    """
    step_names = [name for name, _ in STEP_SEQUENCE]
    if target_step not in step_names:
        raise ValueError(
            f"Unknown step '{target_step}'. Available steps: {step_names}"
        )
    target_index = step_names.index(target_step)
    for name, func in STEP_SEQUENCE[: target_index + 1]:
        print("\n" + "=" * 50)
        print(f"Executing step: {name}")
        print("=" * 50 + "\n")
        try:
            func()
        except Exception as e:
            print(f"ERROR in step '{name}': {e}")
            sys.exit(1)


def summarize_artifacts():
    """
    Print a concise summary of the most important pipeline artifacts.
    This helps users verify that the expected files were created.
    """
    root = Path.cwd()
    data_dir = root / "data"
    artifacts_dir = root / "artifacts"

    def list_files(base_path: Path, pattern: str = "*"):
        return sorted([str(p.relative_to(root)) for p in base_path.rglob(pattern)])

    print("\nPipeline Artifact Summary")
    print("-" * 30)
    print("Data artifacts:")
    for f in list_files(data_dir, "*.csv"):
        print(f"  {f}")
    print("\nArtifact files (reports, models, etc.):")
    for f in list_files(artifacts_dir):
        print(f"  {f}")
    print("-" * 30 + "\n")


def main():
    """Main entry point."""
    args = parse_args()

    if args.all or not args.step:
        # Run the full pipeline
        for name, func in STEP_SEQUENCE:
            print("\n" + "=" * 50)
            print(f"Executing step: {name}")
            print("=" * 50 + "\n")
            try:
                func()
            except Exception as e:
                print(f"ERROR in step '{name}': {e}")
                sys.exit(1)
    else:
        # Run up to the requested step, including all dependencies
        run_steps_up_to(args.step)

    # After successful execution, provide a summary of generated files
    summarize_artifacts()


if __name__ == "__main__":
    main()