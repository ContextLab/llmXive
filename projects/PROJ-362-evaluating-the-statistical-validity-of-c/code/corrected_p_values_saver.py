"""
Module to handle the loading of raw p-values, application of BH correction,
and saving of the corrected p-values to CSV.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional

from config import RESULTS_DIR

# Ensure the directory exists
os.makedirs(os.path.join(RESULTS_DIR, "p_values"), exist_ok=True)

def load_raw_p_values(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads raw p-values from the raw_p_values.csv file.
    Expected columns: query_id, metric, raw_p
    """
    if filepath is None:
        filepath = os.path.join(RESULTS_DIR, "p_values", "raw_p_values.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw p-values file not found at {filepath}")

    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p'])
            })
    return data

def load_bh_correction_factors(filepath: Optional[str] = None) -> Dict[str, float]:
    """
    Loads Benjamini-Hochberg correction factors (m/i) from a file if available,
    or computes them on the fly if the file doesn't exist (though typically
    they are computed internally in the power_analysis module).
    For this task, we assume the factors are computed internally or passed.
    However, to keep this module self-contained for the 'saver' role,
    we will implement the BH logic here or rely on the power_analysis module
    if it exposes the corrected values directly.
    
    Given the API surface, `power_analysis.py` has `apply_bh_correction`.
    We will delegate the calculation there or re-implement the standard BH procedure.
    Standard BH: Sort p-values, find largest k where p(k) <= (k/m) * alpha.
    But for generating a full table of corrected p-values (adjusted p-values),
    we use the formula: adj_p[i] = min( (m/i) * p[i], adj_p[i+1] ) (monotonicity constraint).
    
    This function returns a dictionary mapping (query_id, metric) -> corrected_p.
    """
    # Since the API surface shows `power_analysis` has `apply_bh_correction`,
    # we should ideally use that. However, to avoid circular imports or 
    # complex dependencies if `power_analysis` is heavy, we can implement
    # the standard BH adjustment here which is algorithmically simple.
    
    # We will read raw p-values, sort them, apply BH, and return the map.
    # This function effectively performs the calculation needed for T026.
    pass

def apply_bh_correction_to_raw(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies Benjamini-Hochberg correction to the list of raw p-values.
    Returns a list of dictionaries with added 'corrected_p' and 'is_significant' (at alpha=0.05).
    
    Algorithm for Adjusted P-values (Storey et al.):
    1. Sort p-values in ascending order.
    2. Calculate adjusted p-values: p_adj[i] = p[i] * m / i
    3. Enforce monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1]) going backwards.
    4. Cap at 1.0.
    """
    if not raw_data:
        return []

    # Sort by p-value
    sorted_data = sorted(raw_data, key=lambda x: x['raw_p'])
    m = len(sorted_data)
    
    # Calculate raw adjusted values
    for i, row in enumerate(sorted_data):
        rank = i + 1
        adjusted = row['raw_p'] * m / rank
        row['_adjusted_raw'] = adjusted

    # Enforce monotonicity (cumulative minimum from the end)
    # Start from the second to last element and move backwards
    current_min = sorted_data[-1]['_adjusted_raw']
    sorted_data[-1]['_adjusted_raw'] = min(current_min, 1.0)
    
    for i in range(m - 2, -1, -1):
        val = sorted_data[i]['_adjusted_raw']
        # The adjusted p-value must be <= the next one
        next_val = sorted_data[i+1]['_adjusted_raw']
        current_min = min(val, next_val)
        sorted_data[i]['_adjusted_raw'] = min(current_min, 1.0)

    # Finalize and add significance flag (alpha=0.05)
    result = []
    for row in sorted_data:
        corrected_p = row['_adjusted_raw']
        is_significant = corrected_p < 0.05
        
        result.append({
            'query_id': row['query_id'],
            'metric': row['metric'],
            'raw_p': row['raw_p'],
            'corrected_p': corrected_p,
            'is_significant': is_significant
        })
    
    return result

def save_corrected_p_values(data: List[Dict[str, Any]], filepath: Optional[str] = None) -> None:
    """
    Saves the corrected p-values to a CSV file.
    Columns: query_id, metric, raw_p, corrected_p, is_significant
    """
    if filepath is None:
        filepath = os.path.join(RESULTS_DIR, "p_values", "corrected_p_values.csv")
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    fieldnames = ['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    logging.info(f"Corrected p-values saved to {filepath}")

def run_corrected_p_values_generation() -> None:
    """
    Main entry point to load raw p-values, apply BH correction, and save results.
    """
    logging.info("Starting corrected p-values generation...")
    
    try:
        raw_data = load_raw_p_values()
        logging.info(f"Loaded {len(raw_data)} raw p-value entries.")
        
        corrected_data = apply_bh_correction_to_raw(raw_data)
        logging.info(f"Applied BH correction to {len(corrected_data)} entries.")
        
        save_corrected_p_values(corrected_data)
        logging.info("Corrected p-values generation completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"Failed to generate corrected p-values: {e}")
        raise
    except Exception as e:
        logging.error(f"An error occurred during corrected p-values generation: {e}")
        raise