import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Configure logger for this module
logger = logging.getLogger("aggregate_results")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def aggregate_cv_results(cv_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates cross-validation results (R2 and RMSE per fold) into mean ± std dev.
    
    Args:
        cv_results: List of dictionaries, each containing 'r2' and 'rmse' keys.
                    Example: [{'r2': 0.45, 'rmse': 12.3}, {'r2': 0.41, 'rmse': 12.8}, ...]
    
    Returns:
        Dictionary with aggregated statistics:
        {
            "r2_mean": float,
            "r2_std": float,
            "rmse_mean": float,
            "rmse_std": float,
            "r2_interpretation": str (optional, if mean < 0.30)
        }
    """
    if not cv_results:
        logger.warning("No cross-validation results provided. Returning empty aggregation.")
        return {
            "r2_mean": 0.0,
            "r2_std": 0.0,
            "rmse_mean": 0.0,
            "rmse_std": 0.0,
            "r2_interpretation": "No data available for aggregation."
        }

    r2_values = [res['r2'] for res in cv_results]
    rmse_values = [res['rmse'] for res in cv_results]

    r2_mean = float(np.mean(r2_values))
    r2_std = float(np.std(r2_values))
    rmse_mean = float(np.mean(rmse_values))
    rmse_std = float(np.std(rmse_values))

    result = {
        "r2_mean": r2_mean,
        "r2_std": r2_std,
        "rmse_mean": rmse_mean,
        "rmse_std": rmse_std
    }

    # Add interpretation if R2 is weak (FR-008 logic from T023 context)
    if r2_mean < 0.30:
        result["r2_interpretation"] = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
        logger.info(f"R2 mean is {r2_mean:.4f} (< 0.30). Added interpretation.")
    else:
        logger.info(f"R2 mean is {r2_mean:.4f}. No weak prediction interpretation added.")

    return result

def save_aggregated_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Saves the aggregated results to a JSON file.
    
    Args:
        results: The dictionary returned by aggregate_cv_results.
        output_path: Path to the output JSON file (e.g., 'results/model_performance.json').
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Aggregated results saved to {output_file}")

def update_state_artifact_hash(file_path: str) -> None:
    """
    Computes SHA-256 checksum of the output file and updates the project state YAML.
    This satisfies Constitution Principle III (Data Hygiene) and V (Versioning Discipline).
    
    Args:
        file_path: Path to the file to checksum (model_performance.json).
    """
    import hashlib
    import yaml
    
    state_file_path = Path("state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml")
    
    if not file_path or not os.path.exists(file_path):
        logger.error(f"Cannot compute hash for non-existent file: {file_path}")
        return

    # Compute SHA-256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    logger.info(f"Computed checksum for {file_path}: {checksum}")

    # Load or create state file
    state_data = {}
    if state_file_path.exists():
        with open(state_file_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error reading state file: {e}")
                return
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Update the hash
    state_data["artifact_hashes"][str(file_path)] = checksum
    
    # Write atomically (write to temp, then rename)
    temp_path = state_file_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        os.replace(temp_path, state_file_path)
        logger.info(f"State file updated at {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        if temp_path.exists():
            temp_path.unlink()

def main():
    """
    Main entry point for T024.
    Reads CV results from a temporary file (produced by T023), aggregates them,
    saves to results/model_performance.json, and updates the state file.
    
    Expected input: code/cv_results_temp.json (created by T023)
    Output: results/model_performance.json
    """
    # Define paths
    input_path = "code/cv_results_temp.json"
    output_path = "results/model_performance.json"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. T023 may not have run or failed.")
        # If the input is missing, we cannot proceed. 
        # In a real pipeline, this would be a hard failure.
        # For now, we exit with error code 1.
        return 1

    # Load CV results
    with open(input_path, 'r') as f:
        cv_results = json.load(f)
    
    logger.info(f"Loaded {len(cv_results)} CV results from {input_path}")

    # Aggregate
    aggregated = aggregate_cv_results(cv_results)
    
    # Save
    save_aggregated_results(aggregated, output_path)
    
    # Update State
    update_state_artifact_hash(output_path)
    
    logger.info("T024 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
