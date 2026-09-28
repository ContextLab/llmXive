import os
import logging
from typing import List, Tuple

from utils.constants import get_seed
from utils.logger import get_logger, log_pipeline_step

# Minimum required visualization files as per SC-005
REQUIRED_VISUALIZATION_FILES = [
    "scatter_plot.png",
    "residuals.png"
]

def count_generated_visualizations(output_dir: str = "data/processed") -> Tuple[int, List[str], List[str]]:
    """
    Count the number of generated visualization files in the specified directory
    and validate against the minimum set requirement (SC-005).

    Args:
        output_dir: Path to the directory containing visualization files.

    Returns:
        Tuple containing:
            - count: Total number of expected visualization files found
            - found_files: List of filenames that were found
            - missing_files: List of filenames that were expected but missing

    Raises:
        FileNotFoundError: If the output directory does not exist.
    """
    if not os.path.exists(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    found_files = []
    missing_files = []

    logger = get_logger()
    log_pipeline_step(logger, "Starting visualization count validation")

    for filename in REQUIRED_VISUALIZATION_FILES:
        file_path = os.path.join(output_dir, filename)
        if os.path.exists(file_path):
            found_files.append(filename)
        else:
            missing_files.append(filename)

    count = len(found_files)
    total_required = len(REQUIRED_VISUALIZATION_FILES)

    logger.info(f"Visualization count validation: Found {count}/{total_required} required files")

    if missing_files:
        logger.warning(f"Missing required visualization files: {missing_files}")

    return count, found_files, missing_files

def validate_visualization_count(output_dir: str = "data/processed", min_count: int = None) -> bool:
    """
    Validate that the number of generated visualization files meets the minimum requirement.

    Args:
        output_dir: Path to the directory containing visualization files.
        min_count: Minimum number of files required. If None, uses the length of REQUIRED_VISUALIZATION_FILES.

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FileNotFoundError: If the output directory does not exist.
    """
    if min_count is None:
        min_count = len(REQUIRED_VISUALIZATION_FILES)

    count, found_files, missing_files = count_generated_visualizations(output_dir)

    if count < min_count:
        error_msg = (
            f"Visualization count validation failed: Found {count} files, "
            f"but minimum required is {min_count}. "
            f"Missing: {missing_files}"
        )
        raise FileNotFoundError(error_msg)

    return True

def main():
    """
    Main entry point for the visualization validation script.
    Validates that all required visualization files have been generated.
    """
    logger = get_logger()
    log_pipeline_step(logger, "Starting visualization validation")

    try:
        # Validate that all required files exist
        is_valid = validate_visualization_count()
        
        if is_valid:
            logger.info("Visualization validation PASSED: All required files are present")
            print("SUCCESS: All required visualization files generated.")
            return 0
        else:
            logger.error("Visualization validation FAILED")
            return 1
    except FileNotFoundError as e:
        logger.error(f"Visualization validation FAILED: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during visualization validation: {e}")
        print(f"ERROR: Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
