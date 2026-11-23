"""
validate_citations.py

Script to validate all external citations in a given research markdown file using the
``reference-validator`` CLI tool. The script is part of the T065A task which enforces
Constitution Principle II (citation validation) across the project.

Usage:
    python -m reference_validation.validate_citations <path-to-research.md> [--threshold 0.7]

The script logs its progress via the project's ``pipeline_logger`` and raises a
``PipelineError`` if any citation fails the configured threshold.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, handle_error

__all__ = ["run_validation", "main"]

def _build_command(markdown_path: Path, threshold: float) -> list[str]:
    """
    Construct the CLI command for ``reference-validator``.

    Parameters
    ----------
    markdown_path: Path
        Path to the markdown file containing citations.
    threshold: float
        Minimum title‑token‑overlap required for a citation to be considered valid.

    Returns
    -------
    list[str]
        The command to be passed to ``subprocess.run``.
    """
    return [
        "reference-validator",
        str(markdown_path),
        "--threshold",
        str(threshold),
    ]

@handle_error
def run_validation(markdown_path: Path, threshold: float = 0.7) -> None:
    """
    Execute the ``reference-validator`` CLI on ``markdown_path`` and raise a
    ``PipelineError`` if validation fails.

    Parameters
    ----------
    markdown_path: Path
        The markdown file to validate.
    threshold: float, optional
        Overlap threshold; defaults to 0.7.

    Raises
    ------
    PipelineError
        If the external validator returns a non‑zero exit status.
    """
    logger = get_logger(__name__)
    logger.info("Starting citation validation", extra={"file": str(markdown_path)})

    if not markdown_path.is_file():
        raise PipelineError(f"Markdown file not found: {markdown_path}")

    cmd = _build_command(markdown_path, threshold)
    logger.debug("Running command", extra={"cmd": cmd})

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Log raw output for debugging purposes
    log_dict(
        logger,
        {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        },
        level="debug",
    )

    if result.returncode != 0:
        # The validator reports failures via non‑zero exit code.
        raise PipelineError(
            f"Citation validation failed for {markdown_path}.\n"
            f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
        )

    logger.info(
        "Citation validation succeeded",
        extra={"file": str(markdown_path), "threshold": threshold},
    )

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate citations in a research markdown file using reference-validator."
    )
    parser.add_argument(
        "markdown_path",
        type=Path,
        help="Path to the markdown file containing citations to validate.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum title‑token‑overlap required (default: 0.7).",
    )
    return parser.parse_args()

def main() -> None:
    """
    Entry point for the script when executed directly.
    """
    args = _parse_args()
    run_validation(args.markdown_path, args.threshold)

if __name__ == "__main__":
    main()
