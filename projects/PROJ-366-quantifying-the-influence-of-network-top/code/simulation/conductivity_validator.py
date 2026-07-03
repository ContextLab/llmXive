import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, get_paths
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_thermal_samples(conductivity_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all thermal sample JSON files from the conductivity directory.
    Returns a list of dictionaries containing sample metadata and conductivity.
    """
    samples = []
    if not conductivity_dir.exists():
        logger.warning(f"Conductivity directory does not exist: {conductivity_dir}")
        return samples

    for file_path in conductivity_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure it has the expected keys
                if 'conductivity' in data and 'sample_id' in data:
                    samples.append(data)
                else:
                    logger.warning(f"Skipping {file_path}: missing required keys")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    return samples

def validate_conductivity_range(
    conductivity_value: float, 
    min_val: float, 
    max_val: float
) -> bool:
    """
    Check if the conductivity value falls within the specified range.
    """
    return min_val <= conductivity_value <= max_val

def generate_convergence_report(
    samples: List[Dict[str, Any]], 
    min_val: float, 
    max_val: float,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a convergence report verifying that all computed thermal conductivities
    fall within the configurable range.
    """
    report = {
        "status": "success",
        "total_samples": len(samples),
        "valid_samples": 0,
        "invalid_samples": 0,
        "range": {
            "min": min_val,
            "max": max_val
        },
        "details": []
    }

    if not samples:
        report["status"] = "warning"
        report["message"] = "No thermal samples found to validate."
        logger.warning(report["message"])
        return report

    valid_count = 0
    invalid_count = 0

    for sample in samples:
        sample_id = sample.get("sample_id", "unknown")
        conductivity = sample.get("conductivity")
        
        detail = {
            "sample_id": sample_id,
            "conductivity": conductivity,
            "in_range": False
        }

        if conductivity is None:
            detail["error"] = "Missing conductivity value"
            invalid_count += 1
        elif validate_conductivity_range(conductivity, min_val, max_val):
            detail["in_range"] = True
            valid_count += 1
        else:
            detail["error"] = f"Value {conductivity} outside range [{min_val}, {max_val}]"
            invalid_count += 1

        report["details"].append(detail)

    report["valid_samples"] = valid_count
    report["invalid_samples"] = invalid_count

    if invalid_count > 0:
        report["status"] = "partial_failure"
        logger.warning(f"{invalid_count} samples outside expected range.")
    else:
        logger.info(f"All {valid_count} samples within expected range.")

    # Write report to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Convergence report written to {output_path}")
    return report

def main():
    """
    Main entry point for T026: Verify computed thermal conductivity output.
    """
    config = get_config()
    paths = get_paths()
    
    conductivity_dir = paths.get("processed_conductivities")
    if not conductivity_dir:
        # Fallback if path key is missing
        conductivity_dir = Path("data/processed/conductivities")
    
    # Get configurable range from config
    # Default to 0.5 - 5.0 W/mK for amorphous silicon as per typical literature
    # unless specified in config
    thermal_config = config.get("thermal_conductivity", {})
    min_val = thermal_config.get("min_valid_value", 0.5)
    max_val = thermal_config.get("max_valid_value", 5.0)
    
    logger.info(f"Validating conductivity range: [{min_val}, {max_val}]")
    logger.info(f"Scanning directory: {conductivity_dir}")

    samples = load_thermal_samples(conductivity_dir)
    
    output_path = conductivity_dir / "convergence_report.json"
    
    report = generate_convergence_report(
        samples, 
        min_val, 
        max_val, 
        output_path
    )

    # Exit with error code if critical failure (no samples or all invalid)
    if report["total_samples"] == 0:
        logger.error("No samples found to validate. Exiting with error.")
        sys.exit(1)
    elif report["invalid_samples"] == report["total_samples"]:
        logger.error("All samples are outside the valid range. Exiting with error.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
