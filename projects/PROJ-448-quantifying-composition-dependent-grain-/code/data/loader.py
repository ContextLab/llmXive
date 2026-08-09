"""
Data loader for thermodynamic and experimental data.

This module validates the presence of ternary interaction parameters in the
pycalphad/thermo-data TCFE9 proxy. It handles missing binary parameters via
linear extrapolation (with warnings) and flags missing ternary parameters
to delegate interaction calculation to the surrogate service (zero-interaction assumption).
"""
import os
import sys
from pathlib import Path
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Import existing error types
from errors import DataLoadError, ThermodynamicError

# Import existing config
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TCFE_PROXY_PATH = Path(config.PROJECT_ROOT) / "data" / "TCFE.tdb"
TERNARY_SYSTEMS = [
    ("Fe", "Cr", "Mo"),
    ("Fe", "Cr", "V"),
    ("Fe", "Cr", "W")
]

def _load_thermo_proxy() -> Dict[str, Any]:
    """
    Load the thermodynamic proxy database from the TDB file.
    
    Returns:
        Dict containing parsed thermodynamic parameters.
        
    Raises:
        ThermodynamicError: If the TDB file is missing or unreadable.
    """
    if not TCFE_PROXY_PATH.exists():
        raise ThermodynamicError(
            f"Thermodynamic proxy file not found at {TCFE_PROXY_PATH}. "
            "Run T006b to fetch the data first."
        )

    # For this implementation, we parse the TDB file manually or use pycalphad
    # Since pycalphad is a dependency, we use it to load the database
    try:
        from pycalphad import Database
        db = Database(str(TCFE_PROXY_PATH))
        
        # Extract parameters in a structured format
        parameters = {
            "phases": {},
            "models": {},
            "parameters": []
        }
        
        for phase_name, phase_obj in db.phases.items():
            parameters["phases"][phase_name] = {
                "sublattices": [str(s) for s in phase_obj.sublattices]
            }
        
        # Extract interaction parameters
        for param in db.parameters:
            param_dict = {
                "parameter_type": str(param.parameter_type),
                "phase_name": str(param.phase_name),
                "species": [str(s) for s in param.species],
                "order": int(param.order),
                "values": []
            }
            if hasattr(param, 'values') and param.values is not None:
                param_dict["values"] = [float(v) for v in param.values]
            
            parameters["parameters"].append(param_dict)
        
        return parameters
        
    except ImportError:
        raise ThermodynamicError(
            "pycalphad not installed. Install with: pip install pycalphad"
        )
    except Exception as e:
        raise ThermodynamicError(f"Failed to parse TDB file: {e}")

def _check_ternary_parameters(
    parameters: Dict[str, Any],
    system: Tuple[str, str, str]
) -> Tuple[bool, bool, str]:
    """
    Check for presence of binary and ternary interaction parameters.
    
    Args:
        parameters: Parsed thermodynamic parameters.
        system: Tuple of three elements (e.g., ("Fe", "Cr", "Mo")).
        
    Returns:
        Tuple of (has_binary, has_ternary, status_message)
    """
    element_a, element_b, element_c = sorted(system)
    
    has_binary = False
    has_ternary = False
    
    # Check for binary parameters (order 1, 2 species)
    for param in parameters["parameters"]:
        if param["order"] == 1 and len(param["species"]) == 2:
            species_set = set(param["species"])
            target_pairs = [
                {element_a, element_b},
                {element_a, element_c},
                {element_b, element_c}
            ]
            if species_set in target_pairs:
                has_binary = True
                break
    
    # Check for ternary parameters (order 1, 3 species)
    for param in parameters["parameters"]:
        if param["order"] == 1 and len(param["species"]) == 3:
            species_set = set(param["species"])
            if species_set == {element_a, element_b, element_c}:
                has_ternary = True
                break
    
    status = "OK"
    if not has_ternary:
        if not has_binary:
            status = "MISSING_BINARY_AND_TERNARY"
        else:
            status = "NO_TERNARY_DATA"
    
    return has_binary, has_ternary, status

def validate_thermo_parameters() -> Dict[str, Any]:
    """
    Validate the presence of ternary interaction parameters in the TCFE9 proxy.
    
    Behavior:
    1. If binary parameters are missing, perform linear extrapolation with warning.
    2. If ternary parameters are missing, flag as NO_TERNARY_DATA and delegate
       to surrogate_service.py (zero-interaction assumption).
    3. Explicitly uses 'thermo-data' source for determinism.
    
    Returns:
        Dict containing validation results for each ternary system.
        
    Raises:
        ThermodynamicError: If the proxy file is missing or invalid.
    """
    logger.info("Loading thermodynamic proxy from 'thermo-data' source...")
    parameters = _load_thermo_proxy()
    
    results = {
        "source": "pycalphad/thermo-data TCFE9",
        "systems": {},
        "flags": [],
        "warnings": []
    }
    
    for system in TERNARY_SYSTEMS:
        element_a, element_b, element_c = system
        system_key = f"{element_a}-{element_b}-{element_c}"
        
        has_binary, has_ternary, status = _check_ternary_parameters(
            parameters, system
        )
        
        system_result = {
            "has_binary_parameters": has_binary,
            "has_ternary_parameters": has_ternary,
            "status": status,
            "action": "PROCEED"
        }
        
        if status == "MISSING_BINARY_AND_TERNARY":
            system_result["action"] = "LINEAR_EXTRAPOLATION"
            results["warnings"].append(
                f"System {system_key}: Missing binary parameters. "
                "Using linear extrapolation with warning."
            )
        elif status == "NO_TERNARY_DATA":
            system_result["action"] = "ZERO_INTERACTION"
            results["flags"].append("NO_TERNARY_DATA")
            logger.warning(
                f"System {system_key}: No ternary interaction parameters found. "
                "Delegating to surrogate_service.py with zero-interaction assumption."
            )
        
        results["systems"][system_key] = system_result
    
    return results

def download_apt_data(accession_id, data_dir="data"):
    """Downloads APT data from NIST using the accession ID."""
    base_url = "https://nvl.nist.gov/data-explorer/api/"
    endpoint = f"datasets/{accession_id}/files"

    try:
        response = requests.get(base_url + endpoint)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if not data:
            print(f"No files found for accession ID: {accession_id}")
            return False

        for file in data:
            file_url = file["download_url"]
            filename = os.path.basename(file_url)
            filepath = Path(data_dir) / filename

            print(f"Downloading {filename} from {file_url} to {filepath}")
            response = requests.get(file_url, stream=True)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return True  # Successfully downloaded all files for this accession ID

    except requests.exceptions.RequestException as e:
        print(f"Error downloading data for accession ID {accession_id}: {e}")
        return False

def load_apt_data(accession_ids, data_dir="data"):
    """Loads APT data by attempting to download it from NIST."""
    success = True
    for accession_id in accession_ids:
        if not download_apt_data(accession_id, data_dir):
            success = False

    return success

def main():
    """
    Main entry point for validating thermodynamic parameters.
    
    This function:
    1. Validates the presence of ternary interaction parameters.
    2. Logs warnings for missing binary/ternary data.
    3. Writes validation results to data/processed/thermo_validation.json.
    """
    try:
        logger.info("Starting thermodynamic parameter validation for T047...")
        
        # Validate parameters
        validation_results = validate_thermo_parameters()
        
        # Write results to output file
        output_path = Path(config.PROJECT_ROOT) / "data" / "processed" / "thermo_validation.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Validation results written to {output_path}")
        
        # Print summary
        print("\n=== Thermodynamic Parameter Validation Summary ===")
        print(f"Source: {validation_results['source']}")
        print(f"Systems checked: {len(validation_results['systems'])}")
        print(f"Warnings: {len(validation_results['warnings'])}")
        print(f"Flags: {validation_results['flags']}")
        
        if validation_results['flags']:
            print("\n⚠️  WARNING: Missing ternary data detected.")
            print("   Interaction calculations will use zero-interaction assumption.")
        
        print("=" * 50)
        
    except ThermodynamicError as e:
        logger.error(f"Thermodynamic validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()