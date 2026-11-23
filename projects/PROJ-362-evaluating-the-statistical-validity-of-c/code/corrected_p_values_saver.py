"""
Module for applying Benjamini-Hochberg correction to raw p-values.

This module implements the BH correction procedure separately for NDCG and MAP
p-value families as required by the project specification.
"""
import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_raw_p_values() -> List[Dict[str, Any]]:
    """
    Load raw p-values from the results/p_values/raw_p_values.csv file.
    
    Returns:
        List of dictionaries containing query_id, metric, and raw_p.
    """
    raw_p_values_path = RESULTS_DIR / "p_values" / "raw_p_values.csv"
    
    if not raw_p_values_path.exists():
        raise FileNotFoundError(f"Raw p-values file not found: {raw_p_values_path}")
    
    p_values = []
    with open(raw_p_values_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_values.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p'])
            })
    
    logger.info(f"Loaded {len(p_values)} raw p-values from {raw_p_values_path}")
    return p_values

def load_bh_correction_factors() -> Dict[str, float]:
    """
    Load BH correction factors (m) for each metric family.
    
    The BH correction factor is the total number of hypotheses tested
    within each family (metric).
    
    Returns:
        Dictionary mapping metric name to correction factor (m).
    """
    raw_p_values = load_raw_p_values()
    
    # Count hypotheses per metric family
    metric_counts = {}
    for pv in raw_p_values:
        metric = pv['metric']
        metric_counts[metric] = metric_counts.get(metric, 0) + 1
    
    logger.info(f"Found {len(metric_counts)} metric families with counts: {metric_counts}")
    return metric_counts

def apply_bh_correction_to_raw(
    raw_p_values: List[Dict[str, Any]],
    correction_factors: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to raw p-values.
    
    The BH procedure:
    1. Sort p-values in ascending order
    2. For each p-value at rank i (1-indexed), calculate adjusted p-value:
       p_adj = p * m / i
    3. Ensure monotonicity by taking cumulative minimum from largest to smallest
    4. Cap values at 1.0
    
    Applied separately for each metric family.
    
    Args:
        raw_p_values: List of dictionaries with query_id, metric, raw_p.
        correction_factors: Dictionary mapping metric to m (number of hypotheses).
        
    Returns:
        List of dictionaries with query_id, metric, raw_p, corrected_p, is_significant.
    """
    # Group by metric family
    families = {}
    for pv in raw_p_values:
        metric = pv['metric']
        if metric not in families:
            families[metric] = []
        families[metric].append(pv)
    
    corrected_results = []
    
    for metric, family_pvs in families.items():
        m = correction_factors.get(metric, len(family_pvs))
        
        # Sort by p-value (ascending)
        sorted_pvs = sorted(family_pvs, key=lambda x: x['raw_p'])
        
        # Calculate BH adjusted p-values
        # p_adj[i] = p[i] * m / (i + 1)  (using 0-indexed i, so rank is i+1)
        adjusted_pvs = []
        for i, pv in enumerate(sorted_pvs):
            rank = i + 1
            adjusted_p = pv['raw_p'] * m / rank
            adjusted_pvs.append({
                'query_id': pv['query_id'],
                'metric': pv['metric'],
                'raw_p': pv['raw_p'],
                'adjusted_p': adjusted_p,
                'rank': rank
            })
        
        # Enforce monotonicity: work from largest rank to smallest
        # p_adj[i] = min(p_adj[i], p_adj[i+1], ..., p_adj[m])
        cumulative_min = 1.0
        for i in range(len(adjusted_pvs) - 1, -1, -1):
            if adjusted_pvs[i]['adjusted_p'] < cumulative_min:
                cumulative_min = adjusted_pvs[i]['adjusted_p']
            else:
                adjusted_pvs[i]['adjusted_p'] = cumulative_min
            
            # Cap at 1.0
            adjusted_pvs[i]['adjusted_p'] = min(adjusted_pvs[i]['adjusted_p'], 1.0)
        
        corrected_results.extend(adjusted_pvs)
    
    # Sort back by query_id and metric for consistency
    corrected_results.sort(key=lambda x: (x['query_id'], x['metric']))
    
    logger.info(f"Applied BH correction to {len(corrected_results)} p-values across {len(families)} metric families")
    return corrected_results

def save_corrected_p_values(corrected_p_values: List[Dict[str, Any]]) -> None:
    """
    Save corrected p-values to results/p_values/corrected_p_values.csv.
    
    Args:
        corrected_p_values: List of dictionaries with query_id, metric, 
                           raw_p, corrected_p, is_significant.
    """
    output_path = RESULTS_DIR / "p_values" / "corrected_p_values.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pv in corrected_p_values:
            # Determine significance at alpha=0.05 (default)
            is_significant = pv['corrected_p'] < 0.05
            
            writer.writerow({
                'query_id': pv['query_id'],
                'metric': pv['metric'],
                'raw_p': f"{pv['raw_p']:.6f}",
                'corrected_p': f"{pv['corrected_p']:.6f}",
                'is_significant': is_significant
            })
    
    logger.info(f"Saved {len(corrected_p_values)} corrected p-values to {output_path}")

def run_corrected_p_values_generation() -> List[Dict[str, Any]]:
    """
    Main entry point for generating corrected p-values.
    
    This function orchestrates the full BH correction pipeline:
    1. Load raw p-values
    2. Calculate correction factors per metric family
    3. Apply BH correction
    4. Save results
    
    Returns:
        List of corrected p-value records.
    """
    logger.info("Starting BH correction pipeline")
    
    # Load raw p-values
    raw_p_values = load_raw_p_values()
    
    # Get correction factors (m for each metric family)
    correction_factors = load_bh_correction_factors()
    
    # Apply BH correction
    corrected_p_values = apply_bh_correction_to_raw(raw_p_values, correction_factors)
    
    # Save results
    save_corrected_p_values(corrected_p_values)
    
    logger.info("BH correction pipeline completed successfully")
    return corrected_p_values

def main():
    """Command-line entry point for BH correction."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_corrected_p_values_generation()
        logger.info(f"Generated {len(results)} corrected p-value records")
    except Exception as e:
        logger.error(f"Error in BH correction pipeline: {e}")
        raise

if __name__ == "__main__":
    main()