"""
Statistical analysis module for US3: Boundary Analysis and Threshold Identification.

This module implements:
1. Data Aggregation: Merging baseline and flow metrics into paired datasets.
2. Kolmogorov-Smirnov (K-S) Test: Comparing error distributions.
3. Piecewise Regression: Identifying flow-magnitude thresholds.
4. Sensitivity Analysis: Sweeping cutoffs.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import asdict

import numpy as np
from scipy import stats as scipy_stats
import ruptures as rpt

from config import get_default_config, ensure_directories
from utils.logger import get_logger
from data.models import AnalysisResult

# Initialize logger
logger = get_logger(__name__)


def load_json_metrics(file_path: str) -> List[Dict[str, Any]]:
    """
    Safely loads a JSON metrics file.
    Raises FileNotFoundError or JSONDecodeError if the file is missing or invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle case where root is a list or a dict with a specific key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Common keys in our pipeline: 'metrics', 'results', 'data'
        if 'metrics' in data:
            return data['metrics']
        elif 'results' in data:
            return data['results']
        else:
            # Assume the dict itself contains records if it has expected keys
            # Or if it's a single record wrapped in a dict
            if 'clip_id' in data or 'background_ssim' in data:
                return [data]
            else:
                raise ValueError(f"Unexpected JSON structure in {file_path}: {list(data.keys())}")
    else:
        raise ValueError(f"Unexpected JSON root type in {file_path}: {type(data)}")


def aggregate_metrics_to_pairs(
    baseline_path: str,
    flow_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Merges baseline and flow metrics into paired datasets.
    
    Expects both files to contain lists of metric records with a common 'clip_id'.
    Returns two lists of dictionaries (baseline_records, flow_records) sorted by clip_id.
    
    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If clip_ids do not match between the two files.
    """
    logger.info(f"Loading baseline metrics from: {baseline_path}")
    baseline_data = load_json_metrics(baseline_path)
    
    logger.info(f"Loading flow metrics from: {flow_path}")
    flow_data = load_json_metrics(flow_path)
    
    if not baseline_data:
        raise ValueError("Baseline metrics file is empty.")
    if not flow_data:
        raise ValueError("Flow metrics file is empty.")
    
    # Index baseline by clip_id
    baseline_map = {r['clip_id']: r for r in baseline_data}
    flow_map = {r['clip_id']: r for r in flow_data}
    
    # Find common keys
    common_ids = sorted(set(baseline_map.keys()) & set(flow_map.keys()))
    
    if not common_ids:
        raise ValueError("No common clip_ids found between baseline and flow datasets.")
    
    logger.info(f"Found {len(common_ids)} matching clips for paired analysis.")
    
    # Construct paired lists
    baseline_pairs = [baseline_map[i] for i in common_ids]
    flow_pairs = [flow_map[i] for i in common_ids]
    
    return baseline_pairs, flow_pairs


def compute_kolmogorov_smirnov_test(
    baseline_records: List[Dict[str, Any]],
    flow_records: List[Dict[str, Any]],
    metric_key: str = 'background_ssim'
) -> Dict[str, Any]:
    """
    Performs the Kolmogorov-Smirnov test to compare distributions of a specific metric
    between baseline and flow methods.
    
    Args:
        baseline_records: List of baseline metric dicts.
        flow_records: List of flow metric dicts.
        metric_key: The key in the dict to compare (e.g., 'background_ssim', 'inference_time').
    
    Returns:
        A dictionary containing 'statistic' and 'pvalue'.
    """
    baseline_values = [r.get(metric_key) for r in baseline_records if r.get(metric_key) is not None]
    flow_values = [r.get(metric_key) for r in flow_records if r.get(metric_key) is not None]
    
    if len(baseline_values) < 2 or len(flow_values) < 2:
        logger.warning(f"Insufficient data for K-S test on '{metric_key}'.")
        return {'statistic': None, 'pvalue': None, 'error': 'Insufficient data'}
    
    try:
        statistic, pvalue = scipy_stats.ks_2samp(baseline_values, flow_values)
        return {
            'metric': metric_key,
            'statistic': float(statistic),
            'pvalue': float(pvalue),
            'n_baseline': len(baseline_values),
            'n_flow': len(flow_values)
        }
    except Exception as e:
        logger.error(f"K-S test failed for {metric_key}: {e}")
        return {'metric': metric_key, 'statistic': None, 'pvalue': None, 'error': str(e)}


def compute_piecewise_regression(
    flow_records: List[Dict[str, Any]],
    x_key: str = 'flow_magnitude_mean',
    y_key: str = 'background_ssim',
    min_segment_size: int = 5
) -> Dict[str, Any]:
    """
    Uses ruptures to detect change points (thresholds) in the relationship between
    flow magnitude and SSIM degradation.
    
    We model the data as a sequence of (x, y) sorted by x.
    We use the 'binseg' algorithm with 'l2' cost to find the point where the mean shifts.
    
    Args:
        flow_records: List of flow metric dicts.
        x_key: Key for flow magnitude (independent variable).
        y_key: Key for SSIM (dependent variable).
        min_segment_size: Minimum number of samples per segment.
    
    Returns:
        Dictionary containing detected thresholds, segment means, and model details.
    """
    # Extract and filter data
    data_points = []
    for r in flow_records:
        x = r.get(x_key)
        y = r.get(y_key)
        if x is not None and y is not None and not np.isnan(x) and not np.isnan(y):
            data_points.append((float(x), float(y)))
    
    if len(data_points) < min_segment_size * 2:
        logger.warning(f"Insufficient data points ({len(data_points)}) for piecewise regression.")
        return {'error': 'Insufficient data', 'thresholds': []}
    
    # Sort by x (flow magnitude)
    data_points.sort(key=lambda p: p[0])
    xs = np.array([p[0] for p in data_points])
    ys = np.array([p[1] for p in data_points])
    
    # Prepare signal for ruptures (expects 2D array: n_samples, n_features)
    # We are looking for a change in the mean of Y relative to X, 
    # but ruptures typically works on 1D signals or multivariate.
    # Here we treat Y as the signal and X as the index context.
    # However, standard ruptures change-point detection on 1D signal Y assumes X is ordered index.
    # Since we sorted by X, we can run change point detection on Y.
    
    signal = ys.reshape(-1, 1)
    
    try:
        # Use Binseg algorithm with L2 cost
        algo = rpt.Binseg(model="l2").fit(signal)
        # We look for 1 or 2 changes. Let's try to find 1 significant change point first.
        # We can also use `predict` with a penalty or `check` to find optimal number.
        # For simplicity in this context, we ask for 2 segments (1 change point) 
        # but allow the algorithm to find the best location.
        
        # Try to detect 1 change point
        result = algo.predict(n_bkps=1)
        # result is a list of indices where segments end. e.g., [idx1, n_samples]
        if len(result) > 1:
            change_idx = result[0]
            threshold_x = float(xs[change_idx])
            # Calculate means of segments
            seg1_y = ys[:change_idx]
            seg2_y = ys[change_idx:]
            
            return {
                'algorithm': 'binseg-l2',
                'n_samples': len(xs),
                'threshold_x': threshold_x,
                'segment_1_mean': float(np.mean(seg1_y)),
                'segment_2_mean': float(np.mean(seg2_y)),
                'segment_1_size': int(change_idx),
                'segment_2_size': int(len(xs) - change_idx),
                'x_range': [float(np.min(xs)), float(np.max(xs))]
            }
        else:
            return {'error': 'No change point detected', 'thresholds': []}
            
    except Exception as e:
        logger.error(f"Piecewise regression failed: {e}")
        return {'error': str(e), 'thresholds': []}


def run_sensitivity_analysis(
    baseline_records: List[Dict[str, Any]],
    flow_records: List[Dict[str, Any]],
    cutoffs: List[float]
) -> List[Dict[str, Any]]:
    """
    Sweeps across a set of cutoff values to analyze inconsistency rates.
    
    Args:
        baseline_records: Baseline metrics.
        flow_records: Flow metrics.
        cutoffs: List of flow magnitude cutoffs to test.
    
    Returns:
        List of results for each cutoff.
    """
    results = []
    for cutoff in cutoffs:
        # Filter flow records above cutoff
        flow_above = [r for r in flow_records if r.get('flow_magnitude_mean', 0) >= cutoff]
        baseline_above = [
            b for b in baseline_records 
            if any(f['clip_id'] == b['clip_id'] and f.get('flow_magnitude_mean', 0) >= cutoff for f in flow_records)
        ]
        
        if not flow_above or not baseline_above:
            results.append({
                'cutoff': cutoff,
                'n_samples': 0,
                'inconsistency_rate': None,
                'note': 'No samples above cutoff'
            })
            continue
        
        # Calculate mean SSIM difference
        baseline_ssim = np.mean([r.get('background_ssim', 0) for r in baseline_above])
        flow_ssim = np.mean([r.get('background_ssim', 0) for r in flow_above])
        
        # Inconsistency defined as absolute difference in stability
        inconsistency = abs(baseline_ssim - flow_ssim)
        
        results.append({
            'cutoff': cutoff,
            'n_samples': len(flow_above),
            'baseline_mean_ssim': float(baseline_ssim),
            'flow_mean_ssim': float(flow_ssim),
            'inconsistency_rate': float(inconsistency)
        })
    
    return results


def generate_analysis_summary(
    baseline_path: str,
    flow_path: str,
    output_path: str
) -> AnalysisResult:
    """
    Orchestrates the full statistical analysis:
    1. Aggregates data.
    2. Runs K-S test.
    3. Runs Piecewise Regression.
    4. Runs Sensitivity Analysis.
    5. Saves results to JSON.
    
    Returns the AnalysisResult object.
    """
    ensure_directories()
    config = get_default_config()
    
    logger.info("Starting statistical analysis aggregation...")
    try:
        baseline_records, flow_records = aggregate_metrics_to_pairs(baseline_path, flow_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to aggregate metrics: {e}")
        # Create a failed result object if possible, or raise
        raise e
    
    # 1. K-S Test
    ks_result_ssim = compute_kolmogorov_smirnov_test(baseline_records, flow_records, 'background_ssim')
    ks_result_time = compute_kolmogorov_smirnov_test(baseline_records, flow_records, 'inference_time')
    
    # 2. Piecewise Regression
    pw_result = compute_piecewise_regression(flow_records, 'flow_magnitude_mean', 'background_ssim')
    
    # 3. Sensitivity Analysis
    cutoffs = config.CUTOFFS
    sensitivity_results = run_sensitivity_analysis(baseline_records, flow_records, list(cutoffs))
    
    # Compile final result
    analysis_data = {
        'ks_test_ssim': ks_result_ssim,
        'ks_test_time': ks_result_time,
        'piecewise_regression': pw_result,
        'sensitivity_analysis': sensitivity_results,
        'total_clips_analyzed': len(baseline_records),
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to JSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    logger.info(f"Analysis summary saved to {output_path}")
    
    # Create AnalysisResult object for return
    result_obj = AnalysisResult(
        analysis_type="US3_Threshold_Analysis",
        data=analysis_data,
        status="completed"
    )
    
    return result_obj


def main():
    """
    Entry point for the stats analysis script.
    Expects baseline and flow results to be in the default metrics directory.
    """
    config = get_default_config()
    baseline_path = Path(config.DATA_DIR) / "metrics" / "baseline_results.json"
    flow_path = Path(config.DATA_DIR) / "metrics" / "flow_results.json"
    output_path = Path(config.DATA_DIR) / "metrics" / "analysis_results.json"
    
    if not baseline_path.exists():
        logger.error(f"Baseline results not found at {baseline_path}. Run US1 first.")
        return
    if not flow_path.exists():
        logger.error(f"Flow results not found at {flow_path}. Run US2 first.")
        return
    
    try:
        generate_analysis_summary(str(baseline_path), str(flow_path), str(output_path))
        logger.info("US3 Analysis completed successfully.")
    except Exception as e:
        logger.critical(f"US3 Analysis failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()