"""
Conductivity Validator (T026)

Verifies that computed thermal conductivity output files exist and contain
values within a configurable range defined in config.yaml.

Produces:
  data/processed/conductivities/convergence_report.json
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(get_paths()['logs_dir']) / 'conductivity_validator.log')
    ]
)
logger = logging.getLogger(__name__)


def load_thermal_samples(samples_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all ThermalSample JSON/Pickle files from the conductivities directory.
    Handles both .json and .pkl extensions.
    """
    samples = []
    if not samples_dir.exists():
        logger.error(f"Samples directory does not exist: {samples_dir}")
        return samples

    for file_path in samples_dir.iterdir():
        if file_path.suffix == '.json':
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    samples.append(data)
                    logger.debug(f"Loaded JSON sample: {file_path.name}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load JSON sample {file_path}: {e}")
        elif file_path.suffix == '.pkl':
            try:
                import pickle
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    samples.append(data)
                    logger.debug(f"Loaded PKL sample: {file_path.name}")
            except (pickle.UnpicklingError, IOError) as e:
                logger.warning(f"Failed to load PKL sample {file_path}: {e}")
        else:
            logger.debug(f"Ignoring non-data file: {file_path}")

    logger.info(f"Loaded {len(samples)} thermal samples from {samples_dir}")
    return samples


def validate_conductivity_range(
    samples: List[Dict[str, Any]],
    min_val: float,
    max_val: float
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate that each sample's conductivity is within [min_val, max_val].
    Returns (valid_samples, invalid_samples).
    """
    valid = []
    invalid = []

    for sample in samples:
        sample_id = sample.get('graph_id', 'unknown')
        conductivity = sample.get('conductivity')
        converged = sample.get('converged', False)

        # Check convergence first
        if not converged:
            invalid.append({
                'sample_id': sample_id,
                'reason': 'not_converged',
                'conductivity': conductivity,
                'converged': converged
            })
            logger.warning(f"Sample {sample_id} marked as not converged. Excluding.")
            continue

        if conductivity is None:
            invalid.append({
                'sample_id': sample_id,
                'reason': 'missing_conductivity',
                'conductivity': conductivity,
                'converged': converged
            })
            logger.warning(f"Sample {sample_id} has no conductivity value.")
            continue

        if not isinstance(conductivity, (int, float)):
            invalid.append({
                'sample_id': sample_id,
                'reason': 'invalid_type',
                'conductivity': conductivity,
                'converged': converged
            })
            logger.warning(f"Sample {sample_id} has non-numeric conductivity: {type(conductivity)}")
            continue

        if min_val <= conductivity <= max_val:
            valid.append(sample)
            logger.info(f"Sample {sample_id} conductivity {conductivity:.4f} W/mK is valid.")
        else:
            invalid.append({
                'sample_id': sample_id,
                'reason': 'out_of_range',
                'conductivity': conductivity,
                'converged': converged,
                'range': [min_val, max_val]
            })
            logger.warning(f"Sample {sample_id} conductivity {conductivity:.4f} W/mK is out of range [{min_val}, {max_val}].")

    return valid, invalid


def generate_convergence_report(
    valid_samples: List[Dict[str, Any]],
    invalid_samples: List[Dict[str, Any]],
    min_val: float,
    max_val: float,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the final convergence report JSON.
    """
    total = len(valid_samples) + len(invalid_samples)

    report = {
        "total_samples_processed": total,
        "valid_samples_count": len(valid_samples),
        "invalid_samples_count": len(invalid_samples),
        "valid_samples": [s.get('graph_id') for s in valid_samples],
        "invalid_samples": invalid_samples,
        "config_range": {
            "min": min_val,
            "max": max_val
        },
        "all_converged_and_in_range": len(invalid_samples) == 0 and len(valid_samples) > 0
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Convergence report written to {output_path}")
    return report


def main() -> int:
    """
    Main entry point for T026.
    """
    config = get_config()
    paths = get_paths()

    # Get configurable range from config
    # Expected in config.yaml under simulation.conductivity_range
    sim_config = config.get('simulation', {})
    range_config = sim_config.get('conductivity_range', {})
    min_val = float(range_config.get('min', 1.0))
    max_val = float(range_config.get('max', 150.0))

    logger.info(f"Validating conductivity range: [{min_val}, {max_val}] W/mK")

    samples_dir = Path(paths['conductivities_dir'])
    output_path = Path(paths['conductivities_dir']) / 'convergence_report.json'

    # Load samples
    samples = load_thermal_samples(samples_dir)
    if not samples:
        logger.error("No thermal samples found. Cannot generate report.")
        # Still write a report indicating failure
        generate_convergence_report([], [], min_val, max_val, output_path)
        return 1

    # Validate
    valid, invalid = validate_conductivity_range(samples, min_val, max_val)

    # Generate report
    report = generate_convergence_report(valid, invalid, min_val, max_val, output_path)

    if report['all_converged_and_in_range']:
        logger.info("SUCCESS: All samples converged and within range.")
        return 0
    else:
        logger.warning(f"VALIDATION FAILED: {len(invalid)} samples failed validation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())