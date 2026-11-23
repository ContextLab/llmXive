"""
Task T022c: Write fitted parameters to data/processed/threshold_fit_params.json.

This task consumes the output of the threshold identification process (specifically
data/processed/threshold_identification.json) and formats the fitted model parameters
(slope, intercept, and derived critical threshold theta_c) into a dedicated JSON artifact.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_project_paths

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_fitted_parameters(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the fitted parameters from the threshold identification output.

    Args:
        input_path: Path to the threshold_identification.json file.
                   If None, uses the default project path.

    Returns:
        Dictionary containing the fitted parameters.

    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the input file is not valid JSON.
    """
    if input_path is None:
        paths = get_project_paths()
        input_path = str(paths['processed'] / 'threshold_identification.json')

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded fitted parameters from {input_path}")
    return data

def write_fit_parameters(
    parameters: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Write the fitted parameters to the target JSON file.

    Args:
        parameters: The dictionary of fitted parameters.
        output_path: Path for the output file. If None, uses default.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = str(paths['processed'] / 'threshold_fit_params.json')

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # Prepare the output structure
    # We expect the input to contain 'model_params' (slope, intercept) and 'theta_c'
    output_data = {
        "task_id": "T022c",
        "description": "Fitted parameters for critical threshold identification",
        "model_type": "logistic_regression",
        "parameters": parameters.get("model_params", {}),
        "derived_values": {
            "theta_c": parameters.get("theta_c"),
            "confidence_interval": parameters.get("confidence_interval")
        },
        "metadata": {
            "fit_quality": parameters.get("fit_quality", {}),
            "timestamp": parameters.get("timestamp")
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Wrote fitted parameters to {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for Task T022c.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting Task T022c: Writing fitted parameters...")

        # Load the source data
        fitted_data = load_fitted_parameters()

        # Validate that required keys exist
        required_keys = ["model_params", "theta_c"]
        for key in required_keys:
            if key not in fitted_data:
                raise ValueError(f"Missing required key in input: {key}")

        # Write the formatted output
        output_path = write_fit_parameters(fitted_data)

        logger.info(f"Task T022c completed successfully. Output: {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())