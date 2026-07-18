import os
import sys
from pathlib import Path
import logging

# Ensure we can import sibling modules if needed, though this script is mostly standalone
# Add the parent directory of 'code' to sys.path if running as a script
if __name__ == "__main__":
    code_dir = Path(__file__).resolve().parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_PLOTS = [
    "scatter_tpsa_vs_half_life.png",
    "residuals.png",
    "qq_plot.png"
]

REQUIRED_REPORT = "results_report.md"

def verify_artifact(file_path: Path, description: str) -> bool:
    """
    Verifies that a file exists and has a non-zero size.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"MISSING: {description} at {file_path}")
        return False
    
    size = file_path.stat().st_size
    if size == 0:
        logger.error(f"EMPTY: {description} at {file_path} (0 bytes)")
        return False
    
    logger.info(f"OK: {description} found at {file_path} ({size} bytes)")
    return True

def main():
    """
    Main entry point for T036: Verify existence and non-zero size of required artifacts.
    """
    project_root = Path(__file__).resolve().parent.parent
    outputs_dir = project_root / "data" / "outputs"
    report_path = project_root / "results_report.md"

    all_valid = True

    # Ensure outputs directory exists (it should if T032/T033 ran successfully)
    if not outputs_dir.exists():
        logger.error(f"Outputs directory missing: {outputs_dir}")
        # We can't verify plots if the directory doesn't exist
        return 1

    # Verify plots
    logger.info("Verifying required plot files...")
    for plot_name in REQUIRED_PLOTS:
        plot_path = outputs_dir / plot_name
        if not verify_artifact(plot_path, f"Plot: {plot_name}"):
            all_valid = False

    # Verify report
    logger.info("Verifying report file...")
    if not verify_artifact(report_path, "Report: results_report.md"):
        all_valid = False

    if all_valid:
        logger.info("SUCCESS: All required artifacts for T036 exist and are non-zero.")
        return 0
    else:
        logger.error("FAILURE: One or more required artifacts are missing or empty.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
