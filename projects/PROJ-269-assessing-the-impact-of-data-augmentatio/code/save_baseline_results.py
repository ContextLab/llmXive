import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

# Import from existing API surface
from analyze import load_simulation_results, calculate_error_rates, calculate_bootstrap_ci

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DISCLAIMER = "DISCLAIMER: Findings are associational and do not imply causation. Results are specific to the experimental conditions described."

def save_baseline_results(
    results_dir: Path,
    dataset_name: str,
    sample_size: int,
    simulation_results: Dict[str, Any],
    schema_path: Path
) -> None:
    """
    Saves baseline simulation results to JSON files for Null (Type I) and Alt (Type II) conditions.
    
    Args:
        results_dir: Directory where results will be saved.
        dataset_name: Name of the dataset (e.g., 'breast_cancer').
        sample_size: The subsample size used (e.g., 15).
        simulation_results: Dictionary containing 'null' and 'alt' simulation outputs.
        schema_path: Path to the validation schema (not used for saving, but kept for signature consistency).
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_slug = dataset_name.lower().replace('-', '_').replace(' ', '_')
    
    # Process Null Condition
    null_data = simulation_results.get('null', {})
    if not null_data:
        logger.warning(f"No null data found for {dataset_name}_{sample_size}, skipping.")
        return
        
    null_p_values = null_data.get('p_values', [])
    null_type1_error, null_ci = calculate_error_rates(null_p_values)
    
    null_output = {
        "metadata": {
            "dataset": dataset_slug,
            "sample_size": sample_size,
            "condition": "null",
            "type": "baseline",
            "iterations": len(null_p_values),
            "disclaimer": DISCLAIMER
        },
        "statistics": {
            "type_i_error_rate": float(null_type1_error),
            "confidence_interval_95": [float(null_ci[0]), float(null_ci[1])],
            "p_value_count": len(null_p_values),
            "p_value_min": float(min(null_p_values)) if null_p_values else None,
            "p_value_max": float(max(null_p_values)) if null_p_values else None,
            "p_value_mean": float(np.mean(null_p_values)) if null_p_values else None
        },
        "p_values": [float(p) for p in null_p_values]
    }
    
    null_path = results_dir / f"{dataset_slug}_{sample_size}_baseline_null.json"
    with open(null_path, 'w') as f:
        json.dump(null_output, f, indent=2)
    logger.info(f"Saved Null results to {null_path}")

    # Process Alt Condition
    alt_data = simulation_results.get('alt', {})
    if not alt_data:
        logger.warning(f"No alt data found for {dataset_name}_{sample_size}, skipping.")
        return

    alt_p_values = alt_data.get('p_values', [])
    alt_type2_error, alt_ci = calculate_error_rates(alt_p_values)
    
    alt_output = {
        "metadata": {
            "dataset": dataset_slug,
            "sample_size": sample_size,
            "condition": "alt",
            "type": "baseline",
            "iterations": len(alt_p_values),
            "disclaimer": DISCLAIMER
        },
        "statistics": {
            "type_ii_error_rate": float(alt_type2_error),
            "power": float(1 - alt_type2_error),
            "confidence_interval_95": [float(alt_ci[0]), float(alt_ci[1])],
            "p_value_count": len(alt_p_values),
            "p_value_min": float(min(alt_p_values)) if alt_p_values else None,
            "p_value_max": float(max(alt_p_values)) if alt_p_values else None,
            "p_value_mean": float(np.mean(alt_p_values)) if alt_p_values else None
        },
        "p_values": [float(p) for p in alt_p_values]
    }
    
    alt_path = results_dir / f"{dataset_slug}_{sample_size}_baseline_alt.json"
    with open(alt_path, 'w') as f:
        json.dump(alt_output, f, indent=2)
    logger.info(f"Saved Alt results to {alt_path}")

def main():
    parser = argparse.ArgumentParser(description="Save baseline simulation results to JSON.")
    parser.add_argument("--results-dir", type=str, required=True, help="Path to simulation results directory (contains run_*.json)")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to save output JSON files")
    parser.add_argument("--config", type=str, required=True, help="Path to JSON config file with dataset_name, sample_size, and schema_path")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    config_path = Path(args.config)
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    dataset_name = config.get('dataset_name')
    sample_size = config.get('sample_size')
    schema_path = Path(config.get('schema_path', 'contracts/simulation_schema.json'))
    
    if not dataset_name or not sample_size:
        logger.error("Config must contain 'dataset_name' and 'sample_size'.")
        return

    # Load simulation results (expects a single run file or aggregated structure)
    # Assuming the simulation.py saves a file like: results_dir / f"{dataset_name}_{sample_size}_run.json"
    # or the user provides a specific path. For this task, we assume the simulation output 
    # is passed via a specific file or we iterate. 
    # To be robust, we look for the most recent or specific run file matching the pattern.
    
    simulation_files = list(results_dir.glob(f"*{dataset_name}*{sample_size}*run*.json"))
    if not simulation_files:
        # Fallback: try to find any json in results_dir if pattern fails
        simulation_files = list(results_dir.glob("*.json"))
        
    if not simulation_files:
        logger.error(f"No simulation results found for {dataset_name} size {sample_size} in {results_dir}")
        return
        
    # Load the first matching file (assuming one run per config for this task)
    # In a real pipeline, we might aggregate multiple runs, but T007/T013 imply a single run per config for the loop.
    simulation_file = simulation_files[0]
    logger.info(f"Loading simulation results from {simulation_file}")
    
    with open(simulation_file, 'r') as f:
        raw_results = json.load(f)
        
    # The raw_results structure from simulation.py (T007) is expected to have 'null' and 'alt' keys
    # containing lists of p_values.
    save_baseline_results(
        results_dir=output_dir,
        dataset_name=dataset_name,
        sample_size=sample_size,
        simulation_results=raw_results,
        schema_path=schema_path
    )

if __name__ == "__main__":
    main()
