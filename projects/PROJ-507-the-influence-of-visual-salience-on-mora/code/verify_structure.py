"""
Verify project directory structure.
Ensures all required directories exist as per the project plan.
"""
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

from logging_config import setup_logging, get_logger

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/survey",
    "data/synth",
    "tests",
    "contracts",
    "config",
    "docs",
]

def verify_structure(root_path: Path) -> tuple[bool, list[str], list[str]]:
    """
    Verify that all required directories exist under root_path.

    Returns:
        (success, missing_dirs, existing_dirs)
    """
    missing = []
    existing = []

    for dir_name in REQUIRED_DIRS:
        dir_path = root_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            existing.append(str(dir_path))
        else:
            missing.append(str(dir_path))

    return len(missing) == 0, missing, existing

def main():
    """
    Main entry point for structure verification.
    Writes results to data/logs/structure_log.txt.
    """
    # Setup logging
    setup_logging(log_level=logging.INFO)
    logger = get_logger(__name__)

    project_root = Path(__file__).resolve().parent.parent

    logger.info(f"Verifying project structure at: {project_root}")

    success, missing, existing = verify_structure(project_root)

    # Prepare log content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [
        f"Structure Verification Log",
        f"Timestamp: {timestamp}",
        f"Project Root: {project_root}",
        f"Status: {'PASSED' if success else 'FAILED'}",
        "",
        "Existing Directories:",
    ]
    for d in existing:
        log_lines.append(f"  [OK] {d}")

    if missing:
        log_lines.append("")
        log_lines.append("Missing Directories:")
        for d in missing:
            log_lines.append(f"  [MISSING] {d}")

    log_content = "\n".join(log_lines)

    # Ensure log directory exists
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "structure_log.txt"

    # Write log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(log_content)

    logger.info(f"Verification log written to: {log_file}")
    print(log_content)

    if not success:
        logger.error("Directory structure verification failed.")
        sys.exit(1)
    else:
        logger.info("Directory structure verification passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
