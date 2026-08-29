import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output path as defined in T025
OUTPUT_PATH = Path("data/processed/correlation_results.json")

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file into a list of dictionaries.
    Handles various result CSV formats by looking for 'nodes_visited' and 'accuracy'/'status'.
    """
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}. Skipping.")
        return results

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_point_biserial(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate Point-Biserial correlation coefficient between 'nodes_visited' and reasoning success rate.
    
    Logic:
    1. Filter out tasks with invalid 'nodes_visited' or 'accuracy'.
    2. Determine 'success' (1) vs 'failure' (0) based on accuracy > 0.5 (or status == 'COMPLETED' and accuracy > 0).
       We use a strict threshold: accuracy > 0.5 implies success.
    3. Calculate point-biserial r between continuous variable (nodes_visited) and binary variable (success).
    
    Returns:
        dict containing r_value, p_value, n, and summary stats.
    """
    nodes_visited = []
    binary_success = []
    
    valid_count = 0
    skipped_count = 0

    for row in results:
        try:
            # Parse nodes_visited
            nodes_val = float(row.get('nodes_visited', 0))
            if nodes_val < 0:
                logger.warning(f"Invalid nodes_visited: {nodes_val} in row {row}")
                continue

            # Determine success
            # Prefer accuracy if available, else fallback to status
            acc_val = None
            if 'accuracy' in row:
                try:
                    acc_val = float(row['accuracy'])
                except (ValueError, TypeError):
                    acc_val = None
            
            status = row.get('status', '').upper()
            
            is_success = 0
            if acc_val is not None and not np.isnan(acc_val):
                # Threshold: > 0.5 accuracy is considered success
                if acc_val > 0.5:
                    is_success = 1
                else:
                    is_success = 0
            elif status == 'COMPLETED':
                # Fallback if accuracy missing but status is completed, assume success?
                # Or strictly require accuracy. Let's require accuracy > 0 for safety.
                # If we can't determine, skip.
                # Re-reading task: "reasoning success rate". Usually implies correct answer.
                # If no accuracy, we can't determine success rate reliably. Skip.
                skipped_count += 1
                continue
            else:
                is_success = 0
            
            nodes_visited.append(nodes_val)
            binary_success.append(is_success)
            valid_count += 1

        except Exception as e:
            logger.warning(f"Error processing row {row}: {e}")
            skipped_count += 1
            continue

    if len(nodes_visited) < 2:
        logger.error("Insufficient data points for correlation (need at least 2).")
        return {
            "r_value": None,
            "p_value": None,
            "n": valid_count,
            "skipped": skipped_count,
            "message": "Insufficient data points",
            "method": "point_biserial"
        }

    # Calculate Point-Biserial Correlation
    # scipy.stats.pointbiserialr(x, y) where x is binary, y is continuous
    # Or vice versa, correlation is symmetric.
    # We want correlation between nodes_visited (continuous) and success (binary).
    
    try:
        r, p = stats.pointbiserialr(binary_success, nodes_visited)
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}")
        return {
            "r_value": None,
            "p_value": None,
            "n": valid_count,
            "skipped": skipped_count,
            "message": f"Calculation error: {str(e)}",
            "method": "point_biserial"
        }

    # Interpretation
    # Positive r: More nodes visited correlates with success (harder tasks need more nodes?)
    # Negative r: Fewer nodes visited correlates with success (efficient retrieval?)
    
    summary = {
        "r_value": float(r),
        "p_value": float(p),
        "n": valid_count,
        "skipped": skipped_count,
        "method": "point_biserial",
        "description": "Correlation between nodes_visited and reasoning success (accuracy > 0.5)",
        "interpretation": "Positive r indicates more nodes visited with success; Negative r indicates fewer nodes with success."
    }
    
    if p < 0.05:
        summary["significance"] = "statistically_significant"
    else:
        summary["significance"] = "not_significant"

    return summary

def main():
    """
    Main entry point for T025.
    Aggregates results from baseline, lazy, and greedy runs to calculate correlation.
    """
    # Define input files based on task dependencies (T013, T019a, T019b)
    input_files = [
        "data/processed/baseline_results.csv",
        "data/processed/lazy_results.csv",
        "data/processed/greedy_results.csv",
        "data/processed/noisy_baseline_results.csv" # Optional, if exists
    ]

    all_results = []
    
    logger.info("Loading results from CSV files...")
    for file_path in input_files:
        if not Path(file_path).exists():
            logger.warning(f"Input file not found: {file_path}. Skipping.")
            continue
        
        rows = load_results_from_csv(file_path)
        logger.info(f"Loaded {len(rows)} rows from {file_path}")
        all_results.extend(rows)

    if not all_results:
        logger.error("No valid results found in any input file. Cannot compute correlation.")
        # Write empty/failed result to disk to satisfy "write real output" constraint
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump({
                "r_value": None,
                "p_value": None,
                "n": 0,
                "message": "No data found in input files",
                "method": "point_biserial"
            }, f, indent=2)
        return

    logger.info(f"Total valid rows collected: {len(all_results)}")
    
    # Calculate correlation
    result = calculate_point_biserial(all_results)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to disk
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Correlation results written to {OUTPUT_PATH}")
    logger.info(f"Result: r={result.get('r_value')}, p={result.get('p_value')}")

if __name__ == "__main__":
    main()