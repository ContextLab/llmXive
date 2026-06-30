import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import setup_logging
from config import get_config

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> List[Dict[str, Any]]:
    """Load baseline metrics from a JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return []
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'datasets' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'datasets' in data:
        return data['datasets']
    else:
        logger.warning(f"Unexpected baseline metrics format in {filepath}")
        return []

def load_cleaned_metrics(filepath: str) -> List[Dict[str, Any]]:
    """Load cleaned metrics from a JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return []
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'datasets' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'datasets' in data:
        return data['datasets']
    else:
        logger.warning(f"Unexpected cleaned metrics format in {filepath}")
        return []

def check_missing_outcome_rate(dataset_info: Dict[str, Any]) -> float:
    """
    Calculate the missing outcome rate for a dataset.
    Assumes dataset_info contains 'missing_outcome_rate' or calculates from 'missing_values'.
    """
    if 'missing_outcome_rate' in dataset_info:
        return dataset_info['missing_outcome_rate']
    
    # Fallback: try to calculate from missing_values if available
    if 'missing_values' in dataset_info:
        missing = dataset_info['missing_values']
        total = dataset_info.get('total_rows', 0)
        if total > 0:
            return missing / total
    
    # Default to 0 if no data available
    return 0.0

def log_excluded_datasets(baseline_filepath: str, cleaned_filepath: str, exclusion_threshold: float = 0.80) -> List[Dict[str, Any]]:
    """
    Identify and log datasets excluded due to high missing outcome rate (>80%).
    
    Args:
        baseline_filepath: Path to baseline metrics JSON
        cleaned_filepath: Path to cleaned metrics JSON
        exclusion_threshold: Threshold for missing outcome rate (default 0.80)
    
    Returns:
        List of excluded dataset records with reasons
    """
    baseline_datasets = load_baseline_metrics(baseline_filepath)
    cleaned_datasets = load_cleaned_metrics(cleaned_filepath)
    
    excluded_datasets = []
    
    # Check baseline datasets
    for dataset in baseline_datasets:
        dataset_name = dataset.get('dataset_name', dataset.get('name', 'unknown'))
        missing_rate = check_missing_outcome_rate(dataset)
        
        if missing_rate > exclusion_threshold:
            reason = f"Excluded: Missing outcome rate ({missing_rate:.2%}) exceeds threshold ({exclusion_threshold:.2%})"
            logger.warning(f"⚠ EXCLUDED DATASET: {dataset_name} - {reason}")
            
            excluded_datasets.append({
                'dataset_name': dataset_name,
                'missing_outcome_rate': missing_rate,
                'exclusion_threshold': exclusion_threshold,
                'reason': reason,
                'source': 'baseline'
            })
    
    # Check cleaned datasets (if not already excluded from baseline)
    baseline_names = {d['dataset_name'] for d in excluded_datasets if d['source'] == 'baseline'}
    
    for dataset in cleaned_datasets:
        dataset_name = dataset.get('dataset_name', dataset.get('name', 'unknown'))
        
        # Skip if already excluded from baseline
        if dataset_name in baseline_names:
            continue
        
        missing_rate = check_missing_outcome_rate(dataset)
        
        if missing_rate > exclusion_threshold:
            reason = f"Excluded: Missing outcome rate ({missing_rate:.2%}) exceeds threshold ({exclusion_threshold:.2%})"
            logger.warning(f"⚠ EXCLUDED DATASET: {dataset_name} - {reason}")
            
            excluded_datasets.append({
                'dataset_name': dataset_name,
                'missing_outcome_rate': missing_rate,
                'exclusion_threshold': exclusion_threshold,
                'reason': reason,
                'source': 'cleaned'
            })
    
    if not excluded_datasets:
        logger.info("No datasets excluded due to high missing outcome rate.")
    else:
        logger.info(f"Total excluded datasets: {len(excluded_datasets)}")
    
    return excluded_datasets

def main():
    """Main entry point for T039."""
    config = get_config()
    setup_logging(config.LOG_LEVEL)
    
    baseline_path = config.get('BASELINE_METRICS_PATH', 'data/processed/baseline_metrics.json')
    cleaned_path = config.get('CLEANED_METRICS_PATH', 'data/processed/cleaned_metrics.json')
    exclusion_threshold = float(config.get('EXCLUSION_THRESHOLD', 0.80))
    
    logger.info(f"Starting T039: Log excluded datasets (threshold > {exclusion_threshold:.2%})")
    logger.info(f"Baseline metrics: {baseline_path}")
    logger.info(f"Cleaned metrics: {cleaned_path}")
    
    excluded = log_excluded_datasets(baseline_path, cleaned_path, exclusion_threshold)
    
    # Save exclusion report
    report_path = config.get('EXCLUSION_REPORT_PATH', 'data/processed/excluded_datasets_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'exclusion_threshold': exclusion_threshold,
        'total_excluded': len(excluded),
        'excluded_datasets': excluded
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion report saved to: {report_path}")
    
    return excluded

if __name__ == '__main__':
    main()
