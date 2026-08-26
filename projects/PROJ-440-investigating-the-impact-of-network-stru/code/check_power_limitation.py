"""
T028: Power limitation check implementation.

Verifies that the dataset size (samples) is sufficient for the number of predictors
using the rule: samples >= 10 * number_of_predictors.

If insufficient, halts execution and generates a warning file.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
POWER_RATIO_THRESHOLD = 10.0
NETWORKS_CSV_PATH = "data/raw/networks.csv"
ENERGY_CSV_PATH = "data/processed/energy_decay.csv"
WARNING_OUTPUT_PATH = "data/analysis/power_warning.txt"
ANALYSIS_DIR = "data/analysis"

def load_data():
    """Load the networks and energy decay datasets."""
    if not os.path.exists(NETWORKS_CSV_PATH):
        raise FileNotFoundError(
            f"Required file not found: {NETWORKS_CSV_PATH}. "
            "Ensure T015 (generate_networks.py) has been executed."
        )
    
    if not os.path.exists(ENERGY_CSV_PATH):
        raise FileNotFoundError(
            f"Required file not found: {ENERGY_CSV_PATH}. "
            "Ensure T026 (export_energy_results.py) has been executed."
        )

    networks_df = pd.read_csv(NETWORKS_CSV_PATH)
    energy_df = pd.read_csv(ENERGY_CSV_PATH)

    # Merge to ensure we are analyzing the same set of graphs
    # Join on 'id' from networks and 'graph_id' from energy
    merged_df = pd.merge(
        networks_df, 
        energy_df, 
        left_on='id', 
        right_on='graph_id', 
        how='inner'
    )

    if merged_df.empty:
        raise ValueError(
            "No matching records found between networks and energy data. "
            "Check ID columns and data integrity."
        )

    return merged_df

def get_predictor_count(df):
    """
    Determine the number of predictors (features) used in the analysis.
    
    Based on the project spec, the predictors are the topological metrics 
    computed in T013 (clustering, path_length, avg_degree, etc.).
    We exclude target variables and identifiers.
    """
    # Define known non-predictor columns
    exclude_cols = {
        'id', 'class', 'N', 'decay_rate', 'r_squared', 'status', 
        'graph_id', 'seed', 'timestamp'
    }
    
    # Identify predictor columns
    predictor_cols = [col for col in df.columns if col.lower() not in exclude_cols]
    
    # If the dataset is empty or has no predictors, handle gracefully
    if not predictor_cols:
        # Fallback: assume standard metrics if columns are missing but data exists
        # This handles cases where column names might differ slightly
        standard_metrics = ['clustering_coefficient', 'average_path_length', 
                            'average_degree', 'degree_distribution_std', 
                            'degree_distribution_kurtosis']
        # Check which standard metrics exist in the dataframe
        existing_metrics = [m for m in standard_metrics if m in df.columns]
        if existing_metrics:
            return len(existing_metrics), existing_metrics
        return 0, []
        
    return len(predictor_cols), predictor_cols

def check_power_limitation(df):
    """
    Perform the power limitation check.
    
    Returns:
        tuple: (is_sufficient: bool, samples: int, predictors: int, message: str)
    """
    n_samples = len(df)
    n_predictors, predictor_names = get_predictor_count(df)
    
    required_samples = n_predictors * POWER_RATIO_THRESHOLD
    is_sufficient = n_samples >= required_samples
    
    message = (
        f"Power Analysis Results:\n"
        f"  - Total Samples (N): {n_samples}\n"
        f"  - Number of Predictors (P): {n_predictors}\n"
        f"  - Required Samples (10*P): {required_samples}\n"
        f"  - Status: {'PASS' if is_sufficient else 'FAIL'}\n"
    )
    
    if not is_sufficient:
        message += (
            f"  - Deficit: {required_samples - n_samples} samples needed.\n"
            f"  - Predictors used: {predictor_names}\n"
            f"  - ACTION: HALTING EXECUTION. Please generate more network samples "
            f"or reduce the number of predictors."
        )
    else:
        message += (
            f"  - Power ratio: {n_samples / n_predictors:.2f} (Threshold: {POWER_RATIO_THRESHOLD})"
        )
        
    return is_sufficient, n_samples, n_predictors, message

def write_warning_message(message):
    """Write the warning message to the output file."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    with open(WARNING_OUTPUT_PATH, 'w') as f:
        f.write(message)
    logger.info(f"Warning file written to: {WARNING_OUTPUT_PATH}")

def main():
    parser = argparse.ArgumentParser(description="Check power limitation for regression analysis.")
    parser.add_argument('--force', action='store_true', help="Ignore power check and continue (not recommended).")
    args = parser.parse_args()

    logger.info("Starting power limitation check (Task T028)...")

    try:
        df = load_data()
        is_sufficient, samples, predictors, message = check_power_limitation(df)
        
        logger.info(message)
        
        if not is_sufficient:
            write_warning_message(message)
            logger.error("Power limitation check FAILED. Halting execution.")
            sys.exit(1)
        else:
            logger.info("Power limitation check PASSED. Proceeding with analysis.")
            # If we pass, we might want to log this to the state or analysis log, 
            # but the task specifically asks to halt if insufficient.
            # No warning file needed if passed.
            return 0

    except FileNotFoundError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during power check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
