"""
Task T022c: Write fitted parameters to data/processed/threshold_fit_params.json.

This module loads the fitted critical threshold parameters derived from the
sigmoid curve fitting (performed in T022a/T022b) and writes them to a persistent
JSON artifact.

It relies on the output of `fit_critical_threshold` from `fit_utils.py`.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_project_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_fitted_parameters(
    input_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load the fitted parameters from the raw threshold identification analysis.

    This function expects the output of T022b (analyze_threshold_identification),
    which should contain the fitted curve parameters (theta_c, slope, etc.)
    usually stored in a file like 'data/processed/threshold_identification_raw.json'.

    Args:
        input_path: Path to the raw identification JSON. Defaults to project config.

    Returns:
        Dictionary containing the fitted parameters and metadata.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file content is malformed or missing required keys.
    """
    paths = get_project_paths()
    if input_path is None:
        input_path = str(paths.processed / "threshold_identification_raw.json")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fitted parameters input file not found: {input_path}")

    logger.info(f"Loading fitted parameters from {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate structure based on expected output from fit_utils.analyze_threshold_identification
    if "fitted_params" not in data:
        raise ValueError(
            f"Input file {input_path} missing 'fitted_params' key. "
            "Ensure T022b has run successfully."
        )

    return data


def write_fit_parameters(
    data: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Write the fitted parameters to the final threshold_fit_params.json artifact.

    This function ensures the output directory exists and writes the data
    with proper formatting.

    Args:
        data: The dictionary containing fitted parameters (usually from load_fitted_parameters).
        output_path: Path for the output JSON file. Defaults to project config.

    Returns:
        The absolute path to the written file.

    Raises:
        IOError: If writing to disk fails.
    """
    paths = get_project_paths()
    if output_path is None:
        output_path = str(paths.processed / "threshold_fit_params.json")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing fitted parameters to {output_path}")

    # We might want to add a timestamp or version to the output for provenance
    output_data = {
        "artifact_name": "threshold_fit_params",
        "description": "Fitted critical threshold parameters (theta_c) and confidence intervals",
        "source": "threshold_identification_raw.json (T022b)",
        "fitted_params": data.get("fitted_params", {}),
        "metadata": {
            "fit_method": data.get("fit_method", "sigmoid_curve_fit"),
            "r_squared": data.get("r_squared"),
            "generated_at": data.get("timestamp")
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Successfully wrote parameters to {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for T022c.

    Executes the load and write sequence to persist the fitted parameters.
    """
    try:
        logger.info("Starting T022c: Write fitted parameters")
        
        # Load the intermediate results from T022b
        data = load_fitted_parameters()
        
        # Write the final artifact
        output_file = write_fit_parameters(data)
        
        logger.info(f"T022c completed successfully. Output: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        logger.error("Ensure T022b (analyze_threshold_identification) has run and produced threshold_identification_raw.json")
        raise
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T022c: {e}")
        raise


if __name__ == "__main__":
    main()