import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_baseline_stats(metrics_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate baseline statistics (mean and std) for LOC and CC from a list of metrics.
    This serves as the reference for matching quality evaluation.
    """
    if not metrics_list:
        return {'loc_mean': 0.0, 'loc_std': 0.0, 'cc_mean': 0.0, 'cc_std': 0.0}
    
    loc_values = [m.get('loc', 0) for m in metrics_list]
    cc_values = [m.get('cyclomatic_complexity', 0) for m in metrics_list]
    
    n = len(loc_values)
    loc_mean = sum(loc_values) / n
    cc_mean = sum(cc_values) / n
    
    loc_variance = sum((x - loc_mean) ** 2 for x in loc_values) / n
    cc_variance = sum((x - cc_mean) ** 2 for x in cc_values) / n
    
    loc_std = loc_variance ** 0.5
    cc_std = cc_variance ** 0.5
    
    return {
        'loc_mean': loc_mean,
        'loc_std': loc_std,
        'cc_mean': cc_mean,
        'cc_std': cc_std
    }

def evaluate_matching_quality(
    repo_metrics: Dict[str, Any], 
    baseline_stats: Dict[str, float]
) -> Dict[str, Any]:
    """
    Evaluate the matching quality of a repository against the baseline.
    
    Per FR-009 and task requirements:
    - Compare LOC and CC against baseline mean.
    - Calculate percentage deviation.
    - The ±15% tolerance is for descriptive statistics ONLY.
    - ALL repos are retained; no filtering based on tolerance.
    """
    report = {
        'repo_id': repo_metrics.get('repo_id', 'unknown'),
        'loc': repo_metrics.get('loc', 0),
        'cc': repo_metrics.get('cyclomatic_complexity', 0),
        'baseline': baseline_stats,
        'matching_quality': {}
    }
    
    # Calculate deviations
    loc_deviation = 0.0
    cc_deviation = 0.0
    
    if baseline_stats['loc_std'] > 0:
        loc_deviation = (repo_metrics['loc'] - baseline_stats['loc_mean']) / baseline_stats['loc_mean']
    else:
        # If std is 0, deviation is based on mean difference
        if baseline_stats['loc_mean'] > 0:
            loc_deviation = (repo_metrics['loc'] - baseline_stats['loc_mean']) / baseline_stats['loc_mean']
        
    if baseline_stats['cc_std'] > 0:
        cc_deviation = (repo_metrics['cc'] - baseline_stats['cc_mean']) / baseline_stats['cc_mean']
    else:
        if baseline_stats['cc_mean'] > 0:
            cc_deviation = (repo_metrics['cc'] - baseline_stats['cc_mean']) / baseline_stats['cc_mean']
    
    report['matching_quality'] = {
        'loc_deviation_pct': round(loc_deviation * 100, 2),
        'cc_deviation_pct': round(cc_deviation * 100, 2),
        'within_loc_tolerance_15pct': abs(loc_deviation) <= 0.15,
        'within_cc_tolerance_15pct': abs(cc_deviation) <= 0.15,
        'notes': "Deviation calculated for descriptive statistics. All repos retained for ANCOVA adjustment."
    }
    
    return report

def main():
    """
    Main entry point to execute quantitative matching logic.
    
    1. Loads repo metrics from data/raw/repo_metrics.json (produced by T021c).
    2. Calculates baseline statistics.
    3. Evaluates matching quality for each repo.
    4. Writes the matching quality report to data/raw/repo_matching_report.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / 'data' / 'raw' / 'repo_metrics.json'
    output_path = project_root / 'data' / 'raw' / 'repo_matching_report.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading repository metrics from {metrics_path}")
    try:
        metrics_data = load_json_file(str(metrics_path))
    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        logger.error("T021c must run successfully to produce repo_metrics.json before T021d.")
        sys.exit(1)
    
    if not metrics_data or 'repos' not in metrics_data:
        logger.error("Invalid metrics data format. Expected 'repos' key.")
        sys.exit(1)
    
    repos = metrics_data['repos']
    logger.info(f"Found {len(repos)} repositories to evaluate.")
    
    # Calculate baseline statistics from the loaded metrics
    baseline_stats = calculate_baseline_stats(repos)
    logger.info(f"Calculated baseline stats: {baseline_stats}")
    
    # Evaluate matching quality for each repo
    matching_report = {
        'baseline_statistics': baseline_stats,
        'evaluation_timestamp': str(Path(__file__).parent.parent.stat().st_mtime),
        'matching_details': []
    }
    
    for repo in repos:
        quality_eval = evaluate_matching_quality(repo, baseline_stats)
        matching_report['matching_details'].append(quality_eval)
    
    # Write the output file
    with open(output_path, 'w') as f:
        json.dump(matching_report, f, indent=2)
    
    logger.info(f"Matching quality report written to {output_path}")
    logger.info("Task T021d completed successfully. All repos retained for ANCOVA.")

if __name__ == "__main__":
    main()
