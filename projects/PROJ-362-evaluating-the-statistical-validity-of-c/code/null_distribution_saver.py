"""
Module to save null distribution results to CSV files.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

def save_null_distribution_csv(
    result: Dict[str, Any],
    output_dir: Optional[str] = None
) -> str:
    """
    Save a single null distribution result to a CSV file.
    
    Args:
        result: Dictionary containing query_id, metric, null_distribution, N_actual.
        output_dir: Directory to save the file. Defaults to RESULTS_DIR/null_distributions.
    
    Returns:
        Path to the saved file.
    """
    if output_dir is None:
        ensure_dirs()
        output_dir = str(Path(RESULTS_DIR) / "null_distributions")
    
    os.makedirs(output_dir, exist_ok=True)
    
    query_id = result['query_id']
    metric = result['metric']
    filename = f"q{query_id}_{metric}.csv"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'score', 'permutation_index'])
        
        for idx, score in enumerate(result['null_distribution']):
            writer.writerow([query_id, metric, score, idx])
    
    logger.info(f"Saved null distribution for Query {query_id}, Metric {metric} to {filepath}")
    return filepath

def save_all_null_distributions(
    results: List[Dict[str, Any]],
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Save a list of null distribution results to CSV files.
    
    Args:
        results: List of result dictionaries.
        output_dir: Directory to save files.
    
    Returns:
        List of file paths saved.
    """
    if output_dir is None:
        ensure_dirs()
        output_dir = str(Path(RESULTS_DIR) / "null_distributions")
    
    saved_files = []
    for result in results:
        filepath = save_null_distribution_csv(result, output_dir)
        saved_files.append(filepath)
    
    logger.info(f"Saved {len(saved_files)} null distribution files.")
    return saved_files
