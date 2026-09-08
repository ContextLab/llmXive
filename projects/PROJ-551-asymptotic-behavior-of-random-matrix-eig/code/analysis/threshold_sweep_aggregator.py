import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_threshold_identification_raw(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the raw threshold identification results (JSON) produced by T021c.
    Expected structure: a list of records containing theta, probability, theta_c, etc.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # If it's a single dict, wrap it
        if isinstance(data, dict):
            return [data]
        raise ValueError(f"Expected list of results, got {type(data)}")
    
    return data

def aggregate_sweep_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Aggregate the threshold identification results into a single CSV file.
    This creates the primary deliverable for T024.
    
    Expected fields in results:
    - N: matrix size
    - theta: perturbation strength
    - seed: random seed
    - theta_c: estimated critical threshold (if applicable)
    - probability: probability of outlier emergence
    - outlier_count: number of outliers detected
    - total_runs: total number of runs for this config
    """
    if not results:
        logger.warning("No results to aggregate. Creating empty CSV with headers.")
    
    # Define standard columns for the aggregated results
    fieldnames = [
        'N', 'theta', 'seed', 'theta_c', 'probability', 
        'outlier_count', 'total_runs', 'fit_status', 'residual_norm'
    ]
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for record in results:
            # Normalize record to ensure all expected fields exist
            row = {
                'N': record.get('N', 0),
                'theta': record.get('theta', 0.0),
                'seed': record.get('seed', 0),
                'theta_c': record.get('theta_c', None),
                'probability': record.get('probability', 0.0),
                'outlier_count': record.get('outlier_count', 0),
                'total_runs': record.get('total_runs', 0),
                'fit_status': record.get('fit_status', 'unknown'),
                'residual_norm': record.get('residual_norm', None)
            }
            writer.writerow(row)
    
    logger.info(f"Aggregated {len(results)} results to {output_path}")

def main():
    """
    Main entry point for T024: Generate aggregated results file.
    
    Input: data/processed/threshold_identification.json (produced by T021c)
    Output: data/processed/threshold_sweep_results.csv
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths relative to project root
    input_path = "data/processed/threshold_identification.json"
    output_path = "data/processed/threshold_sweep_results.csv"
    
    try:
        logger.info(f"Loading threshold identification results from {input_path}")
        results = load_threshold_identification_raw(input_path)
        
        logger.info(f"Aggregating {len(results)} results to {output_path}")
        aggregate_sweep_results_to_csv(results, output_path)
        
        logger.info("T024 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during aggregation: {e}")
        raise

if __name__ == "__main__":
    exit(main())
