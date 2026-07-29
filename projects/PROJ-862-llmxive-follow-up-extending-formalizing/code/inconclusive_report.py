"""
Inconclusive Report Generator for No Valid Sigma Scenario.

This module handles the specific case where the validity_log.csv shows that
NO sigma level passes the 90% validity threshold. Instead of attempting
statistical tests on an empty set, it generates a specific report detailing
the trade-off curve and flags the experiment as "Inconclusive".
"""

import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from sibling modules as per API surface
from config import OutputPaths, load_config
from memory_monitor import get_peak_memory_mb

logger = logging.getLogger(__name__)

# Configuration constants
VALIDITY_THRESHOLD = 0.90  # 90% validity threshold

def check_no_valid_sigma_scenario(validity_log_path: str) -> bool:
    """
    Check if the validity_log.csv shows that no sigma level passes the threshold.

    Args:
        validity_log_path: Path to the validity_log.csv file

    Returns:
        True if no sigma level passes the threshold for ANY task type, False otherwise.
    """
    if not os.path.exists(validity_log_path):
        logger.warning(f"Validity log not found at {validity_log_path}. Cannot determine scenario.")
        return False

    try:
        task_types_with_pass = set()
        
        with open(validity_log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pass_rate = float(row.get('pass_rate', 0.0))
                    task_type = row.get('task_type', 'unknown')
                    
                    if pass_rate >= VALIDITY_THRESHOLD:
                        task_types_with_pass.add(task_type)
                except (ValueError, TypeError):
                    continue
        
        # If we found at least one task type with a passing sigma, it's NOT the inconclusive scenario
        return len(task_types_with_pass) == 0
        
    except Exception as e:
        logger.error(f"Error reading validity log: {e}")
        return False

def generate_inconclusive_report(
    validity_log_path: str,
    output_dir: str,
    task_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a detailed NoValidSigmaReport when no sigma passes the threshold.

    This report includes:
    - The full trade-off curve (sigma vs pass_rate) for all task types
    - Explicit flag marking the experiment as "Inconclusive"
    - Statistical summary of the trade-off curves
    - Memory profile at time of generation
    - Timestamp and configuration metadata

    Args:
        validity_log_path: Path to the validity_log.csv
        output_dir: Directory to save the report
        task_types: Optional list of task types to include (if None, all found in log)

    Returns:
        The generated report dictionary (also saved to disk)
    """
    if not os.path.exists(validity_log_path):
        raise FileNotFoundError(f"Validity log not found at {validity_log_path}")

    # Collect trade-off curve data
    trade_off_data: Dict[str, List[Dict[str, Any]]] = {}
    all_task_types = set()
    
    with open(validity_log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_type = row.get('task_type', 'unknown')
            all_task_types.add(task_type)
            
            try:
                sigma = float(row.get('sigma', 0.0))
                pass_rate = float(row.get('pass_rate', 0.0))
                collapse_point = row.get('collapse_point', 'false').lower() == 'true'
                
                if task_type not in trade_off_data:
                    trade_off_data[task_type] = []
                
                trade_off_data[task_type].append({
                    'sigma': sigma,
                    'pass_rate': pass_rate,
                    'collapse_point': collapse_point
                })
            except (ValueError, TypeError):
                continue

    # Filter to requested task types if provided
    if task_types:
        trade_off_data = {k: v for k, v in trade_off_data.items() if k in task_types}

    # Calculate statistics for each task type
    task_stats = {}
    for task_type, data in trade_off_data.items():
        if not data:
            continue
        
        pass_rates = [d['pass_rate'] for d in data]
        sigmas = [d['sigma'] for d in data]
        
        max_pass_rate = max(pass_rates) if pass_rates else 0.0
        max_pass_sigma = sigmas[pass_rates.index(max_pass_rate)] if pass_rates else 0.0
        
        task_stats[task_type] = {
            'max_pass_rate': max_pass_rate,
            'sigma_at_max_pass': max_pass_sigma,
            'total_sigma_points': len(data),
            'all_pass_rates_below_threshold': all(p < VALIDITY_THRESHOLD for p in pass_rates)
        }

    # Build the report
    report = {
        'report_type': 'NoValidSigmaReport',
        'status': 'Inconclusive',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'threshold_used': VALIDITY_THRESHOLD,
        'summary': {
            'total_task_types_analyzed': len(trade_off_data),
            'task_types_with_no_valid_sigma': len([
                t for t, stats in task_stats.items() 
                if stats.get('all_pass_rates_below_threshold', False)
            ]),
            'global_max_pass_rate': max(
                (s['max_pass_rate'] for s in task_stats.values()), 
                default=0.0
            )
        },
        'task_statistics': task_stats,
        'trade_off_curves': trade_off_data,
        'memory_profile': {
            'peak_rss_mb': get_peak_memory_mb()
        },
        'recommendation': (
            "No sigma level achieved the required validity threshold (>=90%). "
            "Statistical analysis on separability cannot be performed on a valid set. "
            "Consider revising the perturbation strategy, lowering the validity threshold, "
            "or investigating why the model outputs collapse so rapidly with noise injection."
        )
    }

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save report to disk
    report_path = os.path.join(output_dir, 'no_valid_sigma_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"NoValidSigmaReport generated and saved to {report_path}")
    
    return report

def main():
    """
    Main entry point for generating the inconclusive report.
    Typically called from main.py when the analysis phase detects no valid sigma.
    """
    # Load configuration
    try:
        config = load_config()
        output_paths = config.output_paths
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1

    validity_log_path = output_paths.validity_log
    
    # Check if we are in the no-valid-sigma scenario
    if not check_no_valid_sigma_scenario(validity_log_path):
        logger.info("Valid sigma levels found. No inconclusive report needed.")
        return 0

    logger.warning("No valid sigma levels found. Generating inconclusive report...")
    
    try:
        report = generate_inconclusive_report(
            validity_log_path=validity_log_path,
            output_dir=output_paths.processed_dir,
            task_types=None  # Process all task types
        )
        logger.info(f"Inconclusive report status: {report['status']}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate inconclusive report: {e}")
        return 1

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())
