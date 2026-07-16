"""
Bias analysis: Calculate bias magnitude between recovered and ground-truth parameters.
Optimized for memory by using float32 for result arrays.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
import numpy as np
from config import DATA_RESULTS_DIR, DATA_METADATA_DIR, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def load_parameter_estimation_results(realization_id: str, algo_name: str) -> Dict[str, float]:
    """
    Loads parameter estimation results from a JSON file.
    """
    path = DATA_RESULTS_DIR / f"params_{realization_id}_{algo_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Parameter results not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Ensure float values are float32 if configured
    if FORCE_FLOAT32:
        for k, v in data.items():
            if isinstance(v, float):
                data[k] = np.float32(v)
    
    return data

def load_ground_truth_parameters(realization_id: str) -> Dict[str, float]:
    """
    Loads ground truth parameters from metadata.
    """
    path = DATA_METADATA_DIR / f"{realization_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Ground truth metadata not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Extract cosmological parameters
    params = {}
    for key in ['H0', 'Omega_m', 'n_s', 'tau']:
        if key in data:
            val = data[key]
            if FORCE_FLOAT32 and isinstance(val, float):
                params[key] = np.float32(val)
            else:
                params[key] = val
    return params

def calculate_bias(recovered: Dict[str, float], ground_truth: Dict[str, float]) -> Dict[str, float]:
    """
    Calculates the absolute bias for each parameter.
    """
    bias = {}
    for key in recovered.keys():
        if key in ground_truth:
            rec_val = float(recovered[key])
            gt_val = float(ground_truth[key])
            bias[key] = abs(rec_val - gt_val)
            if FORCE_FLOAT32:
                bias[key] = np.float32(bias[key])
    return bias

def run_bias_analysis(realization_ids: list, algo_names: list):
    """
    Runs bias analysis for a list of realizations and algorithms.
    Outputs results to a CSV file.
    """
    results = []
    
    for rid in realization_ids:
        for algo in algo_names:
            try:
                recovered = load_parameter_estimation_results(rid, algo)
                ground_truth = load_ground_truth_parameters(rid)
                bias = calculate_bias(recovered, ground_truth)
                
                row = {
                    "realization_id": rid,
                    "algorithm": algo,
                    **{f"bias_{k}": v for k, v in bias.items()}
                }
                results.append(row)
            except Exception as e:
                logger.error(f"Failed to process {rid} with {algo}: {e}")
    
    # Save to CSV
    output_path = DATA_RESULTS_DIR / "bias_summary.csv"
    if results:
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Bias analysis completed. Results saved to {output_path}")
    else:
        logger.warning("No bias results to save.")

def main():
    """
    Main entry point for bias analysis.
    """
    logging.basicConfig(level=logging.INFO)
    # Example: run_bias_analysis(['sim_001'], ['harmonic_interp'])
    logger.info("Bias analysis module loaded.")

if __name__ == "__main__":
    main()
