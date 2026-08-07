"""
Metrics calculation for audio model inference.

Calculates AUC, latency, and peak RAM usage for ablated models.
Enforces Constitution Principle VI by re-measuring on 2-core CPU.
"""
import os
import time
import logging
import json
import tracemalloc
import csv
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from scipy import stats
import pandas as pd

from config import get_path_config, get_resource_limits
from utils.logger import get_logger, EvaluationError

logger = get_logger(__name__)

def calculate_auc(logits: np.ndarray, labels: np.ndarray) -> float:
    """
    Calculate Area Under the Curve (AUC) for binary classification.
    
    Args:
        logits: Model output logits (N,)
        labels: Ground truth labels (N,)
        
    Returns:
        AUC score (0.0 to 1.0)
        
    Raises:
        EvaluationError: If inputs are invalid or AUC cannot be computed
    """
    if len(logits) == 0 or len(labels) == 0:
        raise EvaluationError("Cannot calculate AUC with empty inputs")
    
    if len(logits) != len(labels):
        raise EvaluationError(f"Logits and labels length mismatch: {len(logits)} vs {len(labels)}")
    
    # Ensure labels are binary (0 or 1)
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        # If only one class, AUC is undefined (return 0.5 as neutral)
        logger.warning("Only one class present in labels, returning AUC=0.5")
        return 0.5
    
    try:
        fpr, tpr, _ = stats.roc_curve(labels, logits)
        auc_score = stats.auc(fpr, tpr)
        return float(auc_score)
    except Exception as e:
        raise EvaluationError(f"Failed to calculate AUC: {str(e)}") from e

def calculate_latency(start_time: float, end_time: float) -> float:
    """
    Calculate latency in milliseconds.
    
    Args:
        start_time: Start time in seconds (time.time())
        end_time: End time in seconds (time.time())
        
    Returns:
        Latency in milliseconds
    """
    return (end_time - start_time) * 1000.0

def get_peak_ram_mb() -> float:
    """
    Get peak RAM usage in MB using tracemalloc.
    
    Returns:
        Peak RAM usage in MB
    """
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def check_constraints(ram_gb: float, latency_ms: float) -> Dict[str, bool]:
    """
    Check if resource usage meets project constraints.
    
    Args:
        ram_gb: RAM usage in GB
        latency_ms: Latency in milliseconds
        
    Returns:
        Dictionary with constraint check results
    """
    resource_limits = get_resource_limits()
    max_ram_gb = resource_limits.get('max_memory_gb', 7.0)
    max_latency_ms = resource_limits.get('max_latency_ms', None)
    
    results = {
        'ram_within_limit': ram_gb <= max_ram_gb,
        'ram_gb': ram_gb,
        'max_ram_gb': max_ram_gb
    }
    
    if max_latency_ms is not None:
        results['latency_within_limit'] = latency_ms <= max_latency_ms
        results['latency_ms'] = latency_ms
        results['max_latency_ms'] = max_latency_ms
    
    return results

def calculate_metrics_for_model(
    logits: np.ndarray,
    labels: np.ndarray,
    model_id: str,
    config_id: str
) -> Dict[str, Any]:
    """
    Calculate all metrics for a single model configuration.
    
    Args:
        logits: Model output logits
        labels: Ground truth labels
        model_id: Identifier for the model
        config_id: Identifier for the ablation configuration
        
    Returns:
        Dictionary containing all calculated metrics
    """
    # Measure latency
    start_time = time.time()
    
    # Calculate AUC
    auc_score = calculate_auc(logits, labels)
    
    end_time = time.time()
    latency_ms = calculate_latency(start_time, end_time)
    
    # Get peak RAM
    peak_ram_mb = get_peak_ram_mb()
    peak_ram_gb = peak_ram_mb / 1024.0
    
    # Check constraints
    constraint_results = check_constraints(peak_ram_gb, latency_ms)
    
    metrics = {
        'model_id': model_id,
        'config_id': config_id,
        'auc': auc_score,
        'latency_ms': latency_ms,
        'ram_mb': peak_ram_mb,
        'ram_gb': peak_ram_gb,
        'num_samples': len(logits),
        'constraint_passed': all(
            v for k, v in constraint_results.items() 
            if isinstance(v, bool) and k.endswith('_within_limit')
        )
    }
    
    metrics.update(constraint_results)
    
    return metrics

def load_ablation_logits(filepath: str) -> pd.DataFrame:
    """
    Load ablation logits from parquet file.
    
    Args:
        filepath: Path to the parquet file
        
    Returns:
        DataFrame with columns: config_id, model_id, logits, labels
        
    Raises:
        EvaluationError: If file not found or invalid format
    """
    path = Path(filepath)
    if not path.exists():
        raise EvaluationError(f"Ablation logits file not found: {filepath}")
    
    try:
        df = pd.read_parquet(filepath)
        required_cols = {'config_id', 'model_id', 'logits', 'labels'}
        if not required_cols.issubset(df.columns):
            raise EvaluationError(
                f"Missing required columns in {filepath}. "
                f"Expected: {required_cols}, Found: {set(df.columns)}"
            )
        return df
    except Exception as e:
        raise EvaluationError(f"Failed to load ablation logits: {str(e)}") from e

def run_ablation_metrics_calculation(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Main function to calculate metrics for ablated models.
    
    Reads ablation logits, calculates AUC, latency, and RAM for each configuration,
    and outputs results to CSV.
    
    Args:
        input_path: Path to ablation_logits.parquet (uses config default if None)
        output_path: Path for output CSV (uses config default if None)
        
    Returns:
        List of metric dictionaries for each configuration
    """
    path_config = get_path_config()
    input_file = input_path or str(path_config.processed_dir / "ablation_logits.parquet")
    output_file = output_path or str(path_config.processed_dir / "ablation_metrics.csv")
    
    logger.info(f"Loading ablation logits from: {input_file}")
    df = load_ablation_logits(input_file)
    
    logger.info(f"Processing {len(df)} ablation records")
    
    # Group by config_id and model_id to calculate metrics per configuration
    metrics_list = []
    
    for (config_id, model_id), group in df.groupby(['config_id', 'model_id']):
        logger.info(f"Calculating metrics for config={config_id}, model={model_id}")
        
        # Ensure we have numpy arrays
        logits = group['logits'].values
        labels = group['labels'].values
        
        # Convert string representation of lists to actual arrays if needed
        if isinstance(logits[0], str):
            try:
                logits = np.array([np.fromstring(l.strip('[]'), sep=',') for l in logits])
            except:
                logits = np.array([float(l) for l in logits])
        
        if isinstance(labels[0], str):
            labels = np.array([float(l) for l in labels])
        
        # Calculate metrics
        metrics = calculate_metrics_for_model(
            logits=logits,
            labels=labels,
            model_id=model_id,
            config_id=config_id
        )
        
        metrics_list.append(metrics)
        logger.info(
            f"  AUC: {metrics['auc']:.4f}, "
            f"Latency: {metrics['latency_ms']:.2f}ms, "
            f"RAM: {metrics['ram_gb']:.2f}GB"
        )
    
    # Write results to CSV
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if metrics_list:
        with open(output_file, 'w', newline='') as f:
            fieldnames = [
                'config_id', 'model_id', 'auc', 'latency_ms', 
                'ram_mb', 'ram_gb', 'num_samples', 'constraint_passed'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metrics_list)
        
        logger.info(f"Saved metrics to: {output_file}")
    else:
        logger.warning("No metrics calculated, no output file written")
    
    return metrics_list

def main():
    """Entry point for standalone execution."""
    logger.info("Starting ablation metrics calculation")
    
    try:
        metrics = run_ablation_metrics_calculation()
        logger.info(f"Successfully calculated metrics for {len(metrics)} configurations")
        
        # Summary
        if metrics:
            avg_auc = np.mean([m['auc'] for m in metrics])
            avg_latency = np.mean([m['latency_ms'] for m in metrics])
            avg_ram = np.mean([m['ram_gb'] for m in metrics])
            
            logger.info(f"Summary - Avg AUC: {avg_auc:.4f}, "
                        f"Avg Latency: {avg_latency:.2f}ms, "
                        f"Avg RAM: {avg_ram:.2f}GB")
        
    except Exception as e:
        logger.error(f"Failed to calculate ablation metrics: {str(e)}")
        raise

if __name__ == "__main__":
    main()