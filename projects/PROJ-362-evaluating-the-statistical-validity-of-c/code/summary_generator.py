import os
import csv
import logging
from typing import List, Dict, Any, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_raw_p_values() -> List[Dict[str, Any]]:
    """Load raw p-values from results/p_values/raw_p_values.csv."""
    path = os.path.join(RESULTS_DIR, "p_values", "raw_p_values.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw p-values file not found: {path}")
    
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p'])
            })
    return rows

def load_corrected_p_values() -> List[Dict[str, Any]]:
    """Load corrected p-values from results/p_values/corrected_p_values.csv."""
    path = os.path.join(RESULTS_DIR, "p_values", "corrected_p_values.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Corrected p-values file not found: {path}")
    
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p']),
                'corrected_p': float(row['corrected_p']),
                'is_significant': row['is_significant'] == 'True'
            })
    return rows

def load_mdes_summary() -> List[Dict[str, Any]]:
    """Load MDES summary from results/mdes/mdes_summary.csv."""
    path = os.path.join(RESULTS_DIR, "mdes", "mdes_summary.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"MDES summary file not found: {path}")
    
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'metric': row['metric'],
                'mdes': float(row['mdes']),
                'power': float(row['power']),
                'ci_width': float(row['ci_width'])
            })
    return rows

def generate_summary_csv(
    raw_p_values: List[Dict[str, Any]],
    corrected_p_values: List[Dict[str, Any]],
    mdes_summary: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Aggregate all query-metric pairs, p-values, and MDES into a single summary CSV.
    
    Columns:
    - query_id
    - metric
    - raw_p
    - corrected_p
    - is_significant
    - mdes (metric-specific)
    - power (metric-specific)
    - ci_width (metric-specific)
    """
    # Index MDES by metric for quick lookup
    mdes_map = {m['metric']: m for m in mdes_summary}
    
    # Use corrected p-values as the primary source (they contain all needed info)
    # Merge with MDES data
    aggregated_rows = []
    for cpv in corrected_p_values:
        metric = cpv['metric']
        mdes_data = mdes_map.get(metric, {'mdes': None, 'power': None, 'ci_width': None})
        
        row = {
            'query_id': cpv['query_id'],
            'metric': metric,
            'raw_p': cpv['raw_p'],
            'corrected_p': cpv['corrected_p'],
            'is_significant': cpv['is_significant'],
            'mdes': mdes_data['mdes'],
            'power': mdes_data['power'],
            'ci_width': mdes_data['ci_width']
        }
        aggregated_rows.append(row)
    
    # Sort by query_id then metric for consistency
    aggregated_rows.sort(key=lambda x: (x['query_id'], x['metric']))
    
    # Write to CSV
    fieldnames = ['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant', 'mdes', 'power', 'ci_width']
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated_rows)
    
    logger.info(f"Summary CSV generated with {len(aggregated_rows)} rows: {output_path}")

def run_summary_generation() -> str:
    """
    Main entry point for generating the summary CSV.
    
    Returns:
        Path to the generated summary CSV file.
    """
    logger.info("Starting summary generation...")
    
    # Load all required data
    raw_p_values = load_raw_p_values()
    corrected_p_values = load_corrected_p_values()
    mdes_summary = load_mdes_summary()
    
    logger.info(f"Loaded {len(raw_p_values)} raw p-values, {len(corrected_p_values)} corrected p-values, {len(mdes_summary)} MDES entries")
    
    # Generate output path
    output_path = os.path.join(RESULTS_DIR, "summary.csv")
    
    # Generate the summary
    generate_summary_csv(raw_p_values, corrected_p_values, mdes_summary, output_path)
    
    return output_path
