"""
Sensitivity analysis for decision thresholds in aDDM simulations.

This module implements a sensitivity analysis that sweeps decision thresholds
across a range of low probability values and reports log-likelihood/AIC variation.
It addresses FR-005 requirements for threshold sensitivity testing.
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

# Import from existing API surface
from models.addm import aDDMChoiceOnly, run_single_simulation
from models.fit import load_preprocessed_data, compute_log_likelihood
from utils.logger import get_logger, setup_logging

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_threshold_sweep(
    data: pd.DataFrame,
    threshold_range: Tuple[float, float, int],
    salience_weight: float = 0.5,
    drift_rate: float = 0.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping decision thresholds.

    Args:
        data: Preprocessed data with choices and salience scores
        threshold_range: Tuple of (min_threshold, max_threshold, num_steps)
        salience_weight: Weight for salience in drift rate calculation
        drift_rate: Base drift rate parameter
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger = get_logger(__name__)
    logger.info(f"Starting threshold sweep: {threshold_range}")

    min_thresh, max_thresh, num_steps = threshold_range
    thresholds = np.linspace(min_thresh, max_thresh, num_steps)

    results = []
    n_samples = len(data)
    choices = data['choice'].values
    salience_scores = data['salience_score'].values

    # Pre-compute log-likelihoods for each threshold
    for i, threshold in enumerate(thresholds):
        logger.debug(f"Processing threshold {i+1}/{num_steps}: {threshold:.4f}")

        # Run simulation for each sample with current threshold
        log_likelihoods = []
        for idx in range(n_samples):
            salience = salience_scores[idx]
            choice = choices[idx]

            # Compute drift rate with salience component
            effective_drift = drift_rate + salience_weight * salience

            # Run single simulation
            try:
                sim_result = run_single_simulation(
                    drift=effective_drift,
                    threshold=threshold,
                    seed=seed + idx
                )
                # Compute log-likelihood for this sample
                ll = compute_log_likelihood(
                    sim_result['choice'],
                    choice,
                    threshold=threshold
                )
                log_likelihoods.append(ll)
            except Exception as e:
                logger.warning(f"Simulation failed for sample {idx}: {e}")
                log_likelihoods.append(0.0)  # Penalize failures

        total_ll = sum(log_likelihoods)
        # AIC = 2k - 2ln(L), where k=2 (drift, threshold)
        k = 2
        aic = 2 * k - 2 * total_ll

        results.append({
            'threshold': threshold,
            'log_likelihood': total_ll,
            'aic': aic,
            'n_samples': n_samples
        })

    return {
        'thresholds': [r['threshold'] for r in results],
        'log_likelihoods': [r['log_likelihood'] for r in results],
        'aic_values': [r['aic'] for r in results],
        'best_threshold': results[np.argmin([r['aic'] for r in results])]['threshold'],
        'min_aic': min([r['aic'] for r in results]),
        'parameters': {
            'salience_weight': salience_weight,
            'drift_rate': drift_rate,
            'threshold_range': threshold_range,
            'seed': seed
        }
    }

def compute_sensitivity_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute sensitivity metrics from threshold sweep results.

    Args:
        results: Output from run_threshold_sweep

    Returns:
        Dictionary with sensitivity metrics
    """
    aic_values = np.array(results['aic_values'])
    thresholds = np.array(results['thresholds'])

    # Compute AIC variation (range)
    aic_range = np.max(aic_values) - np.min(aic_values)

    # Compute threshold sensitivity (change in AIC per unit threshold)
    if len(thresholds) > 1:
        threshold_diff = np.diff(thresholds)
        aic_diff = np.diff(aic_values)
        sensitivity = np.abs(aic_diff / threshold_diff)
        mean_sensitivity = np.mean(sensitivity)
        max_sensitivity = np.max(sensitivity)
    else:
        mean_sensitivity = 0.0
        max_sensitivity = 0.0

    return {
        'aic_range': float(aic_range),
        'mean_sensitivity': float(mean_sensitivity),
        'max_sensitivity': float(max_sensitivity),
        'optimal_threshold': float(results['best_threshold']),
        'optimal_aic': float(results['min_aic'])
    }

def generate_sensitivity_report(
    results: Dict[str, Any],
    metrics: Dict[str, float],
    output_path: Path
) -> None:
    """
    Generate a comprehensive sensitivity analysis report.

    Args:
        results: Threshold sweep results
        metrics: Computed sensitivity metrics
        output_path: Path to write JSON report
    """
    report = {
        'analysis_type': 'threshold_sensitivity',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'results': results,
        'metrics': metrics,
        'interpretation': {
            'stability': 'high' if metrics['aic_range'] < 10 else 'medium' if metrics['aic_range'] < 50 else 'low',
            'recommendation': f"Optimal threshold: {metrics['optimal_threshold']:.4f} (AIC: {metrics['optimal_aic']:.2f})"
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logging.info(f"Sensitivity report written to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    setup_logging()
    logger = get_logger(__name__)

    # Configuration
    data_path = PROJECT_ROOT / 'data' / 'processed' / 'salience_preprocessed.csv'
    output_dir = PROJECT_ROOT / 'data' / 'processed'
    output_path = output_dir / 'threshold_sensitivity_report.json'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading preprocessed data from {data_path}")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    data = load_preprocessed_data(data_path)

    if data.empty:
        logger.error("No data available for sensitivity analysis")
        sys.exit(1)

    logger.info(f"Loaded {len(data)} samples for sensitivity analysis")

    # Define threshold range (low probability values as per FR-005)
    # Sweep from 0.1 to 0.9 in 10 steps
    threshold_range = (0.1, 0.9, 10)

    # Run sensitivity analysis
    logger.info("Running threshold sensitivity sweep...")
    start_time = time.time()

    results = run_threshold_sweep(
        data=data,
        threshold_range=threshold_range,
        salience_weight=0.5,
        drift_rate=0.0,
        seed=42
    )

    elapsed = time.time() - start_time
    logger.info(f"Sensitivity analysis completed in {elapsed:.2f} seconds")

    # Compute metrics
    metrics = compute_sensitivity_metrics(results)

    # Generate report
    generate_sensitivity_report(results, metrics, output_path)

    # Print summary
    print("\n" + "="*60)
    print("THRESHOLD SENSITIVITY ANALYSIS SUMMARY")
    print("="*60)
    print(f"Threshold range: {threshold_range[0]:.2f} to {threshold_range[1]:.2f} ({threshold_range[2]} steps)")
    print(f"Optimal threshold: {metrics['optimal_threshold']:.4f}")
    print(f"Optimal AIC: {metrics['optimal_aic']:.2f}")
    print(f"AIC range: {metrics['aic_range']:.2f}")
    print(f"Mean sensitivity: {metrics['mean_sensitivity']:.4f}")
    print(f"Max sensitivity: {metrics['max_sensitivity']:.4f}")
    print(f"Stability: {metrics.get('stability', 'unknown')}")
    print(f"Report saved to: {output_path}")
    print("="*60 + "\n")

    return results

if __name__ == '__main__':
    main()
