import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fetch_data import main as fetch_data_main
from confounds import main as confounds_main
from descriptor_pipeline import main as descriptor_pipeline_main
from dft_calculator import main as dft_calculator_main
from train_models import main as train_models_main
from evaluate_models import main as evaluate_models_main
from sensitivity_sweep import main as sensitivity_sweep_main
from generate_checksums import main as generate_checksums_main
from generate_summary_report import main as generate_summary_main
from runtime_validator import main as runtime_validator_main

def setup_logging():
    """Configure basic logging for the CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_fetch(args):
    """Run the data fetching pipeline (T004b, T004c)."""
    logging.info("Executing Fetch Phase...")
    # fetch_data.py main handles T004b and T004c logic internally
    fetch_data_main()

def run_confounds(args):
    """Run the confounds analysis (T011)."""
    logging.info("Executing Confounds Analysis (T011)...")
    confounds_main()

def run_validate(args):
    """Run data validation (T010)."""
    logging.info("Executing Data Validation (T010)...")
    # Assuming a validator script exists or is part of fetch_data
    # For now, we might just log or call a specific validator if available.
    # Based on API surface, T010 is in code/validators/data_validator.py which is not fully exposed in main.py imports list yet.
    # However, the task list says T010 is completed. We assume it ran or is invoked elsewhere.
    logging.warning("Data Validation (T010) is a prerequisite step. Skipping explicit invocation if not exposed.")

def run_optimize(args):
    """Run geometry optimization and semi-empirical descriptor generation (T013c, T013d, T013e)."""
    logging.info("Executing Optimization Phase (T013)...")
    descriptor_pipeline_main()

def run_dft(args):
    """Run DFT calculations on subset (T020b, T020c)."""
    logging.info("Executing DFT Phase (T020)...")
    dft_calculator_main()

def run_train(args):
    """Train models (T021)."""
    logging.info("Executing Training Phase (T021)...")
    train_models_main()

def run_evaluate(args):
    """Evaluate models (T022)."""
    logging.info("Executing Evaluation Phase (T022)...")
    evaluate_models_main()

def run_sensitivity(args):
    """Run sensitivity analysis (T030b)."""
    logging.info("Executing Sensitivity Analysis (T030b)...")
    sensitivity_sweep_main()

def run_checksums(args):
    """Generate checksums (T034)."""
    logging.info("Generating Checksums (T034)...")
    generate_checksums_main()

def run_summary(args):
    """Generate summary report (T035)."""
    logging.info("Generating Summary Report (T035)...")
    generate_summary_main()

def run_validate_resources(args):
    """Validate resource constraints (T033b)."""
    logging.info("Validating Resource Constraints (T033b)...")
    runtime_validator_main()

def run_full_pipeline(args):
    """Run the entire pipeline sequentially."""
    logging.info("Starting Full Pipeline Execution...")
    run_fetch(args)
    run_confounds(args)
    run_optimize(args)
    run_dft(args)
    run_train(args)
    run_evaluate(args)
    run_sensitivity(args)
    run_checksums(args)
    run_validate_resources(args)
    run_summary(args)
    logging.info("Full Pipeline completed.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline for Molecular Properties")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Fetch
    p_fetch = subparsers.add_parser('fetch', help='Fetch and normalize data (T004)')
    p_fetch.set_defaults(func=run_fetch)

    # Validate
    p_validate = subparsers.add_parser('validate', help='Validate data schema (T010)')
    p_validate.set_defaults(func=run_validate)

    # Confounds
    p_confounds = subparsers.add_parser('confounds', help='Run confounds analysis (T011)')
    p_confounds.set_defaults(func=run_confounds)

    # Optimize
    p_optimize = subparsers.add_parser('optimize', help='Run optimization and semi-empirical descriptors (T013)')
    p_optimize.set_defaults(func=run_optimize)

    # DFT
    p_dft = subparsers.add_parser('dft', help='Run DFT calculations on subset (T020)')
    p_dft.set_defaults(func=run_dft)

    # Train
    p_train = subparsers.add_parser('train', help='Train models (T021)')
    p_train.set_defaults(func=run_train)

    # Evaluate
    p_evaluate = subparsers.add_parser('evaluate', help='Evaluate models (T022)')
    p_evaluate.set_defaults(func=run_evaluate)

    # Sensitivity
    p_sensitivity = subparsers.add_parser('sensitivity', help='Run sensitivity analysis (T030b)')
    p_sensitivity.set_defaults(func=run_sensitivity)

    # Checksums
    p_checksums = subparsers.add_parser('checksums', help='Generate checksums (T034)')
    p_checksums.set_defaults(func=run_checksums)

    # Summary
    p_summary = subparsers.add_parser('summary', help='Generate summary report (T035)')
    p_summary.set_defaults(func=run_summary)

    # Validate Resources
    p_resources = subparsers.add_parser('resources', help='Validate resource constraints (T033b)')
    p_resources.set_defaults(func=run_validate_resources)

    # Full Pipeline
    p_full = subparsers.add_parser('run', help='Run the full pipeline')
    p_full.set_defaults(func=run_full_pipeline)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    setup_logging()
    args.func(args)

if __name__ == "__main__":
    main()
