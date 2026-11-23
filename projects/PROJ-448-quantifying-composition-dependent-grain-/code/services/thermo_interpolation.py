"""
Service for handling missing ternary interaction parameters in the open thermodynamic proxy.

Implements linear interpolation between binary endpoints using sklearn.linear_model.LinearRegression
and manages the NO_TERNARY_DATA flag in the output manifest.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.linear_model import LinearRegression
from errors import ThermodynamicError, ConfigurationError
from code.config import PROJECT_ROOT

# Configure logger
logger = logging.getLogger(__name__)

# Path to the manifest file
MANIFEST_PATH = PROJECT_ROOT / "data" / "data_manifest.json"

def load_binary_parameters(system_name: str, temperature: float) -> Dict[str, Any]:
    """
    Load binary interaction parameters for the given system and temperature.
    
    Args:
        system_name: Name of the binary system (e.g., "Fe-Cr", "Fe-Mo")
        temperature: Temperature in Kelvin
        
    Returns:
        Dictionary containing binary interaction parameters
        
    Raises:
        ThermodynamicError: If parameters cannot be loaded
    """
    # In a real implementation, this would query the thermodynamic proxy
    # For now, we assume parameters are available in a structured format
    # This is a placeholder that would be replaced with actual data fetching
    binary_params = {
        "Fe-Cr": {"L0": -0.02, "L1": 0.01, "L2": -0.005},
        "Fe-Mo": {"L0": -0.03, "L1": 0.015, "L2": -0.008},
        "Fe-V": {"L0": -0.025, "L1": 0.012, "L2": -0.006},
        "Fe-W": {"L0": -0.04, "L1": 0.02, "L2": -0.01},
        "Cr-Mo": {"L0": -0.015, "L1": 0.008, "L2": -0.004},
        "Cr-V": {"L0": -0.018, "L1": 0.009, "L2": -0.005},
        "Cr-W": {"L0": -0.035, "L1": 0.018, "L2": -0.009},
        "Mo-V": {"L0": -0.012, "L1": 0.006, "L2": -0.003},
        "Mo-W": {"L0": -0.022, "L1": 0.011, "L2": -0.006},
        "V-W": {"L0": -0.028, "L1": 0.014, "L2": -0.007},
    }
    
    if system_name in binary_params:
        return binary_params[system_name]
    else:
        raise ThermodynamicError(f"Binary parameters not found for system: {system_name}")

def interpolate_ternary_parameters(
    ternary_system: str, 
    temperature: float,
    binary_systems: List[str]
) -> Dict[str, Any]:
    """
    Perform linear interpolation between binary endpoints for missing ternary parameters.
    
    Args:
        ternary_system: Name of the ternary system (e.g., "Fe-Cr-Mo")
        temperature: Temperature in Kelvin
        binary_systems: List of binary systems that make up the ternary system
        
    Returns:
        Dictionary containing interpolated ternary interaction parameters
        
    Raises:
        ThermodynamicError: If interpolation fails or insufficient binary data
    """
    logger.warning(f"Missing ternary parameters for {ternary_system}. "
                  f"Performing linear interpolation between binary endpoints: {binary_systems}")
    
    # Extract binary parameters for each component system
    binary_data = []
    for binary_sys in binary_systems:
        try:
            params = load_binary_parameters(binary_sys, temperature)
            # Convert to a consistent format for regression
            binary_data.append({
                "system": binary_sys,
                "L0": params.get("L0", 0),
                "L1": params.get("L1", 0),
                "L2": params.get("L2", 0)
            })
        except ThermodynamicError as e:
            logger.warning(f"Could not load binary parameters for {binary_sys}: {e}")
            continue
    
    if len(binary_data) < 2:
        raise ThermodynamicError(
            f"Insufficient binary data for interpolation of {ternary_system}. "
            f"Need at least 2 binary systems, found {len(binary_data)}"
        )
    
    # Prepare data for linear regression
    # We'll use the binary system indices as features and parameter values as targets
    X = np.array([[i] for i in range(len(binary_data))])
    y_L0 = np.array([d["L0"] for d in binary_data])
    y_L1 = np.array([d["L1"] for d in binary_data])
    y_L2 = np.array([d["L2"] for d in binary_data])
    
    # Fit linear regression models for each parameter
    model_L0 = LinearRegression()
    model_L0.fit(X, y_L0)
    
    model_L1 = LinearRegression()
    model_L1.fit(X, y_L1)
    
    model_L2 = LinearRegression()
    model_L2.fit(X, y_L2)
    
    # Predict ternary parameters (using the midpoint of the binary range)
    # This is a simplified approach; in reality, we'd use composition-dependent interpolation
    ternary_index = (len(binary_data) - 1) / 2
    X_ternary = np.array([[ternary_index]])
    
    interpolated_params = {
        "L0": float(model_L0.predict(X_ternary)[0]),
        "L1": float(model_L1.predict(X_ternary)[0]),
        "L2": float(model_L2.predict(X_ternary)[0]),
        "interpolation_method": "linear_regression",
        "binary_sources": binary_systems,
        "temperature": temperature
    }
    
    logger.info(f"Interpolated ternary parameters for {ternary_system}: {interpolated_params}")
    
    return interpolated_params

def set_no_ternary_data_flag(ternary_system: str, reason: str = "Missing ternary parameters") -> bool:
    """
    Set the NO_TERNARY_DATA flag in the manifest for a specific ternary system.
    
    Args:
        ternary_system: Name of the ternary system
        reason: Reason for the flag
        
    Returns:
        True if flag was successfully set, False otherwise
    """
    try:
        if not MANIFEST_PATH.exists():
            logger.error(f"Manifest file not found: {MANIFEST_PATH}")
            return False
        
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        # Find the entry for the ternary system
        if "systems" not in manifest:
            manifest["systems"] = []
        
        system_found = False
        for i, system in enumerate(manifest["systems"]):
            if system.get("name") == ternary_system:
                manifest["systems"][i]["flags"] = manifest["systems"][i].get("flags", [])
                if "NO_TERNARY_DATA" not in manifest["systems"][i]["flags"]:
                    manifest["systems"][i]["flags"].append("NO_TERNARY_DATA")
                manifest["systems"][i]["flag_reason"] = reason
                system_found = True
                break
        
        if not system_found:
            # Add new system entry with flag
            manifest["systems"].append({
                "name": ternary_system,
                "flags": ["NO_TERNARY_DATA"],
                "flag_reason": reason
            })
        
        # Write updated manifest
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.warning(f"Set NO_TERNARY_DATA flag for {ternary_system} in manifest: {reason}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set NO_TERNARY_DATA flag for {ternary_system}: {e}")
        return False

def validate_and_interpolate_ternary(
    ternary_system: str,
    temperature: float,
    binary_systems: Optional[List[str]] = None
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate presence of ternary parameters and perform interpolation if missing.
    
    Args:
        ternary_system: Name of the ternary system
        temperature: Temperature in Kelvin
        binary_systems: Optional list of binary systems to use for interpolation
        
    Returns:
        Tuple of (success_flag, parameters_dict)
        - success_flag: True if parameters were found or successfully interpolated
        - parameters_dict: The ternary parameters (either original or interpolated)
    """
    # In a real implementation, this would check the thermodynamic proxy for ternary parameters
    # For this implementation, we assume ternary parameters are missing and need interpolation
    logger.info(f"Checking for ternary parameters in {ternary_system} at {temperature}K")
    
    # Simulate missing ternary parameters (in real implementation, this would be a check)
    ternary_params_missing = True
    
    if not ternary_params_missing:
        logger.info(f"Ternary parameters found for {ternary_system}")
        # In real implementation, return actual parameters
        return True, {"status": "found", "L0": 0.0, "L1": 0.0, "L2": 0.0}
    
    # Ternary parameters are missing, perform interpolation
    logger.warning(f"Ternary parameters missing for {ternary_system}. "
                  f"Will interpolate from binary endpoints.")
    
    # Determine binary systems if not provided
    if binary_systems is None:
        # Extract elements from ternary system name
        elements = ternary_system.replace("-", "").split("-")
        if len(elements) != 3:
            raise ConfigurationError(f"Invalid ternary system format: {ternary_system}")
        
        # Generate all binary combinations
        binary_systems = [
            f"{elements[0]}-{elements[1]}",
            f"{elements[0]}-{elements[2]}",
            f"{elements[1]}-{elements[2]}"
        ]
    
    try:
        interpolated_params = interpolate_ternary_parameters(
            ternary_system, 
            temperature, 
            binary_systems
        )
        
        # Set the NO_TERNARY_DATA flag in manifest
        flag_success = set_no_ternary_data_flag(
            ternary_system, 
            f"Interpolated from binary systems: {', '.join(binary_systems)}"
        )
        
        if not flag_success:
            logger.error(f"Failed to set NO_TERNARY_DATA flag for {ternary_system}")
            # Continue with interpolation but log the failure
        
        return True, interpolated_params
        
    except Exception as e:
        logger.error(f"Failed to interpolate ternary parameters for {ternary_system}: {e}")
        # Set flag even on failure
        set_no_ternary_data_flag(
            ternary_system, 
            f"Interpolation failed: {str(e)}"
        )
        return False, None

def main():
    """Main function to demonstrate ternary parameter interpolation."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    ternary_systems = ["Fe-Cr-Mo", "Fe-Cr-V", "Fe-Mo-V"]
    temperatures = [1000, 1200, 1400]
    
    for system in ternary_systems:
        for temp in temperatures:
            success, params = validate_and_interpolate_ternary(system, temp)
            if success:
                logger.info(f"Successfully processed {system} at {temp}K")
                logger.info(f"Parameters: {params}")
            else:
                logger.error(f"Failed to process {system} at {temp}K")

if __name__ == "__main__":
    main()
