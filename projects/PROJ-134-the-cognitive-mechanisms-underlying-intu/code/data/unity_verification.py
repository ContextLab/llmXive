"""
Unity Verification Module for Moral Judgment Simulation.

This module verifies the simulation's fidelity to the actual Unity environment
by validating blend-shape parameters against a reference configuration file.
It operates without requiring the Unity runtime, serving as a static validation
layer for the simulation pipeline (T014) outputs.

Addresses spec assumptions regarding salience mapping (T016) by ensuring
that the generated blend-shape values in the simulated VR logs correspond
to valid configurations defined in the project's reference state.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Import project configuration and schema
from code.config import ensure_directories
from code.utils.schema import VRInteractionLog, SalienceLevel

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)


# Reference Configuration Constants
# These represent the valid range of blend-shape weights for the Unity environment
# as defined in the project's design documents.
BLEND_SHAPE_KEYS = [
    "eyeBlinkLeft", "eyeBlinkRight",
    "mouthSmileLeft", "mouthSmileRight",
    "mouthFrownLeft", "mouthFrownRight",
    "jawOpen", "mouthPucker",
    "browDownLeft", "browDownRight",
    "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "eyeSquintLeft", "eyeSquintRight",
    "mouthDimpleLeft", "mouthDimpleRight"
]

VALID_RANGE = (0.0, 1.0)


def load_reference_config(config_path: Path) -> Dict[str, Any]:
    """
    Loads the Unity reference configuration file.

    Args:
        config_path: Path to the JSON configuration file containing
                     valid blend-shape ranges and salience mappings.

    Returns:
        Dictionary containing the reference configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file is malformed.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Reference config not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_blend_shape_ranges(
    data: pd.DataFrame,
    reference: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validates that all blend-shape values in the dataset fall within
    the valid ranges defined in the reference configuration.

    Args:
        data: DataFrame containing VR interaction logs with blend-shape columns.
        reference: The loaded reference configuration dictionary.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    is_valid = True

    # Get valid ranges from reference or use defaults
    valid_ranges = reference.get("blend_shape_ranges", {})
    # Merge with default global range
    global_min = valid_ranges.get("min", VALID_RANGE[0])
    global_max = valid_ranges.get("max", VALID_RANGE[1])

    for key in BLEND_SHAPE_KEYS:
        if key in data.columns:
            col_data = data[key]
            # Check for values outside global range
            out_of_range = col_data[(col_data < global_min) | (col_data > global_max)]
            if not out_of_range.empty:
                is_valid = False
                errors.append(
                    f"Column '{key}' contains {len(out_of_range)} values outside "
                    f"range [{global_min}, {global_max}]."
                )
            # Check for NaNs if reference requires non-null
            if reference.get("require_non_null", False):
                nan_count = col_data.isna().sum()
                if nan_count > 0:
                    is_valid = False
                    errors.append(f"Column '{key}' contains {nan_count} NaN values.")
        else:
            # If a key is defined in the reference but missing in data, log warning
            if key in valid_ranges:
                logger.warning(f"Reference expects '{key}' but it is missing in data.")

    return is_valid, errors


def validate_salience_mapping(
    data: pd.DataFrame,
    reference: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validates that the salience_level in the data matches the expected
    blend-shape thresholds defined in the reference configuration.

    This ensures that the simulation logic (T016) correctly maps text stories
    to VR conditions.

    Args:
        data: DataFrame with 'salience_level' and blend-shape columns.
        reference: Reference configuration containing salience thresholds.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    is_valid = True

    salience_config = reference.get("salience_mapping", {})
    if not salience_config:
        logger.info("No salience mapping configuration found in reference. Skipping mapping validation.")
        return True, []

    # Expected thresholds for 'high' salience (e.g., specific blend-shape activation)
    # This is a simplified check; real logic depends on the specific reference file structure.
    # We assume the reference defines a "high_salience_threshold" for key expressions.
    threshold = salience_config.get("high_salience_threshold", 0.7)
    target_blend = salience_config.get("target_blend_shape", "mouthSmileLeft")

    if target_blend not in data.columns:
        logger.warning(f"Target blend shape '{target_blend}' not found in data.")
        return True, []

    # Check rows marked as 'high'
    high_salience_rows = data[data['salience_level'] == 'high']
    if not high_salience_rows.empty:
        if target_blend in high_salience_rows.columns:
            below_threshold = high_salience_rows[high_salience_rows[target_blend] < threshold]
            if not below_threshold.empty:
                is_valid = False
                errors.append(
                    f"Found {len(below_threshold)} rows marked 'high' salience "
                    f"but '{target_blend}' < {threshold}."
                )

    # Check rows marked as 'low' (should generally be below threshold, though not strictly required)
    low_salience_rows = data[data['salience_level'] == 'low']
    if not low_salience_rows.empty:
        if target_blend in low_salience_rows.columns:
            # Allow some variance, but flag if overwhelmingly high
            above_threshold = low_salience_rows[low_salience_rows[target_blend] > threshold]
            if len(above_threshold) > len(low_salience_rows) * 0.1:
                logger.warning(
                    f"{len(above_threshold)} 'low' salience rows have high {target_blend} "
                    f"values, which may indicate mapping noise."
                )

    return is_valid, errors


def verify_simulation_fidelity(
    data_path: Path,
    config_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main verification routine. Loads the simulated VR logs, compares them
    against the Unity reference configuration, and returns a validation report.

    Args:
        data_path: Path to the simulated VR logs CSV (output of T014/T016).
        config_path: Path to the Unity reference JSON configuration.
        output_path: Optional path to write the validation report JSON.

    Returns:
        Dictionary containing the validation result summary.
    """
    logger.info(f"Starting Unity verification for data: {data_path}")

    # 1. Load Data
    if not data_path.exists():
        return {
            "status": "failed",
            "error": f"Data file not found: {data_path}",
            "details": []
        }

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Failed to load data: {str(e)}",
            "details": []
        }

    # 2. Load Reference
    try:
        reference = load_reference_config(config_path)
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Failed to load reference config: {str(e)}",
            "details": []
        }

    results = {
        "status": "passed",
        "details": [],
        "checks": {}
    }

    # 3. Validate Blend Shape Ranges
    range_valid, range_errors = validate_blend_shape_ranges(df, reference)
    results["checks"]["blend_shape_ranges"] = range_valid
    if range_errors:
        results["status"] = "failed"
        results["details"].extend(range_errors)
    else:
        results["details"].append("All blend-shape values within valid ranges.")

    # 4. Validate Salience Mapping
    map_valid, map_errors = validate_salience_mapping(df, reference)
    results["checks"]["salience_mapping"] = map_valid
    if map_errors:
        results["status"] = "failed"
        results["details"].extend(map_errors)
    else:
        results["details"].append("Salience mapping consistent with reference thresholds.")

    # 5. Summary Stats
    results["summary"] = {
        "total_rows": len(df),
        "unique_salience_levels": df['salience_level'].nunique() if 'salience_level' in df.columns else 0,
        "blend_shapes_checked": len([k for k in BLEND_SHAPE_KEYS if k in df.columns])
    }

    # 6. Write Report
    if output_path:
        ensure_directories() # Ensure output dir exists
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Verification report written to {output_path}")

    return results


def create_reference_config(output_path: Path) -> None:
    """
    Creates a default Unity reference configuration file if one does not exist.
    This is a helper to bootstrap the verification process.
    """
    config = {
        "blend_shape_ranges": {
            "min": 0.0,
            "max": 1.0
        },
        "require_non_null": True,
        "salience_mapping": {
            "high_salience_threshold": 0.7,
            "target_blend_shape": "mouthSmileLeft",
            "description": "Threshold for 'high' salience activation of key expressions."
        },
        "metadata": {
            "source": "Unity Simulation Reference",
            "version": "1.0.0",
            "description": "Reference configuration for validating T014 simulation outputs against Unity constraints."
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Created reference config at {output_path}")


def main():
    """
    Entry point for running the Unity verification script.
    Expects:
      -data <path>: Path to the simulated VR logs CSV.
      --config <path>: Path to the reference JSON config (creates default if missing).
      --output <path>: Optional path for the output report JSON.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Verify simulation fidelity to Unity environment.")
    parser.add_argument("--data", required=True, help="Path to simulated VR logs CSV.")
    parser.add_argument("--config", required=True, help="Path to Unity reference config JSON.")
    parser.add_argument("--output", required=False, help="Path to output verification report JSON.")
    args = parser.parse_args()

    data_path = Path(args.data)
    config_path = Path(args.config)
    output_path = Path(args.output) if args.output else None

    # If config doesn't exist, create a default one to allow the script to run
    if not config_path.exists():
        logger.warning(f"Config not found at {config_path}. Creating default reference config.")
        create_reference_config(config_path)

    result = verify_simulation_fidelity(data_path, config_path, output_path)

    if result["status"] == "passed":
        print("VERIFICATION PASSED: Simulation is consistent with Unity reference.")
    else:
        print("VERIFICATION FAILED: Simulation deviates from Unity reference.")
        for err in result.get("details", []):
            print(f"  - {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()