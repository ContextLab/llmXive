"""
ThermoExtrapolator: Handles missing thermodynamic parameters in CALPHAD databases.
Implements linear extrapolation for missing parameters in the 500-900 K range.
Ensures thermodynamic consistency with TCFE9 trends.
"""

import logging
import numpy as np
from scipy.interpolate import interp1d
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from errors import ThermodynamicError, ConfigurationError

# Configure logger
logger = logging.getLogger(__name__)

# Constants for TCFE9 consistency checks
TCFE9_TEMP_RANGE = (500.0, 900.0)  # Kelvin
TCFE9_MAX_SLOPE = 0.001  # Max allowed slope for binary interaction parameters
TCFE9_MIN_VALUE = -0.1  # Min allowed value for interaction parameters (eV)
TCFE9_MAX_VALUE = 0.1   # Max allowed value for interaction parameters (eV)

def extrapolate_missing_parameters(
    parameters: Dict[str, List[Tuple[float, float]]],
    target_temps: List[float]
) -> Dict[str, List[float]]:
    """
    Extrapolate missing thermodynamic parameters using linear interpolation/extrapolation.
    
    Args:
        parameters: Dict mapping parameter names to list of (temp, value) tuples.
        target_temps: List of temperatures to extrapolate to.
        
    Returns:
        Dict mapping parameter names to extrapolated values at target_temps.
        
    Raises:
        ThermodynamicError: If extrapolation would violate TCFE9 trends.
    """
    result = {}
    
    for param_name, data_points in parameters.items():
        if not data_points:
            raise ThermodynamicError(f"No data points for parameter {param_name}")
        
        # Sort data points by temperature
        sorted_data = sorted(data_points, key=lambda x: x[0])
        temps = np.array([p[0] for p in sorted_data])
        values = np.array([p[1] for p in sorted_data])
        
        # Create interpolation function
        # Use linear interpolation for known range, extrapolate for missing
        if len(temps) < 2:
            # Single point: constant extrapolation
            interp_func = lambda t: values[0]
            logger.warning(f"Only one data point for {param_name}, using constant extrapolation")
        else:
            # Linear interpolation/extrapolation
            interp_func = interp1d(temps, values, kind='linear', fill_value="extrapolate")
        
        # Extrapolate to target temperatures
        extrapolated_values = []
        for temp in target_temps:
            val = float(interp_func(temp))
            
            # Thermodynamic consistency check
            if not _validate_tcf9_consistency(param_name, temp, val, values):
                raise ThermodynamicError(
                    f"Extrapolated value {val:.6f} at {temp}K for {param_name} "
                    f"violates TCFE9 trends"
                )
            
            extrapolated_values.append(val)
        
        result[param_name] = extrapolated_values
        logger.info(f"Extrapolated {param_name} for {len(target_temps)} temperatures")
    
    return result

def _validate_tcf9_consistency(
    param_name: str,
    temp: float,
    value: float,
    known_values: np.ndarray
) -> bool:
    """
    Validate that extrapolated values are consistent with TCFE9 trends.
    
    Args:
        param_name: Name of the parameter.
        temp: Temperature in Kelvin.
        value: Extrapolated value.
        known_values: Array of known values for slope calculation.
        
    Returns:
        True if consistent, False otherwise.
    """
    # Check value bounds
    if value < TCFE9_MIN_VALUE or value > TCFE9_MAX_VALUE:
        logger.warning(
            f"Value {value:.6f} for {param_name} at {temp}K outside TCFE9 bounds "
            f"[{TCFE9_MIN_VALUE}, {TCFE9_MAX_VALUE}]"
        )
        return False
    
    # Check temperature range
    if temp < TCFE9_TEMP_RANGE[0] or temp > TCFE9_TEMP_RANGE[1]:
        logger.warning(
            f"Temperature {temp}K outside TCFE9 range {TCFE9_TEMP_RANGE}"
        )
        # Allow extrapolation but warn
    
    # Check slope consistency
    if len(known_values) >= 2:
        # Calculate approximate slope from known values
        temp_range = TCFE9_TEMP_RANGE[1] - TCFE9_TEMP_RANGE[0]
        if temp_range > 0:
            avg_slope = (known_values[-1] - known_values[0]) / temp_range
            if abs(avg_slope) > TCFE9_MAX_SLOPE:
                logger.warning(
                    f"Slope {avg_slope:.6f} for {param_name} exceeds TCFE9 limit {TCFE9_MAX_SLOPE}"
                )
                return False
    
    return True

def handle_missing_binary_parameters(
    calphad_data: Dict[str, Any],
    missing_params: List[str]
) -> Dict[str, List[Tuple[float, float]]]:
    """
    Identify and prepare missing binary parameters for extrapolation.
    
    Args:
        calphad_data: Loaded CALPHAD database data.
        missing_params: List of parameter names that are missing.
        
    Returns:
        Dict mapping missing parameter names to their available data points.
    """
    available_data = {}
    
    for param in missing_params:
        if param in calphad_data:
            data_points = calphad_data[param]
            if isinstance(data_points, list) and len(data_points) > 0:
                available_data[param] = data_points
                logger.info(f"Found {len(data_points)} data points for {param}")
        else:
            logger.warning(f"No data available for missing parameter {param}")
    
    return available_data

def main():
    """
    Main function to execute and validate thermo_extrapolator on sample data.
    This task validates that extrapolated values are physically plausible.
    """
    logger.info("Starting thermo_extrapolator validation (T047c)")
    
    # Sample test data simulating missing CALPHAD parameters
    # Format: parameter_name -> [(temp_K, value_eV), ...]
    sample_parameters = {
        "Fe-Cr_L12": [(500, -0.02), (600, -0.018), (700, -0.015), (800, -0.012)],
        "Fe-Mo_L12": [(500, -0.025), (600, -0.022), (700, -0.018)],
        "Fe-V_L12": [(600, -0.01), (700, -0.008), (800, -0.005), (900, -0.002)],
        "Fe-W_L12": [(500, -0.03), (600, -0.028), (700, -0.025), (800, -0.022), (900, -0.02)]
    }
    
    # Target temperatures for extrapolation (including some outside the known range)
    target_temps = [450.0, 500.0, 550.0, 600.0, 650.0, 700.0, 750.0, 800.0, 850.0, 900.0, 950.0]
    
    logger.info(f"Testing extrapolation for parameters: {list(sample_parameters.keys())}")
    logger.info(f"Target temperatures: {target_temps}")
    
    try:
        # Perform extrapolation
        extrapolated_results = extrapolate_missing_parameters(sample_parameters, target_temps)
        
        # Validate results
        validation_passed = True
        for param, values in extrapolated_results.items():
            logger.info(f"\n{param}:")
            for temp, val in zip(target_temps, values):
                status = "OK"
                if val < TCFE9_MIN_VALUE or val > TCFE9_MAX_VALUE:
                    status = "OUT_OF_BOUNDS"
                    validation_passed = False
                logger.info(f"  {temp}K: {val:.6f} eV [{status}]")
        
        if validation_passed:
            logger.info("✓ All extrapolated values are physically plausible and consistent with TCFE9 trends")
            
            # Save validation results
            output_path = Path("data/processed/thermo_extrapolation_validation.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            validation_report = {
                "task_id": "T047c",
                "status": "success",
                "parameters_tested": list(sample_parameters.keys()),
                "target_temperatures": target_temps,
                "results": {
                    param: {
                        "temps": target_temps,
                        "values": values
                    }
                    for param, values in extrapolated_results.items()
                },
                "consistency_checks": {
                    "temp_range": TCFE9_TEMP_RANGE,
                    "value_bounds": [TCFE9_MIN_VALUE, TCFE9_MAX_VALUE],
                    "max_slope": TCFE9_MAX_SLOPE
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"✓ Validation report saved to {output_path}")
            return True
        else:
            logger.error("✗ Some extrapolated values failed consistency checks")
            return False
            
    except ThermodynamicError as e:
        logger.error(f"Thermodynamic consistency check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during extrapolation: {e}")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = main()
    exit(0 if success else 1)
