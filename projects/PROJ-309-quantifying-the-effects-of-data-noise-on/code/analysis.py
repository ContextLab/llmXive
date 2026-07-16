"""
Analysis module for computing metric errors and identifying critical thresholds.

Implements FR-007 (Error Calculation) and FR-008 (Threshold Identification).
"""
import os
import json
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np

from config import get_snr_levels, NoiseType
from utils.data_models import MetricResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_ground_truth_metrics(
    metrics_dir: str,
    system_type: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, MetricResult]:
    """
    Load ground truth metrics from the processed directory.
    
    Args:
        metrics_dir: Path to the directory containing ground truth metric JSON files.
        system_type: Optional filter for system type (e.g., 'lorenz', 'rossler').
        seed: Optional filter for specific seed.
        
    Returns:
        Dictionary mapping (system_type, seed) to MetricResult objects.
    """
    ground_truth = {}
    pattern = os.path.join(metrics_dir, "ground_truth_metrics_*.json")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No ground truth metric files found in {metrics_dir}")
        return ground_truth
        
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract system and seed from filename or data
            # Expected format: ground_truth_metrics_{seed}.json
            # Or data contains system_type and seed fields
            file_seed = None
            file_system = None
            
            # Try to parse from filename
            base_name = os.path.basename(file_path)
            if base_name.startswith("ground_truth_metrics_") and base_name.endswith(".json"):
                try:
                    file_seed = int(base_name.replace("ground_truth_metrics_", "").replace(".json", ""))
                except ValueError:
                    pass
                    
            if 'seed' in data:
                file_seed = data['seed']
            if 'system_type' in data:
                file_system = data['system_type']
                
            if seed is not None and file_seed != seed:
                continue
            if system_type is not None and file_system != system_type:
                continue
                
            key = (file_system, file_seed)
            ground_truth[key] = MetricResult(**data)
            logger.info(f"Loaded ground truth for {key} from {file_path}")
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            
    return ground_truth


def load_noisy_metrics(
    metrics_dir: str,
    snr_level: Optional[float] = None,
    noise_type: Optional[NoiseType] = None,
    system_type: Optional[str] = None,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load noisy metrics from the processed directory.
    
    Args:
        metrics_dir: Path to the directory containing noisy metric JSON files.
        snr_level: Optional filter for specific SNR level.
        noise_type: Optional filter for noise type.
        system_type: Optional filter for system type.
        seed: Optional filter for specific seed.
        
    Returns:
        List of dictionaries containing metric data.
    """
    noisy_metrics = []
    pattern = os.path.join(metrics_dir, "noisy_metrics_*.json")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No noisy metric files found in {metrics_dir}")
        return noisy_metrics
        
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Filter by criteria
            if snr_level is not None and data.get('snr_db') != snr_level:
                continue
            if noise_type is not None and data.get('noise_type') != noise_type.value:
                continue
            if system_type is not None and data.get('system_type') != system_type:
                continue
            if seed is not None and data.get('seed') != seed:
                continue
                
            noisy_metrics.append(data)
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            
    return noisy_metrics


def calculate_metric_error(
    computed_value: float,
    ground_truth_value: float,
    metric_name: str
) -> float:
    """
    Calculate the absolute percentage error between a computed value and ground truth.
    
    Implements FR-007: Error = |computed - ground_truth| / |ground_truth| * 100
    
    Args:
        computed_value: The metric value computed from noisy data.
        ground_truth_value: The ground truth metric value from clean data.
        metric_name: Name of the metric for logging purposes.
        
    Returns:
        Absolute percentage error.
        
    Raises:
        ValueError: If ground_truth_value is zero or near-zero to avoid division issues.
    """
    if abs(ground_truth_value) < 1e-10:
        logger.warning(f"Ground truth for {metric_name} is near zero, returning infinite error")
        return float('inf')
        
    error = abs(computed_value - ground_truth_value) / abs(ground_truth_value) * 100.0
    return error


def analyze_metric_degradation(
    ground_truth: Dict[str, MetricResult],
    noisy_metrics: List[Dict[str, Any]],
    metrics_of_interest: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Analyze metric degradation across noisy datasets compared to ground truth.
    
    Args:
        ground_truth: Dictionary of ground truth metrics.
        noisy_metrics: List of noisy metric results.
        metrics_of_interest: Optional list of specific metrics to analyze (default: all).
        
    Returns:
        List of dictionaries containing error analysis for each metric.
    """
    if metrics_of_interest is None:
        metrics_of_interest = ['correlation_dimension', 'lyapunov_exponent', 'fnn_rate']
        
    results = []
    
    for noisy_data in noisy_metrics:
        system_type = noisy_data.get('system_type')
        seed = noisy_data.get('seed')
        snr_db = noisy_data.get('snr_db')
        noise_type = noisy_data.get('noise_type')
        
        key = (system_type, seed)
        if key not in ground_truth:
            logger.warning(f"No ground truth found for {key}, skipping error calculation")
            continue
            
        gt = ground_truth[key]
        
        for metric_name in metrics_of_interest:
            computed_val = noisy_data.get(metric_name)
            gt_val = getattr(gt, metric_name, None)
            
            if computed_val is None or gt_val is None:
                continue
                
            error_pct = calculate_metric_error(computed_val, gt_val, metric_name)
            
            results.append({
                'system_type': system_type,
                'seed': seed,
                'snr_db': snr_db,
                'noise_type': noise_type,
                'metric_name': metric_name,
                'computed_value': computed_val,
                'ground_truth_value': gt_val,
                'error_percent': error_pct
            })
            
    return results


def identify_fnn_threshold(
    error_results: List[Dict[str, Any]],
    fnn_threshold_rate: float = 0.5,
    system_type: Optional[str] = None,
    noise_type: Optional[NoiseType] = None
) -> Optional[Dict[str, Any]]:
    """
    Identify the critical SNR threshold where FNN rate exceeds the specified limit.
    
    Implements FR-008: Iterate SNR levels from low to high, find the lowest SNR
    where FNN rate > threshold.
    
    Args:
        error_results: List of error analysis results.
        fnn_threshold_rate: The FNN rate threshold (default 0.5).
        system_type: Optional filter for system type.
        noise_type: Optional filter for noise type.
        
    Returns:
        Dictionary containing threshold information, or None if not found.
    """
    # Filter results for FNN metric and optional system/noise constraints
    fnn_results = [
        r for r in error_results
        if r['metric_name'] == 'fnn_rate'
        and (system_type is None or r['system_type'] == system_type)
        and (noise_type is None or r['noise_type'] == noise_type)
    ]
    
    if not fnn_results:
        logger.warning("No FNN results found to analyze threshold")
        return None
        
    # Group by SNR and find the average FNN rate at each SNR
    snr_fnn_map = {}
    for r in fnn_results:
        snr = r['snr_db']
        if snr not in snr_fnn_map:
            snr_fnn_map[snr] = []
        snr_fnn_map[snr].append(r['error_percent']) # Note: storing error_percent as proxy for FNN rate in this context, but we need actual FNN rate. 
        # Correction: We need to store the actual FNN rate, not error. 
        # Let's re-structure: we need the 'computed_value' which is the FNN rate.
        
    # Re-group properly
    snr_fnn_map = {}
    for r in fnn_results:
        snr = r['snr_db']
        if snr not in snr_fnn_map:
            snr_fnn_map[snr] = []
        snr_fnn_map[snr].append(r['computed_value']) # This is the actual FNN rate
        
    # Sort SNR levels
    sorted_snr = sorted(snr_fnn_map.keys())
    
    critical_snr = None
    critical_data = None
    
    for snr in sorted_snr:
        avg_fnn = np.mean(snr_fnn_map[snr])
        if avg_fnn > fnn_threshold_rate:
            critical_snr = snr
            # Find the original result object for this SNR to get full details
            for r in fnn_results:
                if r['snr_db'] == snr:
                    critical_data = r
                    break
            break
            
    if critical_snr is not None and critical_data is not None:
        return {
            'threshold_snr': critical_snr,
            'metric_name': 'fnn_rate',
            'fnn_rate': np.mean(snr_fnn_map[critical_snr]),
            'error_percent': critical_data['error_percent'],
            'system_type': critical_data['system_type'],
            'noise_type': critical_data['noise_type']
        }
        
    logger.info(f"No critical threshold found (FNN rate never exceeded {fnn_threshold_rate})")
    return None


def run_analysis_pipeline(
    metrics_dir: str,
    output_dir: str,
    snr_levels: Optional[List[float]] = None,
    system_types: Optional[List[str]] = None,
    noise_types: Optional[List[NoiseType]] = None
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: load data, compute errors, identify thresholds.
    
    Args:
        metrics_dir: Directory containing ground truth and noisy metrics.
        output_dir: Directory to write analysis results.
        snr_levels: Optional list of SNR levels to process.
        system_types: Optional list of system types to process.
        noise_types: Optional list of noise types to process.
        
    Returns:
        Dictionary containing analysis summary and paths to output files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load ground truth
    logger.info(f"Loading ground truth metrics from {metrics_dir}")
    ground_truth = load_ground_truth_metrics(metrics_dir)
    if not ground_truth:
        raise ValueError("No ground truth metrics found. Cannot proceed with analysis.")
        
    # Load noisy metrics
    logger.info(f"Loading noisy metrics from {metrics_dir}")
    noisy_metrics = load_noisy_metrics(
        metrics_dir,
        snr_level=None, # Load all
        noise_type=None,
        system_type=None,
        seed=None
    )
    if not noisy_metrics:
        raise ValueError("No noisy metrics found. Cannot proceed with analysis.")
        
    # Analyze degradation
    logger.info("Analyzing metric degradation")
    error_results = analyze_metric_degradation(ground_truth, noisy_metrics)
    
    # Save error results
    error_file = os.path.join(output_dir, "error_analysis.json")
    with open(error_file, 'w') as f:
        json.dump(error_results, f, indent=2)
    logger.info(f"Saved error analysis to {error_file}")
    
    # Identify critical thresholds
    thresholds = []
    for system in (system_types or ['lorenz', 'rossler']):
        for noise in (noise_types or list(NoiseType)):
            threshold = identify_fnn_threshold(
                error_results,
                system_type=system,
                noise_type=noise
            )
            if threshold:
                thresholds.append(threshold)
                
    # Save thresholds
    threshold_file = os.path.join(output_dir, "critical_thresholds.json")
    with open(threshold_file, 'w') as f:
        json.dump(thresholds, f, indent=2)
    logger.info(f"Saved critical thresholds to {threshold_file}")
    
    return {
        'error_analysis_file': error_file,
        'threshold_file': threshold_file,
        'num_errors': len(error_results),
        'num_thresholds': len(thresholds)
    }


def get_analysis_functions() -> List[str]:
    """Return list of public analysis functions."""
    return [
        'load_ground_truth_metrics',
        'load_noisy_metrics',
        'calculate_metric_error',
        'analyze_metric_degradation',
        'identify_fnn_threshold',
        'run_analysis_pipeline'
    ]
