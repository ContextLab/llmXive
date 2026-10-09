"""
Citation validation script for the project.

This script invokes the external ``reference-validator`` CLI on the project's
``research.md`` file and ensures that every citation meets the configured
similarity threshold (default: 0.7).  It integrates with the project's
logging and error‑handling utilities so that failures are recorded in a
structured JSON‑line log and cause the pipeline to abort with a
``PipelineError``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, handle_error

__all__ = ["main"]

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Relative location of the research markdown file.  The script resides in
# ``code/reference_validation/``; the markdown file lives at the repository
# root.
RESEARCH_MD_RELATIVE = Path(__file__).resolve().parents[2] / "research.md"

# Default similarity threshold for the reference‑validator CLI.
DEFAULT_THRESHOLD = "0.7"


def _run_reference_validator(md_path: Path, threshold: str) -> subprocess.CompletedProcess:
    """
    Execute the ``reference-validator`` command‑line tool.

    Parameters
    ----------
    md_path: Path
        Path to the markdown file to validate.
    threshold: str
        The similarity threshold to pass to the CLI.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object.
    """
    cmd = ["reference-validator", str(md_path), "--threshold", threshold]
    logger = get_logger(__name__)
    logger.info("Running reference-validator", extra={"command": cmd})
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        # The CLI is not installed – raise a clear pipeline error.
        raise PipelineError(
            f"reference-validator CLI not found. Ensure it is installed "
            f"(add 'reference-validator' to requirements.txt)."
        ) from exc
    return result


def main() -> None:
    """
    Entry point for the citation‑validation step.

    The function performs the following actions:

    1. Verify that ``research.md`` exists.
    2. Call the ``reference-validator`` CLI with the configured threshold.
    3. Log the CLI output.
    4. Raise ``PipelineError`` if any citation fails (non‑zero exit code).
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1. Locate the markdown file.
    # ------------------------------------------------------------------
    if not RESEARCH_MD_RELATIVE.is_file():
        raise PipelineError(
            f"Research markdown file not found at expected location: {RESEARCH_MD_RELATIVE}"
        )
    logger.info("Found research markdown file", extra={"path": str(RESEARCH_MD_RELATIVE)})

    # ------------------------------------------------------------------
    # 2. Run the validator.
    # ------------------------------------------------------------------
    result = _run_reference_validator(RESEARCH_MD_RELATIVE, DEFAULT_THRESHOLD)

    # ------------------------------------------------------------------
    # 3. Log the output (both stdout and stderr) in a structured way.
    # ------------------------------------------------------------------
    log_dict(
        logger,
        {
            "step": "reference_validation",
            "cmd": ["reference-validator", str(RESEARCH_MD_RELATIVE), "--threshold", DEFAULT_THRESHOLD],
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    )

    # ------------------------------------------------------------------
    # 4. Handle failure.
    # ------------------------------------------------------------------
    if result.returncode != 0:
        # The CLI returns a non‑zero code when any citation does not meet the
        # threshold.  We surface this as a pipeline‑level error.
        raise PipelineError(
            f"Reference validation failed (return code {result.returncode}). "
            f"See log for details."
        )
    else:
        logger.info("All citations passed reference validation.")


if __name__ == "__main__":
    # When executed as a script, any unhandled exception is routed through
    # the project's ``handle_error`` helper to ensure consistent logging
    # and exit behaviour.
    handle_error(main)
