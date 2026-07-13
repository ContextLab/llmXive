import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from analysis import run_baseline_analysis
from config import Config
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

def format_metric_value(value: Any) -> Any:
    """Format metric values to required precision (>=3 decimal places)."""
    if isinstance(value, float):
        return round(value, 4) # 4 decimal places ensures >=3
    elif isinstance(value, list):
        return [format_metric_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: format_metric_value(v) for k, v in value.items()}
    return value

def log_metrics_summary(metrics: List[Dict[str, Any]]) -> None:
    """Log a summary of the baseline metrics."""
    logger.info("=== Baseline Metrics Summary ===")
    for dataset in metrics:
        name = dataset.get("dataset_name", "Unknown")
        logger.info(f"Dataset: {name}")
        logger.info(f"  Rows: {dataset.get('n_rows')}, Cols: {dataset.get('n_cols')}")
        logger.info(f"  T-tests: {len(dataset.get('t_test_results', []))}")
        logger.info(f"  Regressions: {len(dataset.get('regression_results', []))}")
        for t in dataset.get("t_test_results", []):
            logger.info(f"    T-Test ({t.get('group_col')} vs {t.get('outcome_col')}): p={t.get('p_value'):.4f}, d={t.get('effect_size_cohen_d'):.4f}")
        for r in dataset.get("regression_results", []):
            logger.info(f"    Regression ({r.get('predictor_col')} vs {r.get('outcome_col')}): R2={r.get('r_squared'):.4f}, p_slope={r.get('p_values', {}).get('slope', 'N/A')}")

def process_dataset_for_baseline(dataset_path: str, dataset_name: str, output_path: str) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset, run baseline analysis, and record metrics.
    """
    try:
        # Run analysis on the specific file
        results = run_baseline_analysis(
            data_source=dataset_path,
            dataset_name=dataset_name,
            output_path=None # We handle output manually to ensure checksumming
        )
        
        if not results:
            logger.warning(f"No results for {dataset_name}")
            return None

        # results is a list, take the first (and usually only) entry
        metric_entry = results[0]
        
        # Format values
        formatted_entry = format_metric_value(metric_entry)
        
        # Compute checksum
        checksum = compute_file_checksum(dataset_path)
        formatted_entry["data_checksum"] = checksum
        
        return formatted_entry
    except Exception as e:
        logger.error(f"Failed to process {dataset_name}: {e}")
        return None

def main():
    setup_logging("INFO")
    config = Config()
    
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw directory {raw_dir} does not exist.")
        return 1
    
    files = [f for f in os.listdir(raw_dir) if f.endswith(('.csv', '.tsv'))]
    if not files:
        logger.warning(f"No CSV/TSV files found in {raw_dir}.")
        return 1
    
    all_metrics = []
    for filename in files:
        filepath = os.path.join(raw_dir, filename)
        name = os.path.splitext(filename)[0]
        logger.info(f"Processing {name}...")
        metric = process_dataset_for_baseline(filepath, name, output_file)
        if metric:
            all_metrics.append(metric)
    
    if all_metrics:
        # Write final aggregated JSON
        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        log_metrics_summary(all_metrics)
        logger.info(f"Baseline metrics saved to {output_file}")
        logger.info(f"Total datasets processed: {len(all_metrics)}")
        
        # Verify file exists
        if os.path.exists(output_file):
            logger.info("Output file verification: SUCCESS")
            return 0
        else:
            logger.error("Output file verification: FAILED - file not found after write")
            return 1
    else:
        logger.error("No metrics recorded. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())