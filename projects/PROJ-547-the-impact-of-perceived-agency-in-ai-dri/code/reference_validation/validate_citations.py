"""
Citation validation script for the PROJ‑547 project.

This script is intended to be run as a blocking gate before any analysis
pipeline starts. It invokes the external ``reference-validator`` CLI on the
project's ``research.md`` file and aborts the pipeline if any citation
fails the configured similarity threshold.

The script uses the project's logging utilities so that failures are
recorded in the standard JSON‑line log files.
"""

import subprocess
from pathlib import Path
from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, handle_error

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Path to the research markdown file (relative to the repository root)
RESEARCH_MD_PATH = Path(__file__).resolve().parents[2] / "specs" / "PROJ-547-perceived-agency" / "research.md"

# Desired similarity threshold for the Reference‑Validator tool
VALIDATION_THRESHOLD = "0.7"

# CLI command name – assumed to be available in the environment after installing
# the ``reference-validator`` package (added to ``requirements.txt``).
REFERENCE_VALIDATOR_CMD = "reference-validator"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _run_reference_validator(md_path: Path, threshold: str) -> subprocess.CompletedProcess:
    """
    Execute the ``reference-validator`` CLI.

    Parameters
    ----------
    md_path: Path
        Path to the markdown file containing citations.
    threshold: str
        Minimum token‑overlap score required for a citation to be considered valid.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object containing return code and output.
    """
    cmd = [
        REFERENCE_VALIDATOR_CMD,
        str(md_path),
        "--threshold",
        threshold,
    ]
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
@handle_error
def main() -> None:
    """
    Run the citation validation gate.

    If the external validator reports any failures (non‑zero exit status),
    the function logs the error details and raises ``PipelineError`` to abort
    the pipeline.
    """
    logger = get_logger(__name__)

    if not RESEARCH_MD_PATH.is_file():
        error_msg = f"Research markdown file not found at {RESEARCH_MD_PATH}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    logger.info(f"Running reference validation on {RESEARCH_MD_PATH}")

    result = _run_reference_validator(RESEARCH_MD_PATH, VALIDATION_THRESHOLD)

    # Log the raw output for traceability
    log_dict(
        logger,
        {
            "step": "reference_validation",
            "command": " ".join(result.args),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )

    if result.returncode != 0:
        # Validation failed – abort the pipeline
        error_msg = (
            "Reference validation failed. "
            "Citations did not meet the required similarity threshold.\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        logger.error(error_msg)
        raise PipelineError(error_msg)

    logger.info("All citations passed reference validation.")

if __name__ == "__main__":
    main()
