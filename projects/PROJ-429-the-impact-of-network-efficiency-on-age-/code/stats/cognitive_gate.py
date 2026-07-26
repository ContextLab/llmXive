"""
Cognitive Data Gate Module (T023a).

Checks data/quality/download_report.json to determine if cognitive data is available.
If no cognitive data is found (missing_cognitive_count == total_count), it generates
a status file blocking User Story 2 and 3, allowing the pipeline to proceed with
EEG-only analysis.
"""
import json
import logging
import sys
from pathlib import Path

from config import ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def load_download_report(report_path: Path) -> dict:
    """
    Load the download report JSON file.

    Args:
        report_path: Path to data/quality/download_report.json

    Returns:
        Dictionary containing the report data.

    Raises:
        FileNotFoundError: If the report file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not report_path.exists():
        raise FileNotFoundError(
            f"Download report not found at {report_path}. "
            "Please run code/data/download.py first (T005_run)."
        )

    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_cognitive_availability(report: dict) -> tuple[bool, str]:
    """
    Check if cognitive data is available based on the report.

    Logic:
        - If missing_cognitive_count == total_count, cognitive data is BLOCKED.
        - Otherwise, data exists and we can proceed.

    Args:
        report: The loaded download report dictionary.

    Returns:
        Tuple of (is_available: bool, reason: str)
    """
    total_count = report.get("total_count", 0)
    missing_cognitive_count = report.get("missing_cognitive_count", 0)

    if total_count == 0:
        return False, "Total record count is zero; cannot proceed with cognitive analysis."

    if missing_cognitive_count == total_count:
        return (
            False,
            "No linked cognitive data found in TUH Corpus. Proceeding with EEG-only analysis.",
        )

    return True, "Cognitive data is available."

def write_status_file(status_path: Path, status: str, reason: str) -> None:
    """
    Write the cognitive status result to a JSON file.

    Args:
        status_path: Path to output file (data/results/cognitive_status.json).
        status: Status string ("BLOCKED" or "AVAILABLE").
        reason: Explanation string.
    """
    ensure_dirs(status_path)
    data = {
        "status": status,
        "reason": reason,
    }
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Cognitive status written to {status_path}: {status}")

def main() -> int:
    """
    Main entry point for the Cognitive Data Gate (T023a).

    Returns:
        0 on success (whether blocked or available).
    """
    config_paths = ensure_dirs(Path("."))
    report_path = config_paths["quality_dir"] / "download_report.json"
    status_path = config_paths["results_dir"] / "cognitive_status.json"

    logger.info(f"Loading download report from {report_path}")
    try:
        report = load_download_report(report_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report: {e}")
        return 1

    is_available, reason = check_cognitive_availability(report)

    if not is_available:
        logger.warning(f"Cognitive data gate: {reason}")
        write_status_file(status_path, "BLOCKED", reason)
        logger.info("User Story 2 and 3 are blocked. Pipeline will proceed with EEG-only analysis.")
    else:
        logger.info(f"Cognitive data gate: {reason}")
        write_status_file(status_path, "AVAILABLE", reason)
        logger.info("Proceeding to User Story 2 implementation.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
