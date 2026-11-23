"""
Interpret CLI entry point for User Story 3.
Orchestrates partial dependence plots and feature importance export.
Enforces the 10MB total plot size limit (T034c / T050).
"""
import os
import sys
import logging
import glob
from pathlib import Path
from typing import List

# Import local project modules using the provided API surface
# Note: The API surface shows src modules, but the file structure is code/src/...
# We adjust imports to match the actual file location relative to the project root.
# Since this file is at code/src/cli/interpret.py, we import from code/src/...
# However, the prompt's "Existing project API surface" lists imports as `from src.xxx`.
# To ensure this runs correctly in the `code/` directory context, we assume PYTHONPATH
# includes `code/` or we adjust relative imports.
# Based on the task description, we are implementing `src/cli/interpret.py`.
# The existing API surface lists `code/src/cli/interpret.py` as the location.
# We will use absolute imports assuming `code` is in sys.path or we are running from `code`.
# To be safe and consistent with the "Existing project API surface" which says:
# `import as: from src.cli.interpret import ...`
# We will write the code assuming it is run from the `code` directory or PYTHONPATH is set.

from src.interpret.partial_dependence import generate_partial_dependence_plots
from src.interpret.feature_importance import export_feature_importance
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

PLOT_SIZE_LIMIT_MB = 10
PLOT_DIR = "results"
PLOT_PATTERN = "partial_dependence_*.png"

def validate_plot_size(plot_dir: str, pattern: str) -> bool:
    """
    Calculates the total file size of all generated plots.
    Raises SystemExit if total size > limit.
    """
    plot_path = Path(plot_dir)
    if not plot_path.exists():
        logger.warning(f"Plot directory {plot_dir} does not exist. Skipping size validation.")
        return True

    matches = list(plot_path.glob(pattern))
    if not matches:
        logger.warning(f"No plots found matching {pattern} in {plot_dir}. Skipping size validation.")
        return True

    total_size_bytes = 0
    large_files = []
    
    logger.info(f"Validating plot sizes for {len(matches)} files in {plot_dir}...")

    for file_path in matches:
        size = file_path.stat().st_size
        total_size_bytes += size
        if size > 0:
            logger.debug(f"Plot {file_path.name}: {size / 1024:.2f} KB")

    total_size_mb = total_size_bytes / (1024 * 1024)
    limit_bytes = PLOT_SIZE_LIMIT_MB * 1024 * 1024

    logger.info(f"Total plot size: {total_size_mb:.2f} MB (Limit: {PLOT_SIZE_LIMIT_MB} MB)")

    if total_size_bytes > limit_bytes:
        offending_files = [f.name for f in matches if f.stat().st_size > 0]
        error_msg = (
            f"CRITICAL: Total plot size ({total_size_mb:.2f} MB) exceeds limit ({PLOT_SIZE_LIMIT_MB} MB).\n"
            f"Offending files: {offending_files}"
        )
        logger.error(error_msg)
        raise SystemExit(error_msg)

    logger.info("Plot size validation passed.")
    return True

def main():
    """
    Main entry point for the interpret CLI.
    1. Generate partial dependence plots.
    2. Export feature importance.
    3. Validate total plot size (T050).
    """
    logger.info("Starting Interpret Pipeline (T034)...")

    try:
        # Step 1: Generate Partial Dependence Plots
        logger.info("Generating partial dependence plots...")
        # The function signature from API surface is not fully detailed, 
        # but we call it as defined in the task description context.
        # Assuming it creates files in `results/`
        generate_partial_dependence_plots()
        logger.info("Partial dependence plots generated.")

        # Step 2: Export Feature Importance
        logger.info("Exporting feature importance...")
        export_feature_importance()
        logger.info("Feature importance exported.")

        # Step 3: Validate Plot Size (T050 / T034c)
        logger.info("Validating total plot size...")
        validate_plot_size(PLOT_DIR, PLOT_PATTERN)

        logger.info("Interpret pipeline completed successfully.")
        return 0

    except SystemExit as e:
        # Re-raise SystemExit to ensure the CLI fails with the specific message
        raise
    except Exception as e:
        logger.exception(f"Interpret pipeline failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
