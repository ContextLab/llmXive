"""
Aggregator for threshold sweep results.

This module loads threshold identification raw data and Monte Carlo results,
aggregates them into a single CSV file for downstream analysis and visualization.
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from utils.config import get_project_paths
from analysis.threshold_identification_raw import load_mc_results, aggregate_by_theta
from analysis.monte_carlo_runner import run_single_mc_iteration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_threshold_identification_raw(
    input_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load the raw threshold identification data from the Monte Carlo results.
    
    Args:
        input_path: Path to threshold_identification_raw.json. If None, uses default path.
        
    Returns:
        Dictionary containing aggregated threshold identification data.
    """
    if input_path is None:
        project_paths = get_project_paths()
        input_path = project_paths['processed'] / 'threshold_identification_raw.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Threshold identification raw file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded threshold identification raw data from {input_path}")
    return data


def aggregate_sweep_results_to_csv(
    input_data: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Aggregate sweep results into a CSV file.
    
    This function combines data from Monte Carlo runs and threshold identification
    analysis into a single CSV file with the following columns:
    - run_id: Unique identifier for the simulation run
    - N: Matrix size
    - theta: Perturbation strength
    - seed: Random seed used
    - outlier_count: Number of outliers detected
    - max_eigenvalue: Maximum eigenvalue observed
    - outlier_probability: Probability of outlier emergence (from aggregation)
    - fitted_theta_c: Fitted critical threshold (if available)
    
    Args:
        input_data: Pre-loaded threshold identification data. If None, loads from default path.
        output_path: Path for output CSV. If None, uses default path.
        
    Returns:
        Path to the generated CSV file.
    """
    project_paths = get_project_paths()
    
    if input_data is None:
        input_data = load_threshold_identification_raw()
    
    if output_path is None:
        output_path = project_paths['processed'] / 'threshold_sweep_results.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load Monte Carlo results for additional details
    mc_results_path = project_paths['processed'] / 'mc_results.csv'
    mc_data = []
    if mc_results_path.exists():
        with open(mc_results_path, 'r') as f:
            reader = csv.DictReader(f)
            mc_data = list(reader)
    
    # Prepare aggregated data
    aggregated_data = []
    
    # Process aggregated threshold data
    if 'aggregated_by_theta' in input_data:
        for theta_key, theta_data in input_data['aggregated_by_theta'].items():
            theta_val = float(theta_key)
            N_val = theta_data.get('N', 0)
            total_runs = theta_data.get('total_runs', 0)
            outlier_runs = theta_data.get('outlier_runs', 0)
            prob_outlier = theta_data.get('probability_outlier', 0.0)
            
            # Find matching MC results for this theta and N
            matching_mc = [
                row for row in mc_data
                if float(row['theta']) == theta_val and int(row['N']) == N_val
            ]
            
            for mc_row in matching_mc:
                aggregated_data.append({
                    'run_id': mc_row.get('run_id', ''),
                    'N': int(mc_row.get('N', N_val)),
                    'theta': theta_val,
                    'seed': int(mc_row.get('seed', 0)),
                    'outlier_count': int(mc_row.get('outlier_count', 0)),
                    'max_eigenvalue': float(mc_row.get('max_eigenvalue', 0.0)),
                    'outlier_probability': prob_outlier,
                    'total_runs_at_config': total_runs,
                    'outlier_runs_at_config': outlier_runs
                })
    
    # Write to CSV
    fieldnames = [
        'run_id', 'N', 'theta', 'seed', 'outlier_count', 'max_eigenvalue',
        'outlier_probability', 'total_runs_at_config', 'outlier_runs_at_config'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated_data)
    
    logger.info(f"Aggregated {len(aggregated_data)} records to {output_path}")
    return output_path


def main():
    """
    Main entry point for the threshold sweep aggregation.
    
    This function orchestrates the loading of raw threshold identification data
    and Monte Carlo results, then aggregates them into a single CSV file.
    """
    logger.info("Starting threshold sweep aggregation...")
    
    try:
        # Load and aggregate results
        output_path = aggregate_sweep_results_to_csv()
        
        logger.info(f"Successfully aggregated results to {output_path}")
        
        # Verify output file exists and has content
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"Output file size: {file_size} bytes")
            
            if file_size == 0:
                logger.warning("Output file is empty - check input data sources")
            else:
                logger.info("Aggregation completed successfully")
        else:
            logger.error("Output file was not created")
            return 1
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during aggregation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())