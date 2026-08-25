"""
Thermodynamic validation service for checking binary interaction parameters
in the open thermodynamic proxy and handling missing data via linear extrapolation.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from errors import ThermodynamicError, ConfigurationError

# Configure logger
logger = logging.getLogger(__name__)

def validate_binary_parameters(thermo_data: Dict[str, Any], system_name: str) -> Tuple[bool, List[str]]:
    """
    Validate the presence of binary interaction parameters in the thermodynamic data.

    Args:
        thermo_data: Dictionary containing thermodynamic parameters from the proxy.
        system_name: Name of the alloy system (e.g., 'Fe-Cr', 'Fe-Mo').

    Returns:
        Tuple of (is_valid, list of warnings).
    """
    warnings = []
    is_valid = True

    if not thermo_data or 'binary_parameters' not in thermo_data:
        is_valid = False
        warnings.append(f"No binary parameters found for system {system_name}")
        return is_valid, warnings

    binary_params = thermo_data['binary_parameters']
    if system_name not in binary_params:
        is_valid = False
        warnings.append(f"Binary parameters missing for {system_name} in thermo data")
        return is_valid, warnings

    params = binary_params[system_name]
    if not params or not any(params.values()):
        is_valid = False
        warnings.append(f"All binary parameters are empty/None for {system_name}")
        return is_valid, warnings

    return is_valid, warnings

def perform_linear_extrapolation(
    known_params: Dict[str, float],
    target_temperature: float,
    temp_range: Tuple[float, float]
) -> Dict[str, float]:
    """
    Perform linear extrapolation of missing binary parameters based on known
    temperature-dependent data points.

    Args:
        known_params: Dictionary of known parameter values at specific temperatures.
                      Keys are temperatures (float), values are parameter values (float).
        target_temperature: Temperature at which to extrapolate the parameter.
        temp_range: Tuple of (min_temp, max_temp) defining the valid range for extrapolation.

    Returns:
        Dictionary with extrapolated parameter values.

    Raises:
        ThermodynamicError: If extrapolation is not possible due to insufficient data.
    """
    if len(known_params) < 2:
        raise ThermodynamicError(
            f"Insufficient data points ({len(known_params)}) for linear extrapolation. "
            "At least 2 points are required."
        )

    temps = np.array(sorted(known_params.keys()))
    values = np.array([known_params[t] for t in temps])

    # Perform linear fit
    try:
        slope, intercept = np.polyfit(temps, values, 1)
        extrapolated_value = slope * target_temperature + intercept
    except Exception as e:
        raise ThermodynamicError(f"Linear extrapolation failed: {str(e)}")

    # Check if extrapolation is within reasonable bounds (optional safety check)
    if target_temperature < temp_range[0] or target_temperature > temp_range[1]:
        logger.warning(
            f"Extrapolating outside valid temperature range {temp_range}. "
            f"Target: {target_temperature} K"
        )

    return {"extrapolated_value": float(extrapolated_value), "method": "linear"}

def validate_and_extrapolate(
    thermo_data: Dict[str, Any],
    system_name: str,
    target_temperature: float,
    temp_range: Tuple[float, float],
    output_manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main validation function that checks for binary parameters, performs extrapolation
    if missing, and updates the manifest with flags.

    Args:
        thermo_data: Thermodynamic data from the proxy.
        system_name: Name of the alloy system.
        target_temperature: Temperature for which parameters are needed.
        temp_range: Valid temperature range for the system.
        output_manifest_path: Path to update the manifest with validation results.

    Returns:
        Dictionary containing validation results, extrapolated parameters, and flags.
    """
    result = {
        "system": system_name,
        "target_temperature": target_temperature,
        "is_valid": False,
        "has_binary_params": False,
        "extrapolated": False,
        "warnings": [],
        "parameters": None,
        "gap_flagged": False
    }

    # Step 1: Validate existing parameters
    is_valid, warnings = validate_binary_parameters(thermo_data, system_name)
    result["warnings"].extend(warnings)

    if is_valid:
        result["is_valid"] = True
        result["has_binary_params"] = True
        result["parameters"] = thermo_data['binary_parameters'][system_name]
        logger.info(f"Binary parameters validated for {system_name}")
        return result

    # Step 2: Attempt linear extrapolation if parameters are missing
    logger.warning(
        f"Binary parameters missing for {system_name}. "
        f"Attempting linear extrapolation with gap flag."
    )
    result["gap_flagged"] = True

    # Check if we have temperature-dependent data for extrapolation
    if 'temperature_dependent' in thermo_data and system_name in thermo_data['temperature_dependent']:
        known_params = thermo_data['temperature_dependent'][system_name]
        try:
            extrapolated = perform_linear_extrapolation(
                known_params, target_temperature, temp_range
            )
            result["extrapolated"] = True
            result["parameters"] = extrapolated
            result["warnings"].append(
                f"Linear extrapolation performed for {system_name} at {target_temperature}K"
            )
            logger.warning(
                f"Extrapolated binary parameters for {system_name}: {extrapolated}"
            )
        except ThermodynamicError as e:
            result["warnings"].append(f"Extrapolation failed: {str(e)}")
            logger.error(f"Extrapolation failed for {system_name}: {str(e)}")
    else:
        result["warnings"].append(
            f"No temperature-dependent data available for {system_name}. "
            "Extrapolation not possible."
        )
        logger.error(
            f"Cannot extrapolate binary parameters for {system_name}. "
            "No temperature-dependent data available."
        )

    # Step 3: Update manifest if path provided
    if output_manifest_path and result["gap_flagged"]:
        _update_manifest_with_gap(output_manifest_path, system_name, result)

    return result

def _update_manifest_with_gap(manifest_path: Path, system_name: str, result: Dict[str, Any]):
    """
    Update the data manifest to flag systems with extrapolated parameters.

    Args:
        manifest_path: Path to the manifest file.
        system_name: Name of the system with gaps.
        result: Validation result dictionary.
    """
    try:
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {"systems": {}, "metadata": {"created": str(datetime.now())}}

        if "systems" not in manifest:
            manifest["systems"] = {}

        manifest["systems"][system_name] = {
            "status": "extrapolated",
            "gap_flagged": True,
            "warnings": result["warnings"],
            "temperature": result["target_temperature"]
        }

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Updated manifest with gap flag for {system_name}")
    except Exception as e:
        logger.error(f"Failed to update manifest: {str(e)}")

def main():
    """
    Main entry point for validating binary parameters in the open thermodynamic proxy.
    This function demonstrates the validation workflow and can be run as a script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example usage with sample data
    sample_thermo_data = {
        "binary_parameters": {
            "Fe-Cr": {
                "L0": 15000.0,
                "L1": -2000.0,
                "L2": 500.0
            },
            # Missing Fe-Mo parameters to trigger extrapolation
        },
        "temperature_dependent": {
            "Fe-Mo": {
                1000.0: 12000.0,
                1200.0: 10000.0,
                1400.0: 8000.0
            }
        }
    }

    systems_to_check = ["Fe-Cr", "Fe-Mo"]
    target_temp = 1100.0
    temp_range = (900.0, 1500.0)

    for system in systems_to_check:
        result = validate_and_extrapolate(
            sample_thermo_data,
            system,
            target_temp,
            temp_range,
            output_manifest_path=Path("data/processed/thermo_validation_manifest.json")
        )
        logger.info(f"Validation result for {system}: {json.dumps(result, indent=2)}")

    logger.info("Thermodynamic validation completed.")

if __name__ == "__main__":
    main()
