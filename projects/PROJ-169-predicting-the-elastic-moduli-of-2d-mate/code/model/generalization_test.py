"""Inter-family generalization test.

Measures MAPE drop on unseen families vs intra-family baseline.
Outputs: data/results/generalization_metrics.json
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from utils.logger import get_logger
from model.baseline_metrics import BaselineResult, BaselineReport, run_intra_family_baseline

logger = get_logger(__name__)

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)

def run_generalization_test(
    intra_family_metrics: Dict[str, float],
    inter_family_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Compare intra-family vs inter-family performance.

    Calculates the drop in performance when moving from seen families (intra)
    to unseen families (inter).

    Args:
        intra_family_metrics: Metrics from the intra-family baseline (T020a).
            Expected keys: 'mape', 'rmse', 'r2'.
        inter_family_metrics: Metrics from the inter-family test split (T019/T018).
            Expected keys: 'mape', 'rmse', 'r2'.

    Returns:
        Dictionary containing intra, inter, and the calculated drop metrics.
    """
    # Calculate drops (positive drop = performance degradation)
    mape_drop = intra_family_metrics['mape'] - inter_family_metrics['mape']
    rmse_drop = intra_family_metrics['rmse'] - inter_family_metrics['rmse']
    # R2: higher is better, so a drop means inter R2 < intra R2
    r2_drop = intra_family_metrics['r2'] - inter_family_metrics['r2']

    return {
        'intra_family': intra_family_metrics,
        'inter_family': inter_family_metrics,
        'generalization_drop': {
            'mape_drop': float(mape_drop),
            'rmse_drop': float(rmse_drop),
            'r2_drop': float(r2_drop)
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description="Run inter-family generalization test against intra-family baseline."
    )
    parser.add_argument(
        '--intra',
        required=True,
        help='Path to intra-family baseline metrics JSON (from T020a)'
    )
    parser.add_argument(
        '--inter',
        required=True,
        help='Path to inter-family test metrics JSON (from T019/T018)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for generalization metrics JSON'
    )
    args = parser.parse_args()

    # Load metrics
    logger.info(f"Loading intra-family metrics from {args.intra}")
    intra_path = Path(args.intra)
    if not intra_path.exists():
        raise FileNotFoundError(f"Intra-family metrics file not found: {intra_path}")
    intra = load_json(intra_path)

    logger.info(f"Loading inter-family metrics from {args.inter}")
    inter_path = Path(args.inter)
    if not inter_path.exists():
        raise FileNotFoundError(f"Inter-family metrics file not found: {inter_path}")
    inter = load_json(inter_path)

    # Run test
    results = run_generalization_test(intra, inter)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Generalization metrics saved to {output_path}")
    logger.info(f"MAPE Drop: {results['generalization_drop']['mape_drop']:.4f}")
    logger.info(f"RMSE Drop: {results['generalization_drop']['rmse_drop']:.4f}")
    logger.info(f"R2 Drop: {results['generalization_drop']['r2_drop']:.4f}")

if __name__ == '__main__':
    main()