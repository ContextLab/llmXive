"""
Module to write ground-truth parameters to metadata JSON files.

This module reads ground-truth values from code/config.py and writes them
to data/metadata/{realization_id}.json with the required schema.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import from project configuration
try:
    from config import (
        H0_GROUND_TRUTH,
        OMEGA_M_GROUND_TRUTH,
        N_S_GROUND_TRUTH,
        TAU_GROUND_TRUTH,
        SIMULATION_SEED_BASE,
        DATA_METADATA_DIR,
        N_SIDE
    )
except ImportError:
    # Fallback for direct execution testing
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import (
        H0_GROUND_TRUTH,
        OMEGA_M_GROUND_TRUTH,
        N_S_GROUND_TRUTH,
        TAU_GROUND_TRUTH,
        SIMULATION_SEED_BASE,
        DATA_METADATA_DIR,
        N_SIDE
    )

# Import CAMB version getter
try:
    from simulation.generate_maps import get_camb_version
except ImportError:
    from code.simulation.generate_maps import get_camb_version

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_metadata_dir() -> Path:
    """Ensure the metadata output directory exists."""
    metadata_dir = Path(DATA_METADATA_DIR)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured metadata directory exists: {metadata_dir}")
    return metadata_dir


def get_ground_truth_parameters(
    realization_id: int,
    camb_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Construct the ground-truth parameters dictionary for a realization.
    
    Args:
        realization_id: Unique identifier for this simulation realization.
        camb_version: Optional CAMB version string. If None, will be fetched.
        
    Returns:
        Dictionary containing ground-truth parameters matching the schema:
        - realization_id (int)
        - H0 (float)
        - Omega_m (float)
        - n_s (float)
        - tau (float)
        - seed (int)
        - camb_version (str)
        - Nside (int)
        - generated_at (str) - ISO format timestamp
    """
    if camb_version is None:
        camb_version = get_camb_version()
    
    # Calculate seed for this realization
    seed = SIMULATION_SEED_BASE + realization_id
    
    params = {
        "realization_id": realization_id,
        "H0": H0_GROUND_TRUTH,
        "Omega_m": OMEGA_M_GROUND_TRUTH,
        "n_s": N_S_GROUND_TRUTH,
        "tau": TAU_GROUND_TRUTH,
        "seed": seed,
        "camb_version": camb_version,
        "Nside": N_SIDE,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    logger.debug(f"Ground-truth parameters for realization {realization_id}: {params}")
    return params


def write_ground_truth_metadata(
    realization_id: int,
    output_dir: Optional[Path] = None,
    camb_version: Optional[str] = None
) -> Path:
    """
    Write ground-truth parameters to a JSON file.
    
    Args:
        realization_id: Unique identifier for the realization.
        output_dir: Optional output directory. Defaults to DATA_METADATA_DIR.
        camb_version: Optional CAMB version. If None, fetched automatically.
        
    Returns:
        Path to the written metadata file.
        
    Raises:
        IOError: If the file cannot be written.
        ValueError: If realization_id is negative.
    """
    if realization_id < 0:
        raise ValueError(f"realization_id must be non-negative, got {realization_id}")
    
    if output_dir is None:
        output_dir = ensure_metadata_dir()
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct parameters
    params = get_ground_truth_parameters(realization_id, camb_version)
    
    # Write to file
    output_path = output_dir / f"{realization_id}.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2)
        
        logger.info(f"Successfully wrote ground-truth metadata to {output_path}")
        return output_path
        
    except IOError as e:
        logger.error(f"Failed to write metadata file {output_path}: {e}")
        raise IOError(f"Could not write metadata file {output_path}") from e


def validate_metadata_schema(params: Dict[str, Any]) -> bool:
    """
    Validate that a parameters dictionary contains all required keys.
    
    Required keys: realization_id, H0, Omega_m, n_s, tau, seed, camb_version
    
    Args:
        params: Dictionary to validate.
        
    Returns:
        True if all required keys are present, False otherwise.
    """
    required_keys = ["realization_id", "H0", "Omega_m", "n_s", "tau", "seed", "camb_version"]
    missing = [k for k in required_keys if k not in params]
    
    if missing:
        logger.warning(f"Missing required keys in metadata: {missing}")
        return False
    
    # Validate types
    if not isinstance(params["realization_id"], int):
        logger.warning(f"realization_id must be int, got {type(params['realization_id'])}")
        return False
        
    float_keys = ["H0", "Omega_m", "n_s", "tau"]
    for key in float_keys:
        if not isinstance(params[key], (int, float)):
            logger.warning(f"{key} must be numeric, got {type(params[key])}")
            return False
            
    if not isinstance(params["seed"], int):
        logger.warning(f"seed must be int, got {type(params['seed'])}")
        return False
        
    if not isinstance(params["camb_version"], str):
        logger.warning(f"camb_version must be str, got {type(params['camb_version'])}")
        return False
    
    return True


def main():
    """
    Command-line entry point for testing the metadata writer.
    
    Usage:
        python code/simulation/metadata_writer.py [--realization-id ID]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Write ground-truth parameters to metadata JSON."
    )
    parser.add_argument(
        "--realization-id",
        type=int,
        default=0,
        help="Realization ID to write metadata for (default: 0)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for metadata (default: from config)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        output_path = write_ground_truth_metadata(
            realization_id=args.realization_id,
            output_dir=output_dir
        )
        print(f"Metadata written to: {output_path}")
        
        # Validate the written file
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        if validate_metadata_schema(data):
            print("Schema validation: PASSED")
            print(f"Content: {json.dumps(data, indent=2)}")
        else:
            print("Schema validation: FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Error writing metadata: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())