import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import existing project utilities
from data_model import MetricResult
from logging_config import get_logger
from state_tracker import load_state_file, save_state_file, update_state_timestamp
from metric_validation import load_metrics_data

logger = get_logger(__name__)

def compute_cliffs_delta(group1_values: List[float], group2_values: List[float]) -> float:
    """
    Compute Cliff's Delta effect size between two independent groups.
    
    Cliff's Delta = (number of times x > y - number of times x < y) / (n1 * n2)
    Range: [-1, 1]
    """
    if not group1_values or not group2_values:
        raise ValueError("Both groups must contain values.")
    
    n1 = len(group1_values)
    n2 = len(group2_values)
    
    count_greater = 0
    count_less = 0
    
    for x in group1_values:
        for y in group2_values:
            if x > y:
                count_greater += 1
            elif x < y:
                count_less += 1
    
    delta = (count_greater - count_less) / (n1 * n2)
    return delta

def get_effect_size_magnitude(delta: float) -> str:
    """
    Classify the magnitude of Cliff's Delta based on standard thresholds.
    
    Thresholds (commonly used):
    |delta| < 0.147: negligible
    0.147 <= |delta| < 0.33: small
    0.33 <= |delta| < 0.474: medium
    |delta| >= 0.474: large
    """
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return "negligible"
    elif abs_delta < 0.33:
        return "small"
    elif abs_delta < 0.474:
        return "medium"
    else:
        return "large"

def load_metric_data_for_comparison(metric_type: str) -> Tuple[List[float], List[float]]:
    """
    Load metric values for 'human' (CodeSearchNet) and 'llm' (CodeGen) groups.
    Returns (human_values, llm_values).
    """
    # Expected path based on T023/T024: data/metrics/
    metrics_dir = Path("data/metrics")
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found at {metrics_dir}")
    
    # Look for the specific metric file
    # T023 says "one file per metric type". Assuming naming convention: {metric_type}_metrics.csv
    # Or we might need to load the aggregated file. Let's try to find the specific metric file.
    # Based on T024, it conforms to MetricResult schema.
    
    file_path = metrics_dir / f"{metric_type}_metrics.csv"
    
    if not file_path.exists():
        # Fallback: try to find any csv with the metric name or load general metrics
        # For robustness, we assume the file naming convention from T023
        raise FileNotFoundError(f"Metric file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Ensure columns exist
    required_cols = ['group_label', 'score']
    if not all(col in df.columns for col in required_cols):
        # Try to infer column names if they differ slightly, or raise error
        raise ValueError(f"Metric file {file_path} missing required columns: {required_cols}")
    
    human_data = df[df['group_label'] == 'human']['score'].tolist()
    llm_data = df[df['group_label'] == 'llm']['score'].tolist()
    
    if not human_data or not llm_data:
        raise ValueError(f"One or both groups have no data for metric {metric_type}")
    
    return human_data, llm_data

def run_cliffs_delta_analysis(metric_types: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Run Cliff's Delta analysis for all metric types.
    Returns a dictionary of results keyed by metric type.
    """
    if metric_types is None:
        # Default metric types based on T020/T021
        metric_types = [
            'cyclomatic_complexity', 
            'maintainability_index', 
            'loc', 
            'potential_bug', 
            'style_issue'
        ]
    
    results = {}
    
    for metric in metric_types:
        try:
            logger.info(f"Computing Cliff's Delta for metric: {metric}")
            human_vals, llm_vals = load_metric_data_for_comparison(metric)
            
            delta = compute_cliffs_delta(human_vals, llm_vals)
            magnitude = get_effect_size_magnitude(delta)
            
            results[metric] = {
                'cliffs_delta': delta,
                'magnitude': magnitude,
                'human_n': len(human_vals),
                'llm_n': len(llm_vals),
                'human_mean': float(np.mean(human_vals)),
                'llm_mean': float(np.mean(llm_vals))
            }
            logger.info(f"  Result: delta={delta:.4f}, magnitude={magnitude}")
            
        except FileNotFoundError as e:
            logger.warning(f"Skipping {metric}: {e}")
            results[metric] = {'error': str(e), 'cliffs_delta': None, 'magnitude': None}
        except Exception as e:
            logger.error(f"Error processing {metric}: {e}")
            results[metric] = {'error': str(e), 'cliffs_delta': None, 'magnitude': None}
    
    return results

def save_results_to_csv(results: Dict[str, Dict[str, Any]], output_path: str) -> None:
    """
    Save Cliff's Delta results to a CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for metric, data in results.items():
        row = {
            'metric_type': metric,
            'cliffs_delta': data.get('cliffs_delta'),
            'magnitude': data.get('magnitude'),
            'human_n': data.get('human_n'),
            'llm_n': data.get('llm_n'),
            'human_mean': data.get('human_mean'),
            'llm_mean': data.get('llm_mean'),
            'error': data.get('error')
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved Cliff's Delta results to {output_file}")

def update_state_with_cliffs_delta(results: Dict[str, Dict[str, Any]]) -> None:
    """
    Update the project state file with Cliff's Delta analysis results.
    """
    state_path = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}, skipping update.")
        return
    
    state = load_state_file(state_path)
    
    if 'analysis_results' not in state:
        state['analysis_results'] = {}
    
    state['analysis_results']['cliffs_delta'] = {
        'timestamp': update_state_timestamp(),
        'results': results
    }
    
    save_state_file(state, state_path)
    logger.info(f"Updated state file with Cliff's Delta results.")

def main():
    """
    Main entry point for Cliff's Delta analysis task (T029).
    """
    logger.info("Starting Cliff's Delta Analysis (T029)")
    
    # Run analysis
    results = run_cliffs_delta_analysis()
    
    # Save results
    output_csv = "data/metrics/cliffs_delta_results.csv"
    save_results_to_csv(results, output_csv)
    
    # Update state
    update_state_with_cliffs_delta(results)
    
    logger.info("Cliff's Delta Analysis completed.")
    return results

if __name__ == "__main__":
    main()
