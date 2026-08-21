"""
Module to generate corrected p-values using Benjamini-Hochberg correction.
Reads raw p-values, applies BH correction per metric family, and saves results.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_p_values(raw_p_values_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load raw p-values from the CSV file generated in T018.
    
    Args:
        raw_p_values_path: Path to the raw p-values CSV. Defaults to RESULTS_DIR/p_values/raw_p_values.csv.
        
    Returns:
        List of dictionaries containing query_id, metric, and raw_p.
    """
    if raw_p_values_path is None:
        raw_p_values_path = os.path.join(RESULTS_DIR, "p_values", "raw_p_values.csv")
    
    if not os.path.exists(raw_p_values_path):
        raise FileNotFoundError(f"Raw p-values file not found at {raw_p_values_path}")
    
    raw_p_values = []
    with open(raw_p_values_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_p_values.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p'])
            })
    
    logger.info(f"Loaded {len(raw_p_values)} raw p-values from {raw_p_values_path}")
    return raw_p_values

def load_bh_correction_factors(metrics: List[str] = ["NDCG@10", "MAP"]) -> Dict[str, int]:
    """
    Load or calculate Benjamini-Hochberg correction factors.
    The factor is the number of tests in each metric family.
    
    Args:
        metrics: List of metric names to calculate factors for.
        
    Returns:
        Dictionary mapping metric name to the number of tests (queries) for that metric.
    """
    # We need to count how many queries exist for each metric.
    # Since we don't have the raw data here, we assume the raw_p_values file has all queries.
    # We'll load it temporarily to count.
    raw_p_values = load_raw_p_values()
    
    factors = {}
    for metric in metrics:
        count = sum(1 for item in raw_p_values if item['metric'] == metric)
        factors[metric] = count
        logger.info(f"BH correction factor for {metric}: {count} tests")
    
    return factors

def apply_bh_correction_to_raw(
    raw_p_values: List[Dict[str, Any]],
    metrics: List[str] = ["NDCG@10", "MAP"]
) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to raw p-values.
    
    The BH procedure:
    1. Sort p-values for each metric family in ascending order.
    2. For each p-value at rank i (1-indexed) out of m tests:
       corrected_p = (m / i) * raw_p
    3. Ensure corrected p-values are monotonically non-decreasing when sorted by rank.
    4. Clamp corrected p-values to [0, 1].
    
    Args:
        raw_p_values: List of dictionaries with query_id, metric, raw_p.
        metrics: List of metric families to correct separately.
        
    Returns:
        List of dictionaries with query_id, metric, raw_p, corrected_p.
    """
    if not raw_p_values:
        logger.warning("No raw p-values to correct.")
        return []

    # Group by metric
    grouped_by_metric = {metric: [] for metric in metrics}
    for item in raw_p_values:
        metric = item['metric']
        if metric in grouped_by_metric:
            grouped_by_metric[metric].append(item)
        else:
            logger.warning(f"Unknown metric {metric} found, skipping BH correction for this entry.")

    corrected_results = []
    
    for metric in metrics:
        items = grouped_by_metric[metric]
        if not items:
            continue
        
        m = len(items)  # Number of tests for this metric
        logger.info(f"Applying BH correction to {m} tests for metric {metric}")
        
        # Sort by raw p-value ascending
        items_sorted = sorted(items, key=lambda x: x['raw_p'])
        
        # Calculate raw corrected p-values
        for rank_idx, item in enumerate(items_sorted):
            i = rank_idx + 1  # 1-based rank
            corrected_p = (m / i) * item['raw_p']
            item['corrected_p_raw'] = corrected_p
        
        # Enforce monotonicity: iterate backwards and ensure p[i] <= p[i+1]
        # Since we sorted by raw p ascending, the corrected p should be non-decreasing by rank.
        # We need to ensure that if corrected_p[i] > corrected_p[i+1], we set corrected_p[i] = corrected_p[i+1]
        # Actually, the standard BH procedure ensures monotonicity by:
        # p_corrected[i] = min(p_corrected[i], p_corrected[i+1], ..., p_corrected[m])
        # We iterate from the largest rank down to 1.
        
        # First, clamp to 1.0
        for item in items_sorted:
            if item['corrected_p_raw'] > 1.0:
                item['corrected_p_raw'] = 1.0
            if item['corrected_p_raw'] < 0.0:
                item['corrected_p_raw'] = 0.0
        
        # Enforce monotonicity
        # We want corrected_p[rank] <= corrected_p[rank+1]
        # Iterate from m-1 down to 0
        for rank_idx in range(m - 2, -1, -1):
            if items_sorted[rank_idx]['corrected_p_raw'] > items_sorted[rank_idx + 1]['corrected_p_raw']:
                items_sorted[rank_idx]['corrected_p_raw'] = items_sorted[rank_idx + 1]['corrected_p_raw']
        
        # Store final corrected p
        for item in items_sorted:
            corrected_results.append({
                'query_id': item['query_id'],
                'metric': item['metric'],
                'raw_p': item['raw_p'],
                'corrected_p': item['corrected_p_raw']
            })
    
    logger.info(f"Applied BH correction to {len(corrected_results)} entries.")
    return corrected_results

def save_corrected_p_values(
    corrected_data: List[Dict[str, Any]],
    output_path: Optional[str] = None,
    alpha: float = 0.05
) -> str:
    """
    Save corrected p-values to CSV with significance determination.
    
    Args:
        corrected_data: List of dictionaries with query_id, metric, raw_p, corrected_p.
        output_path: Path to save the CSV. Defaults to RESULTS_DIR/p_values/corrected_p_values.csv.
        alpha: Significance threshold (default 0.05).
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "p_values", "corrected_p_values.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
        writer.writeheader()
        
        for item in corrected_data:
            is_significant = item['corrected_p'] <= alpha
            writer.writerow({
                'query_id': item['query_id'],
                'metric': item['metric'],
                'raw_p': f"{item['raw_p']:.6f}",
                'corrected_p': f"{item['corrected_p']:.6f}",
                'is_significant': str(is_significant)
            })
    
    logger.info(f"Saved {len(corrected_data)} corrected p-values to {output_path}")
    return output_path

def run_corrected_p_values_generation(
    raw_p_values_path: Optional[str] = None,
    output_path: Optional[str] = None,
    metrics: List[str] = ["NDCG@10", "MAP"],
    alpha: float = 0.05
) -> str:
    """
    Main entry point to generate corrected p-values.
    
    Args:
        raw_p_values_path: Path to raw p-values CSV.
        output_path: Path to save corrected p-values CSV.
        metrics: List of metrics to correct.
        alpha: Significance threshold.
        
    Returns:
        Path to the generated CSV file.
    """
    logger.info("Starting corrected p-values generation...")
    
    # Load raw p-values
    raw_p_values = load_raw_p_values(raw_p_values_path)
    
    # Apply BH correction
    corrected_data = apply_bh_correction_to_raw(raw_p_values, metrics)
    
    # Save results
    output_file = save_corrected_p_values(corrected_data, output_path, alpha)
    
    logger.info("Corrected p-values generation completed successfully.")
    return output_file

if __name__ == "__main__":
    # Example execution
    run_corrected_p_values_generation()
