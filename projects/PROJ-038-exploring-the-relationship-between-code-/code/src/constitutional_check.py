"""
Constitutional Check Module for llmXive Pipeline.

This module handles the verification of constitutional amendments
required before proceeding with the research pipeline.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConstitutionalBlockError(Exception):
    """Raised when the constitutional amendment check fails."""
    pass


def verify_amendment_artifact(marker_path: Path) -> bool:
    """
    Verify the existence of the amendment ratification marker.

    Args:
        marker_path: Path to the amendment_ratified.md file.

    Returns:
        True if the file exists and is non-empty.

    Raises:
        ConstitutionalBlockError: If the file is missing or empty.
    """
    if not marker_path.exists():
        logger.error(f"Amendment marker file not found: {marker_path}")
        raise ConstitutionalBlockError(
            f"Constitutional Amendment Check Failed: "
            f"Marker file '{marker_path}' does not exist. "
            "Please ensure the PR has been merged and the marker file created by a human."
        )

    if marker_path.stat().st_size == 0:
        logger.error(f"Amendment marker file is empty: {marker_path}")
        raise ConstitutionalBlockError(
            f"Constitutional Amendment Check Failed: "
            f"Marker file '{marker_path}' is empty."
        )

    logger.info(f"Amendment marker verified: {marker_path}")
    return True


def main() -> int:
    """
    Main entry point for the constitutional check task.

    Checks for the existence of the amendment_ratified.md marker file.
    Returns 0 on success, 1 on failure (blocking the pipeline).

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Define the expected path relative to the project root
    # Assuming the script is run from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent.parent
    marker_path = project_root / "amendment_ratified.md"

    # Also check relative to current working directory if not found in project root
    if not marker_path.exists():
        cwd_marker = Path.cwd() / "amendment_ratified.md"
        if cwd_marker.exists():
            marker_path = cwd_marker

    try:
        verify_amendment_artifact(marker_path)
        logger.info("Constitutional amendment ratified. Pipeline can proceed.")
        return 0
    except ConstitutionalBlockError as e:
        logger.error(str(e))
        logger.error("Pipeline execution HALTED until human intervention resolves the constitutional conflict.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
