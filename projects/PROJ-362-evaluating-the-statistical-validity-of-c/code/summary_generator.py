import os
import csv
import logging
from typing import List, Dict, Any, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_raw_p_values() -> List[Dict[str, Any]]:
    """Load raw p-values from results/p_values/raw_p_values.csv"""
    path = os.path.join(RESULTS_DIR, 'p_values', 'raw_p_values.csv')
    if not os.path.exists(path):
        logger.warning(f"Raw p-values file not found at {path}")
        return []
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p'])
            })
    return data

def load_corrected_p_values() -> List[Dict[str, Any]]:
    """Load corrected p-values from results/p_values/corrected_p_values.csv"""
    path = os.path.join(RESULTS_DIR, 'p_values', 'corrected_p_values.csv')
    if not os.path.exists(path):
        logger.warning(f"Corrected p-values file not found at {path}")
        return []
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p']),
                'corrected_p': float(row['corrected_p']),
                'is_significant': row['is_significant'].lower() == 'true'
            })
    return data

def load_mdes_summary() -> List[Dict[str, Any]]:
    """Load MDES summary from results/mdes/mdes_summary.csv"""
    path = os.path.join(RESULTS_DIR, 'mdes', 'mdes_summary.csv')
    if not os.path.exists(path):
        logger.warning(f"MDES summary file not found at {path}")
        return []
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'metric': row['metric'],
                'mdes': float(row['mdes']),
                'power': float(row['power']),
                'ci_width': float(row['ci_width'])
            })
    return data

def generate_summary_csv() -> str:
    """
    Generate results/summary.csv aggregating all query-metric pairs, 
    p-values, and MDES estimates.
    
    Output columns:
    query_id, metric, raw_p, corrected_p, is_significant, mdes, power, ci_width
    """
    raw_p_values = load_raw_p_values()
    corrected_p_values = load_corrected_p_values()
    mdes_summary = load_mdes_summary()
    
    # Create a lookup for MDES by metric
    mdes_lookup = {item['metric']: item for item in mdes_summary}
    
    # Create a lookup for corrected p-values by (query_id, metric)
    corrected_lookup = {}
    for item in corrected_p_values:
        key = (item['query_id'], item['metric'])
        corrected_lookup[key] = item
    
    # Aggregate data
    summary_rows = []
    for raw in raw_p_values:
        query_id = raw['query_id']
        metric = raw['metric']
        raw_p = raw['raw_p']
        
        key = (query_id, metric)
        corrected_item = corrected_lookup.get(key)
        
        if corrected_item:
            corrected_p = corrected_item['corrected_p']
            is_significant = corrected_item['is_significant']
        else:
            # Fallback if corrected p-values are missing for some reason
            corrected_p = raw_p
            is_significant = False
        
        # Get MDES for this metric
        mdes_item = mdes_lookup.get(metric)
        if mdes_item:
            mdes = mdes_item['mdes']
            power = mdes_item['power']
            ci_width = mdes_item['ci_width']
        else:
            mdes = None
            power = None
            ci_width = None
        
        summary_rows.append({
            'query_id': query_id,
            'metric': metric,
            'raw_p': raw_p,
            'corrected_p': corrected_p,
            'is_significant': is_significant,
            'mdes': mdes,
            'power': power,
            'ci_width': ci_width
        })
    
    # Ensure output directory exists
    output_dir = os.path.join(RESULTS_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'summary.csv')
    
    # Write summary CSV
    fieldnames = ['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant', 'mdes', 'power', 'ci_width']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)
    
    logger.info(f"Generated summary CSV at {output_path} with {len(summary_rows)} rows")
    return output_path

def run_summary_generation() -> str:
    """Entry point for generating the summary CSV."""
    logging.basicConfig(level=logging.INFO)
    return generate_summary_csv()

if __name__ == '__main__':
    run_summary_generation()
