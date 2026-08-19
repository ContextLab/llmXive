import json
import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats as scipy_stats
import logging

from src.config import get_config
from src.main import run_evaluation_pipeline, load_paths_from_json, save_paths_to_json
from src.evaluator import Evaluator, load_test_sessions, save_metrics_to_json

logger = logging.getLogger(__name__)

def run_sensitivity_analysis(
    output_dir: str = "results",
    path_lengths: Optional[List[int]] = None,
    similarity_thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on decision cutoffs: path length and similarity threshold.
    
    This function sweeps across specified values of path length (L) and similarity threshold,
    re-running the evaluation pipeline for each combination to observe how headline metrics
    (Precision@K, Recall@K, Diversity, Coverage) vary.
    
    Args:
        output_dir: Directory to store the sensitivity analysis results.
        path_lengths: List of path lengths to test (default: [3, 4, 5]).
        similarity_thresholds: List of similarity thresholds to test (default: [0.01, 0.05, 0.1]).
        
    Returns:
        A dictionary containing the sweep results keyed by (path_length, threshold) tuples.
    """
    if path_lengths is None:
        path_lengths = [3, 4, 5]
    if similarity_thresholds is None:
        similarity_thresholds = [0.01, 0.05, 0.1]

    logger.info(f"Starting sensitivity analysis with path_lengths={path_lengths}, thresholds={similarity_thresholds}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    config = get_config()
    
    for L in path_lengths:
        for thresh in similarity_thresholds:
            logger.info(f"Running evaluation for L={L}, threshold={thresh}")
            
            # Update config for this sweep
            config['path_length'] = L
            config['similarity_threshold'] = thresh
            
            # Run the evaluation pipeline with updated config
            # This will regenerate paths and metrics for the current L and threshold
            try:
                # We need to re-run the pipeline to get fresh results for these parameters
                # The run_evaluation_pipeline function should respect the updated config
                evaluation_results = run_evaluation_pipeline(config)
                
                # Store the results for this configuration
                key = f"L{L}_thresh{thresh}"
                results[key] = {
                    "path_length": L,
                    "similarity_threshold": thresh,
                    "metrics": evaluation_results
                }
                
                logger.info(f"Completed evaluation for L={L}, threshold={thresh}")
                
            except Exception as e:
                logger.error(f"Error during evaluation for L={L}, threshold={thresh}: {str(e)}")
                results[f"L{L}_thresh{thresh}"] = {
                    "path_length": L,
                    "similarity_threshold": thresh,
                    "error": str(e)
                }

    # Save raw sensitivity results
    raw_results_path = os.path.join(output_dir, "sensitivity_analysis_raw.json")
    with open(raw_results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis raw results saved to {raw_results_path}")
    
    return results

def aggregate_sensitivity_report(
    sensitivity_results: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregate sensitivity analysis results into a summary report.
    
    This function processes the raw sensitivity results to compute headline rate variations
    across different path lengths and similarity thresholds, identifying trends and optimal
    parameter ranges.
    
    Args:
        sensitivity_results: The raw results from run_sensitivity_analysis.
        output_path: Path to save the aggregated report (optional).
        
    Returns:
        A dictionary containing the aggregated sensitivity report.
    """
    report = {
        "summary": {},
        "trends": {},
        "optimal_configs": [],
        "parameter_sweep": sensitivity_results
    }
    
    # Extract metrics for analysis
    metrics_data = {}
    for key, result in sensitivity_results.items():
        if "error" in result:
            continue
        
        L = result["path_length"]
        thresh = result["similarity_threshold"]
        metrics = result["metrics"]
        
        if L not in metrics_data:
            metrics_data[L] = {}
        metrics_data[L][thresh] = metrics
    
    # Analyze trends by path length
    for L, thresh_metrics in metrics_data.items():
        if not thresh_metrics:
            continue
        
        # Average metrics across thresholds for this path length
        avg_metrics = {}
        metric_names = list(next(iter(thresh_metrics.values())).keys())
        
        for metric_name in metric_names:
            values = [
                thresh_metrics[thresh].get(metric_name, 0) 
                for thresh in thresh_metrics 
                if metric_name in thresh_metrics[thresh]
            ]
            if values:
                avg_metrics[metric_name] = np.mean(values)
        
        report["trends"][f"avg_by_path_length_{L}"] = avg_metrics
    
    # Analyze trends by threshold
    all_thresholds = set()
    for L_data in metrics_data.values():
        all_thresholds.update(L_data.keys())
    
    for thresh in all_thresholds:
        avg_metrics = {}
        metric_names = list(next(iter(metrics_data.values())).keys()) if metrics_data else []
        
        for metric_name in metric_names:
            values = []
            for L_data in metrics_data.values():
                if thresh in L_data and metric_name in L_data[thresh]:
                    values.append(L_data[thresh][metric_name])
            
            if values:
                avg_metrics[metric_name] = np.mean(values)
        
        report["trends"][f"avg_by_threshold_{thresh}"] = avg_metrics
    
    # Identify optimal configurations (highest Precision@K or F1-like score)
    best_score = -1
    best_config = None
    
    for key, result in sensitivity_results.items():
        if "error" in result:
            continue
        
        metrics = result["metrics"]
        precision = metrics.get("precision_at_5", 0)
        recall = metrics.get("recall_at_5", 0)
        
        # Simple F1-like score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0
        
        if f1_score > best_score:
            best_score = f1_score
            best_config = {
                "path_length": result["path_length"],
                "similarity_threshold": result["similarity_threshold"],
                "f1_score": f1_score,
                "precision_at_5": precision,
                "recall_at_5": recall
            }
    
    if best_config:
        report["optimal_configs"].append(best_config)
    
    # Save report if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Sensitivity report saved to {output_path}")
    
    return report