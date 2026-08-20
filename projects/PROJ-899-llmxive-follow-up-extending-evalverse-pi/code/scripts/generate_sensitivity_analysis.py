import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path if not already there
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.evaluate import load_sensitivity_sweep_data, calculate_stability_and_flip_rate, flag_threshold_sensitive, generate_sensitivity_analysis
from src.utils import get_logger, ensure_directories
from src.config import get_data_root

logger = get_logger(__name__)

def load_sensitivity_data(input_path: str) -> pd.DataFrame:
    """Wrapper to load sensitivity data with error handling."""
    try:
        return load_sensitivity_sweep_data(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load sensitivity data: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid sensitivity data format: {e}")
        sys.exit(1)

def main() -> int:
    """
    Script entry point to run T027 logic.
    Reads data/sensitivity_sweep_raw.csv and writes data/sensitivity_analysis.csv.
    """
    data_root = get_data_root()
    input_path = os.path.join(data_root, "sensitivity_sweep_raw.csv")
    output_path = os.path.join(data_root, "sensitivity_analysis.csv")

    logger.info(f"Starting sensitivity analysis generation.")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} does not exist. Ensure T026 has run.")
        return 1

    try:
        generate_sensitivity_analysis(input_path, output_path)
        logger.info("Sensitivity analysis generated successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())