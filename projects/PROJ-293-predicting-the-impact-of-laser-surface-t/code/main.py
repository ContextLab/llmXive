"""
Entry point for the Laser Surface Texturing (LST) wear resistance pipeline.

Provides subcommands:
  - ingest
  - preprocess
  - train
  - interpret
  - report

The global random seed is fixed to 42 for reproducibility.
"""
import argparse
import sys
from pathlib import Path

# Ensure the seed is set before any other imports that may rely on randomness
from seed import ensure_seed_set

# Import subcommand entry points lazily to avoid unnecessary imports at startup
def _run_ingest(args):
    from ingest import main as ingest_main
    ingest_main()

def _run_preprocess(args):
    from preprocess import main as preprocess_main
    preprocess_main()

def _run_train(args):
    from train import main as train_main
    train_main()

def _run_interpret(args):
    from interpret import main as interpret_main
    interpret_main()

def _run_report(args):
    from report import main as report_main
    report_main()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m code.main",
        description="Runnable pipeline entry point for LST wear resistance project."
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline subcommands")

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Download and merge raw data sources.")
    ingest_parser.set_defaults(func=_run_ingest)

    # Preprocess subcommand
    preprocess_parser = subparsers.add_parser("preprocess", help="Clean, normalize and split the dataset.")
    preprocess_parser.set_defaults(func=_run_preprocess)

    # Train subcommand
    train_parser = subparsers.add_parser("train", help="Train regression models with CV and grid search.")
    train_parser.set_defaults(func=_run_train)

    # Interpret subcommand
    interpret_parser = subparsers.add_parser("interpret", help="Compute SHAP values and related analyses.")
    interpret_parser.set_defaults(func=_run_interpret)

    # Report subcommand
    report_parser = subparsers.add_parser("report", help="Aggregate metrics and generate final reports.")
    report_parser.set_defaults(func=_run_report)

    return parser

def main(argv=None):
    """
    Main entry point invoked via `python -m code.main <subcommand>`.
    """
    ensure_seed_set()  # Global fixed seed = 42
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the selected subcommand
    args.func(args)

if __name__ == "__main__":
    main()
