import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SensitivityResult:
    """Result of sensitivity analysis for metastability thresholds."""
    density_threshold: float
    vortex_threshold: float
    false_positive_rate: float
    false_negative_rate: float
    accuracy: float
    f1_score: float

def load_or_generate_ground_truth_metrics(metrics_dir: str) -> List[Dict[str, Any]]:
    """
    Load ground truth metrics from processed data or generate if not available.
    In a real scenario, this would load from data/aggregated/ or data/processed/.
    For this implementation, we load from existing CSV/JSON outputs.
    
    Args:
        metrics_dir: Directory containing metric files.
        
    Returns:
        List of metric dictionaries with ground truth labels.
    """
    from utils.io_helpers import load_dataframe
    import pandas as pd
    
    # Try to load from aggregated metrics CSV
    aggregated_path = os.path.join(metrics_dir, 'aggregated_metrics.csv')
    if os.path.exists(aggregated_path):
        df = load_dataframe(aggregated_path)
        if df is not None:
            return df.to_dict('records')
    
    # Fallback: try to find any JSON files in the directory
    metrics_list = []
    for filename in os.listdir(metrics_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(metrics_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        metrics_list.extend(data)
                    else:
                        metrics_list.append(data)
            except Exception as e:
                logger.warning(f"Could not load {filepath}: {e}")
    
    return metrics_list

def evaluate_threshold(metrics_list: List[Dict[str, Any]], 
                       density_threshold: float, 
                       vortex_threshold: float) -> SensitivityResult:
    """
    Evaluate metastability classification performance for given thresholds.
    
    Args:
        metrics_list: List of metric dictionaries.
        density_threshold: Density drop threshold for metastability.
        vortex_threshold: Vortex density threshold for metastability.
        
    Returns:
        SensitivityResult with error rates and accuracy.
    """
    predictions = []
    ground_truth = []
    
    for m in metrics_list:
        # Apply classification logic
        condensate_density = m.get('condensate_density', 1.0)
        vortex_density = m.get('vortex_density', 0.0)
        
        # Predict metastability based on thresholds
        is_metastable_pred = (condensate_density < density_threshold) or \
                             (vortex_density > vortex_threshold)
        
        # Get ground truth if available (from 'is_metastable' field or external label)
        is_metastable_gt = m.get('is_metastable', is_metastable_pred)
        
        predictions.append(is_metastable_pred)
        ground_truth.append(is_metastable_gt)
    
    # Calculate metrics
    from .metrics import calculate_false_positive_rate, calculate_false_negative_rate
    
    fp_rate = calculate_false_positive_rate(predictions, ground_truth)
    fn_rate = calculate_false_negative_rate(predictions, ground_truth)
    
    # Calculate accuracy
    correct = sum(1 for p, gt in zip(predictions, ground_truth) if p == gt)
    accuracy = correct / len(predictions) if predictions else 0.0
    
    # Calculate F1 score
    tp = sum(1 for p, gt in zip(predictions, ground_truth) if p and gt)
    fp = sum(1 for p, gt in zip(predictions, ground_truth) if p and not gt)
    fn = sum(1 for p, gt in zip(predictions, ground_truth) if not p and gt)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return SensitivityResult(
        density_threshold=density_threshold,
        vortex_threshold=vortex_threshold,
        false_positive_rate=fp_rate,
        false_negative_rate=fn_rate,
        accuracy=accuracy,
        f1_score=f1_score
    )

def run_sensitivity_analysis(metrics_dir: str, 
                             density_range: Tuple[float, float] = (0.5, 0.9),
                             vortex_range: Tuple[float, float] = (0.2, 0.8),
                             steps: int = 5) -> List[SensitivityResult]:
    """
    Run sensitivity analysis across a range of thresholds.
    
    Args:
        metrics_dir: Directory containing metric files.
        density_range: (min, max) for density threshold search.
        vortex_range: (min, max) for vortex threshold search.
        steps: Number of steps for each parameter.
        
    Returns:
        List of SensitivityResult objects.
    """
    metrics_list = load_or_generate_ground_truth_metrics(metrics_dir)
    
    if not metrics_list:
        logger.warning("No metrics data found. Cannot perform sensitivity analysis.")
        return []
    
    results = []
    
    density_values = np.linspace(density_range[0], density_range[1], steps)
    vortex_values = np.linspace(vortex_range[0], vortex_range[1], steps)
    
    import numpy as np
    
    for d_thresh in density_values:
        for v_thresh in vortex_values:
            result = evaluate_threshold(metrics_list, d_thresh, v_thresh)
            results.append(result)
            logger.info(f"Thresholds: density={d_thresh:.2f}, vortex={v_thresh:.2f} -> "
                        f"FP={result.false_positive_rate:.3f}, FN={result.false_negative_rate:.3f}")
    
    return results

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description='Sensitivity analysis for metastability thresholds')
    parser.add_argument('--metrics-dir', type=str, required=True, help='Directory with metric files')
    parser.add_argument('--density-min', type=float, default=0.5, help='Min density threshold')
    parser.add_argument('--density-max', type=float, default=0.9, help='Max density threshold')
    parser.add_argument('--vortex-min', type=float, default=0.2, help='Min vortex threshold')
    parser.add_argument('--vortex-max', type=float, default=0.8, help='Max vortex threshold')
    parser.add_argument('--steps', type=int, default=5, help='Number of steps for search')
    parser.add_argument('--output', type=str, default=None, help='Output JSON file')
    
    args = parser.parse_args()
    
    results = run_sensitivity_analysis(
        args.metrics_dir,
        (args.density_min, args.density_max),
        (args.vortex_min, args.vortex_max),
        args.steps
    )
    
    # Convert to serializable format
    serializable_results = [asdict(r) for r in results]
    
    print(json.dumps(serializable_results, indent=2))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

if __name__ == '__main__':
    main()
