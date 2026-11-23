"""
Entry point for the full Glass Forming Region prediction pipeline.

Executes each stage of the pipeline sequentially:
1. Ingestion
2. Feature engineering
3. Model training
4. Analysis
5. Report generation
6. Schema validation
"""

import sys
import subprocess
import logging
from pathlib import Path

# Use the project's logger utility
from llmxive_toolkit import get_logger

log = get_logger(__name__)


def run_script(relative_path: str) -> None:
    """
    Run a Python script located at `relative_path` using the current interpreter.
    Logs stdout and stderr; aborts on non‑zero exit code.
    """
    script_path = Path(relative_path)
    if not script_path.is_file():
        log.error(f"Script not found: {script_path}")
        sys.exit(1)

    cmd = [sys.executable, str(script_path)]
    log.info(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Log output for debugging
    if result.stdout:
        log.info(result.stdout)
    if result.stderr:
        log.error(result.stderr)

    if result.returncode != 0:
        log.error(f"Script {script_path} exited with code {result.returncode}")
        sys.exit(result.returncode)


def main() -> None:
    """Run all pipeline stages in the required order."""
    steps = [
        "code/ingestion.py",
        "code/features.py",
        "code/train.py",
        "code/analyze.py",
        "code/generate_report.py",
        "code/validate_schemas.py",
    ]

    for step in steps:
        run_script(step)

    log.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()