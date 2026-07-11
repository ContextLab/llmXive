import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config/simulation.yaml") -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "seed": 42,
            "synthetic": {
                "n_samples": 1000,
                "n_features": 5,
                "means": [0, 1, 2],
                "variances": [1, 1, 1]
            },
            "null_hypothesis": {
                "n_samples": 1000,
                "n_features": 5
            },
            "output_dirs": {
                "synthetic": "data/corrupted/synthetic_grid",
                "null_hypothesis": "data/corrupted/null_hypothesis",
                "state": "state"
            },
            "schema_path": "contracts/result.schema.yaml"
        }
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def _compute_sha256(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the result schema for validation."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file {schema_path} not found. Skipping validation.")
        return {}
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a dictionary against a simple schema.
    This is a basic validator checking for expected keys and types.
    """
    if not schema:
        return True
    
    # Simple validation logic based on typical schema structure
    # Expected keys in result metadata: p_value, ci_bounds, effect_size, type_I_flag
    required_keys = ["p_value", "ci_bounds", "effect_size", "type_I_flag"]
    
    for key in required_keys:
        if key not in data:
            logger.warning(f"Missing required key in result metadata: {key}")
            return False
    
    # Type checks
    if not isinstance(data.get("p_value"), (int, float)):
        return False
    if not isinstance(data.get("ci_bounds"), list) or len(data.get("ci_bounds", [])) != 2:
        return False
    if not isinstance(data.get("effect_size"), (int, float)):
        return False
    if not isinstance(data.get("type_I_flag"), bool):
        return False
        
    return True

def generate_synthetic_dataset(config: Dict[str, Any], seed: int) -> pd.DataFrame:
    """Generate a synthetic dataset with known population parameters."""
    np.random.seed(seed)
    n_samples = config["synthetic"]["n_samples"]
    n_features = config["synthetic"]["n_features"]
    
    data = {}
    for i in range(n_features):
        mean = config["synthetic"]["means"][i % len(config["synthetic"]["means"])]
        var = config["synthetic"]["variances"][i % len(config["synthetic"]["variances"])]
        data[f"feature_{i}"] = np.random.normal(mean, np.sqrt(var), n_samples)
    
    df = pd.DataFrame(data)
    return df

def generate_null_hypothesis_dataset(config: Dict[str, Any], seed: int, source_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate a null-hypothesis dataset via label permutation or equal-mean simulation."""
    np.random.seed(seed)
    n_samples = config["null_hypothesis"]["n_samples"]
    n_features = config["null_hypothesis"]["n_features"]
    
    if source_df is not None:
        # Permutation approach: shuffle one column to break correlation
        df = source_df.copy()
        if len(df.columns) > 1:
            df[df.columns[-1]] = np.random.permutation(df[df.columns[-1]].values)
        else:
           df = pd.DataFrame({f"feature_{i}": np.random.normal(0, 1, n_samples) for i in range(n_features)})
    else:
        # Equal-mean simulation
        data = {}
        for i in range(n_features):
            data[f"feature_{i}"] = np.random.normal(0, 1, n_samples)
        df = pd.DataFrame(data)
    return df

def validate_and_record_artifact(
    filepath: str, 
    metadata: Dict[str, Any], 
    schema_path: str,
    state_file: str
) -> bool:
    """
    Validates an artifact against the result schema, computes checksum,
    and logs status to the state file.
    """
    logger.info(f"Validating artifact: {filepath}")
    
    # 1. Compute Checksum
    checksum = _compute_sha256(filepath)
    logger.info(f"Checksum computed: {checksum[:16]}...")
    
    # 2. Validate against schema
    schema = _load_schema(schema_path)
    is_valid = _validate_against_schema(metadata, schema)
    
    status = "valid" if is_valid else "invalid"
    logger.info(f"Validation status: {status}")
    
    if not is_valid:
        logger.error(f"Artifact {filepath} failed validation against schema.")
    
    # 3. Update State File
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    state_data["artifacts"][filepath] = {
        "checksum": checksum,
        "status": status,
        "validated_at": str(Path(filepath).stat().st_mtime),
        "metadata_keys": list(metadata.keys()) if metadata else []
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    return is_valid

def determine_iterations(config: Dict[str, Any]) -> int:
    """Determine the number of iterations based on convergence criteria."""
    # Placeholder implementation as per T030a requirement context
    return config.get("max_iterations", 100)

def run_simulation_loop(config: Dict[str, Any]) -> None:
    """Orchestrate the simulation loop, generating and validating artifacts."""
    # This is a placeholder for the full loop logic which depends on other tasks (T020-T022, T028a-d)
    # For T014, we focus on the validation logic integration.
    logger.info("Running simulation loop (validation focus)...")
    pass

def main() -> None:
    """Main entry point for simulate.py."""
    parser = argparse.ArgumentParser(description="Generate and validate synthetic/null datasets.")
    parser.add_argument("--config", type=str, default="config/simulation.yaml", help="Path to config file")
    parser.add_argument("--mode", type=str, choices=["synthetic", "null", "validate", "all"], default="all", help="Operation mode")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    args = parser.parse_args()

    config = load_config(args.config)
    
    output_dirs = config.get("output_dirs", {})
    synthetic_dir = output_dirs.get("synthetic", "data/corrupted/synthetic_grid")
    null_dir = output_dirs.get("null_hypothesis", "data/corrupted/null_hypothesis")
    state_dir = output_dirs.get("state", "state")
    schema_path = config.get("schema_path", "contracts/result.schema.yaml")
    state_file = os.path.join(state_dir, "simulation_artifacts.yaml")

    os.makedirs(synthetic_dir, exist_ok=True)
    os.makedirs(null_dir, exist_ok=True)
    os.makedirs(state_dir, exist_ok=True)

    if args.mode in ["synthetic", "all"]:
        logger.info("Generating synthetic datasets...")
        # Generate a sample synthetic dataset for validation demonstration
        seed = config.get("seed", 42)
        df_synthetic = generate_synthetic_dataset(config, seed)
        output_file = os.path.join(synthetic_dir, f"synthetic_seed_{seed}.csv")
        df_synthetic.to_csv(output_file, index=False)
        
        # Create a mock metadata result for validation (since full analysis isn't run here)
        # In a real flow, this metadata comes from T028a-d analysis results
        mock_metadata = {
            "p_value": 0.05,
            "ci_bounds": [0.1, 0.5],
            "effect_size": 0.4,
            "type_I_flag": False,
            "ground_truth_type": "population_parameters"
        }
        
        validate_and_record_artifact(output_file, mock_metadata, schema_path, state_file)

    if args.mode in ["null", "all"]:
        logger.info("Generating null hypothesis datasets...")
        seed = config.get("seed", 42) + 1
        df_null = generate_null_hypothesis_dataset(config, seed)
        output_file = os.path.join(null_dir, f"null_seed_{seed}.csv")
        df_null.to_csv(output_file, index=False)

        mock_metadata = {
            "p_value": 0.50,
            "ci_bounds": [-0.2, 0.2],
            "effect_size": 0.0,
            "type_I_flag": False,
            "ground_truth_type": "permutation"
        }
        
        validate_and_record_artifact(output_file, mock_metadata, schema_path, state_file)

    logger.info("Simulation and validation complete.")

if __name__ == "__main__":
    main()