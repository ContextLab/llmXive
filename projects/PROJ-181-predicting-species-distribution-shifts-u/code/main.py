#!/usr/bin/env python
"""
Project entry point providing a simple CLI.

Sub‑commands:
  - scaffold : create the project scaffold (required by T001)
  - download : run the data‑download step (implemented in code/download.py)
  - preprocess : placeholder for the preprocessing step (to be implemented later)
  - train : placeholder for model training
  - evaluate : placeholder for evaluation and projection
  - report : placeholder for final report generation
"""
import argparse
import sys
from pathlib import Path

# Project‑wide logging initialisation
from code.logging_setup import initialize_logging
from llmxive_toolkit import paths
from llmxive_toolkit import get_logger

# Import the download entry point
from code.download import main as download_main

# Initialise logging for this script (creates logs/main.log)
initialize_logging(paths.logs("main.log"))
log = get_logger(__name__)

def _create_gitkeep(dir_path: Path) -> None:
    """
    Ensure a directory exists and contains a .gitkeep file.

    The .gitkeep file is written with a minimal comment so that the
    file is non‑empty (required by the execution validator).
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    gitkeep = dir_path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# placeholder for git tracking\n", encoding="utf-8")

def _ensure_flake8() -> None:
    """
    Create a minimal .flake8 configuration at the repository root if it
    does not already exist.
    """
    flake8_path = Path.cwd() / ".flake8"
    if not flake8_path.exists():
        flake8_path.write_text("[flake8]\nmax-line-length = 88\n", encoding="utf-8")

def scaffold() -> None:
    """
    Create the full project scaffold required by task T001.

    Directories created:
      code/, data/raw/, data/processed/, models/, metrics/,
      logs/, reports/, tests/, contracts/
    Each receives a .gitkeep file (non‑empty). A .flake8 file is added
    at the repository root.
    """
    root = Path.cwd()
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "models",
        "metrics",
        "logs",
        "reports",
        "tests",
        "contracts",
    ]
    for d in dirs:
        _create_gitkeep(root / d)

    _ensure_flake8()
    log.info("Project scaffold created successfully.")
    print("Project scaffold created successfully.")

def _unimplemented(command: str) -> None:
    """Utility for commands that are not yet implemented."""
    log.error(f"{command} command not implemented yet.")
    sys.stderr.write(f"{command} command not implemented yet.\n")
    sys.exit(1)

def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scaffold command – fully implemented
    subparsers.add_parser(
        "scaffold", help="Create the project scaffold (directories, .gitkeep files, .flake8)."
    )

    # download command – now forwards to the real download script
    subparsers.add_parser(
        "download", help="Download occurrence and climate data (implemented in code/download.py)."
    )

    # placeholders for future tasks
    subparsers.add_parser("preprocess", help="Pre‑process raw data (to be implemented).")
    subparsers.add_parser("train", help="Train SDM models (to be implemented).")
    subparsers.add_parser("evaluate", help="Evaluate and project models (to be implemented).")
    subparsers.add_parser("report", help="Generate final report (to be implemented).")

    args = parser.parse_args()

    if args.command == "scaffold":
        scaffold()
    elif args.command == "download":
        # Delegate to the fully‑featured download implementation
        download_main()
    elif args.command == "preprocess":
        _unimplemented("preprocess")
    elif args.command == "train":
        _unimplemented("train")
    elif args.command == "evaluate":
        _unimplemented("evaluate")
    elif args.command == "report":
        _unimplemented("report")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
