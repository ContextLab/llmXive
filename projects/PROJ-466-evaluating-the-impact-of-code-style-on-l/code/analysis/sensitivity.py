import logging
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Any
import numpy as np
from scipy.stats import kruskal

from config.loader import load_config
from utils.logger import log_generation_error

logger = logging.getLogger(__name__)

def load_metrics_for_sensitivity(metrics_path: Path) -> Dict[str, List[float]]:
    """
    Load metrics from the valid metrics CSV and group by style.
    Returns a dictionary: {style: [list of diversity scores]}
    """
    style_data: Dict[str, List[float]] = {}
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    with open(metrics_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            style = row.get('style')
            # Assuming the column for diversity score is 'ast_edit_distance' or similar
            # We need to be flexible. Let's look for a numeric metric column.
            # Based on T025, the file contains computed metrics.
            # We will look for 'ast_edit_distance' as the primary metric for diversity.
            score_str = row.get('ast_edit_distance')
            if score_str is None:
                # Fallback: try to find any numeric column if ast_edit_distance isn't present
                for key, val in row.items():
                    if key not in ['task_id', 'style', 'sample_id'] and val:
                        try:
                            score_str = val
                            break
                        except:
                            continue

            if score_str:
                try:
                    score = float(score_str)
                    if style not in style_data:
                        style_data[style] = []
                    style_data[style].append(score)
                except ValueError:
                    continue
    
    return style_data

def run_sweep_kruskal(style_data: Dict[str, List[float]], alpha_values: List[float]) -> List[Dict[str, Any]]:
    """
    Perform Kruskal-Wallis test for a range of alpha values.
    Returns a list of results for each alpha.
    """
    if len(style_data) < 2:
        logger.warning("Not enough style groups to perform statistical test.")
        return []

    groups = list(style_data.values())
    if any(len(g) == 0 for g in groups):
        logger.warning("One or more style groups are empty.")
        return []

    results = []
    
    # Perform the test once to get the statistic and p-value
    # We assume the distribution doesn't change with alpha, only the significance decision.
    try:
        stat, p_value = kruskal(*groups)
    except Exception as e:
        log_generation_error("Sensitivity Analysis", "Kruskal-Wallis test failed", str(e))
        return []

    for alpha in alpha_values:
        is_significant = p_value < alpha
        results.append({
            'alpha': alpha,
            'p_value': p_value,
            'is_significant': is_significant,
            'h_statistic': stat
        })
    
    return results

def run_sensitivity_analysis(metrics_path: Path, output_path: Path, alpha_range: List[float] = None):
    """
    Main entry point for sensitivity analysis.
    Sweeps alpha, determines significance, and writes results to CSV.
    """
    if alpha_range is None:
        # Default range of small values as per task description
        alpha_range = [0.001, 0.005, 0.01, 0.025, 0.05, 0.10]

    logger.info(f"Starting sensitivity analysis with alpha range: {alpha_range}")
    
    try:
        style_data = load_metrics_for_sensitivity(metrics_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    results = run_sweep_kruskal(style_data, alpha_range)

    if not results:
        logger.warning("No results generated from sensitivity analysis.")
        return

    # Write results to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['alpha', 'h_statistic', 'p_value', 'is_significant']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        significant_count = 0
        for res in results:
            writer.writerow(res)
            if res['is_significant']:
                significant_count += 1

    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    logger.info(f"Significant tasks found in {significant_count}/{len(results)} alpha thresholds.")

    return results

def run_sensitivity_pipeline():
    """
    Orchestrates the sensitivity analysis pipeline.
    """
    config = load_config()
    metrics_path = Path(config.get('paths', {}).get('metrics_valid', 'data/processed/metrics_valid.csv'))
    output_path = Path(config.get('paths', {}).get('sensitivity_results', 'data/processed/sensitivity_analysis.csv'))
    
    # Extract alpha range from config if available, else use default
    alpha_range = config.get('analysis', {}).get('alpha_sweep', [0.001, 0.005, 0.01, 0.025, 0.05, 0.10])

    run_sensitivity_analysis(metrics_path, output_path, alpha_range)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_sensitivity_pipeline()
