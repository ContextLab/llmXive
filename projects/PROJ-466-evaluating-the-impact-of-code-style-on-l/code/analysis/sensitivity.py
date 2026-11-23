import logging
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Any
import numpy as np
from scipy.stats import kruskal
from config.loader import load_config

logger = logging.getLogger(__name__)

def load_metrics_for_sensitivity(metrics_path: Path) -> List[Dict[str, Any]]:
    """
    Load metrics from the valid samples CSV (metrics_valid.csv).
    Returns a list of dictionaries containing task_id, style, and metric values.
    """
    data = []
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'task_id': row['task_id'],
                'style': row['style'],
                'ast_distance': float(row['ast_distance']),
                'ngram_entropy': float(row['ngram_entropy'])
            })
    return data

def run_sweep_kruskal(
    data: List[Dict[str, Any]],
    alpha_range: List[float],
    metric: str = 'ast_distance'
) -> List[Dict[str, Any]]:
    """
    Perform Kruskal-Wallis H-test for each alpha in the range.
    Returns a list of results: {alpha, significant_count, significant_tasks}.
    """
    results = []
    styles = sorted(list(set(d['style'] for d in data)))
    
    # Group data by task_id to check significance per task
    tasks = {}
    for row in data:
        tid = row['task_id']
        if tid not in tasks:
            tasks[tid] = {}
        if row['style'] not in tasks[tid]:
            tasks[tid][row['style']] = []
        tasks[tid][row['style']].append(row[metric])
    
    for alpha in alpha_range:
        significant_tasks = []
        
        for tid, style_data in tasks.items():
            if len(style_data) < 3:
                continue # Need at least 3 groups for Kruskal-Wallis
            
            groups = [style_data[s] for s in styles if s in style_data]
            if len(groups) < 3:
                continue
            
            # Remove empty groups
            groups = [g for g in groups if len(g) > 0]
            if len(groups) < 3:
                continue

            try:
                h_stat, p_val = kruskal(*groups)
                if p_val < alpha:
                    significant_tasks.append(tid)
            except Exception as e:
                logger.warning(f"Kruskal-Wallis failed for task {tid}: {e}")
                continue
        
        results.append({
            'alpha': alpha,
            'significant_count': len(significant_tasks),
            'significant_tasks': significant_tasks,
            'total_tasks': len(tasks)
        })
    
    return results

def run_sensitivity_analysis(
    metrics_path: Path,
    output_path: Path,
    alpha_range: List[float] = None
) -> Dict[str, Any]:
    """
    Main function to run sensitivity analysis.
    Sweeps alpha, computes significant tasks, and saves results to CSV.
    """
    if alpha_range is None:
        # Default small values as per spec
        alpha_range = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
    
    logger.info(f"Loading metrics from {metrics_path}")
    data = load_metrics_for_sensitivity(metrics_path)
    
    logger.info(f"Running Kruskal-Wallis sweep for alphas: {alpha_range}")
    sweep_results = run_sweep_kruskal(data, alpha_range, metric='ast_distance')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['alpha', 'significant_count', 'total_tasks', 'significant_tasks']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for res in sweep_results:
            # Convert list to string for CSV
            res['significant_tasks'] = ';'.join(res['significant_tasks'])
            writer.writerow(res)
    
    # Calculate summary statistics
    significant_counts = [r['significant_count'] for r in sweep_results]
    min_sig = min(significant_counts)
    max_sig = max(significant_counts)
    
    summary = {
        'alpha_range': alpha_range,
        'significant_task_count_range': (min_sig, max_sig),
        'output_file': str(output_path),
        'total_tasks_analyzed': sweep_results[0]['total_tasks'] if sweep_results else 0
    }
    
    logger.info(f"Sensitivity analysis complete. Significant tasks range: {min_sig} - {max_sig}")
    return summary

def run_sensitivity_pipeline(
    config_path: Path,
    metrics_input_path: Path = None,
    output_path: Path = None
) -> Dict[str, Any]:
    """
    Orchestrates the sensitivity analysis pipeline.
    Loads config, determines paths, and runs the analysis.
    """
    config = load_config(config_path)
    
    # Determine paths from config if not provided
    if metrics_input_path is None:
        metrics_input_path = Path(config.get('paths', {}).get('metrics_valid', 'data/processed/metrics_valid.csv'))
    if output_path is None:
        output_path = Path(config.get('paths', {}).get('sensitivity_results', 'data/processed/sensitivity_analysis.csv'))
    
    # Determine alpha range from config or use default
    alpha_range = config.get('analysis', {}).get('sensitivity_alpha_range', None)
    
    return run_sensitivity_analysis(
        metrics_input_path,
        output_path,
        alpha_range=alpha_range
    )
