"""
Aggregation module for T016.
Merges entropy results, convergence results, exclusion logs, and significance flags
into a single analysis_summary.json file.
"""
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def load_entropy_results(path: str) -> List[Dict[str, Any]]:
    """Load entropy results from CSV."""
    results = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Entropy results file not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to appropriate types
            row['entropy'] = float(row['entropy']) if row['entropy'] else 0.0
            row['cluster_count'] = int(row['cluster_count']) if row['cluster_count'] else 0
            results.append(row)
    return results

def load_convergence_results(path: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    results = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Convergence results file not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert k_correct to int if present
            if 'k_correct' in row and row['k_correct']:
                row['k_correct'] = int(row['k_correct'])
            results.append(row)
    return results

def load_exclusion_log(path: str) -> Dict[str, Any]:
    """Load exclusion log from JSON."""
    p = Path(path)
    if not p.exists():
        logger.warning(f"Exclusion log not found: {path}. Returning empty log.")
        return {"excluded_count": 0, "excluded_rate": 0.0, "details": []}
    
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_significance_flag(path: str) -> bool:
    """Load the is_significant flag from analysis_summary.json created by T015b."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Analysis summary (significance flag) not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("is_significant", False)

def aggregate_results(
    entropy_path: str,
    convergence_path: str,
    exclusion_log_path: str,
    significance_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Aggregate all results into a single analysis_summary.json.
    
    Merges:
    - entropy_results.csv
    - convergence_results.csv
    - exclusion_log.json
    - is_significant flag from T015b
    
    Creates a unified record per task_id with all metrics.
    """
    # Load all components
    entropy_data = load_entropy_results(entropy_path)
    convergence_data = load_convergence_results(convergence_path)
    exclusion_log = load_exclusion_log(exclusion_log_path)
    is_significant = load_significance_flag(significance_path)
    
    # Create lookup dictionaries by task_id
    entropy_by_task = {item['task_id']: item for item in entropy_data}
    conv_by_task = {item['task_id']: item for item in convergence_data}
    
    # Get all unique task_ids
    all_task_ids = set(entropy_by_task.keys()) | set(conv_by_task.keys())
    
    # Merge records
    merged_records = []
    for task_id in sorted(all_task_ids):
        record = {
            'task_id': task_id,
            'entropy': entropy_by_task.get(task_id, {}).get('entropy'),
            'cluster_count': entropy_by_task.get(task_id, {}).get('cluster_count'),
            'excluded_reason': entropy_by_task.get(task_id, {}).get('excluded_reason'),
            'k_correct': conv_by_task.get(task_id, {}).get('k_correct'),
            'trajectory_status': conv_by_task.get(task_id, {}).get('trajectory_status')
        }
        merged_records.append(record)
    
    # Build final summary
    summary = {
        'metadata': {
            'total_tasks': len(merged_records),
            'entropy_tasks': len(entropy_data),
            'convergence_tasks': len(convergence_data),
            'excluded_count': exclusion_log.get('excluded_count', 0),
            'excluded_rate': exclusion_log.get('excluded_rate', 0.0),
            'is_significant': is_significant
        },
        'exclusion_log': exclusion_log,
        'significance': {
            'is_significant': is_significant,
            'threshold': 0.05
        },
        'results': merged_records
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Aggregated results written to {output_path}")
    logger.info(f"Total tasks: {len(merged_records)}")
    logger.info(f"Significant: {is_significant}")
    
    return summary

def main():
    """Main entry point for T016 aggregation."""
    import os
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data' / 'processed'
    
    entropy_path = str(data_dir / 'entropy_results.csv')
    convergence_path = str(data_dir / 'convergence_results.csv')
    exclusion_log_path = str(data_dir / 'exclusion_log.json')
    significance_path = str(data_dir / 'analysis_summary.json')  # Contains is_significant from T015b
    output_path = str(data_dir / 'analysis_summary.json')  # Overwrite with full aggregation
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        result = aggregate_results(
            entropy_path=entropy_path,
            convergence_path=convergence_path,
            exclusion_log_path=exclusion_log_path,
            significance_path=significance_path,
            output_path=output_path
        )
        print(f"Aggregation complete. Output: {output_path}")
        print(f"Total tasks aggregated: {result['metadata']['total_tasks']}")
        print(f"Is significant: {result['metadata']['is_significant']}")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

if __name__ == '__main__':
    main()
