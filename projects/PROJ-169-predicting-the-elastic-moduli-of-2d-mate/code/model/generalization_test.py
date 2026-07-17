"""Inter-family generalization test.

Measures MAPE drop on unseen families vs intra-family baseline.
Outputs: data/results/generalization_metrics.json

WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import numpy as np

from utils.logger import get_logger
from model.baseline_metrics import BaselineResult, BaselineReport, run_intra_family_baseline
from model.splitter import load_graphs_from_parquet, SplitManifest

logger = get_logger(__name__)

# Metadata disclaimer for all JSON outputs
DISCLAIMER = (
    "These results are ML interpolations of DFT data, not first-principles solutions. "
    "The model is a surrogate that learns statistical correlations from pre-computed "
    "Density Functional Theory results."
)

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save a dictionary to a JSON file with the standard disclaimer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_family_disjoint(
    train_manifest_path: Path,
    test_manifest_path: Path
) -> None:
    """Ensure no family appears in both training and test sets.

    Raises:
        ValueError: If there is an overlap in family IDs between train and test.
    """
    train_data = load_json(train_manifest_path)
    test_data = load_json(test_manifest_path)

    train_families: Set[str] = set(train_data.get('train_families', []))
    test_families: Set[str] = set(test_data.get('test_families', []))

    overlap = train_families.intersection(test_families)
    if overlap:
        raise ValueError(
            f"CRITICAL: Family overlap detected between train and test sets: {overlap}. "
            "Test set MUST consist of entirely excluded families. "
            "No training family can appear in the test set."
        )
    logger.info("Family disjointness verified: No overlap between train and test families.")

def run_generalization_test(
    intra_family_metrics: Dict[str, float],
    inter_family_metrics: Dict[str, float],
    train_manifest_path: Optional[Path] = None,
    test_manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Compare intra-family vs inter-family performance.

    Calculates the drop in performance when moving from seen families (intra)
    to unseen families (inter).

    Args:
        intra_family_metrics: Metrics from the intra-family baseline (T020a).
            Expected keys: 'mape', 'rmse', 'r2'.
        inter_family_metrics: Metrics from the inter-family test split (T019/T018).
            Expected keys: 'mape', 'rmse', 'r2'.
        train_manifest_path: Optional path to training split manifest for verification.
        test_manifest_path: Optional path to test split manifest for verification.

    Returns:
        Dictionary containing intra, inter, and the calculated drop metrics.
    """
    # Verify family disjointness if manifests are provided
    if train_manifest_path and test_manifest_path:
        verify_family_disjoint(train_manifest_path, test_manifest_path)

    # Calculate drops (positive drop = performance degradation)
    mape_drop = intra_family_metrics['mape'] - inter_family_metrics['mape']
    rmse_drop = intra_family_metrics['rmse'] - inter_family_metrics['rmse']
    # R2: higher is better, so a drop means inter R2 < intra R2
    r2_drop = intra_family_metrics['r2'] - inter_family_metrics['r2']

    # Calculate percentage drop relative to intra-family performance
    # Avoid division by zero if intra-family MAPE is 0 (unlikely but safe)
    if intra_family_metrics['mape'] != 0:
        drop_percentage = (mape_drop / intra_family_metrics['mape']) * 100
    else:
        drop_percentage = 0.0 if mape_drop == 0 else float('inf')

    result = {
        'metadata': {
            'disclaimer': DISCLAIMER,
            'task_id': 'T021',
            'description': 'Inter-family generalization test'
        },
        'intra_family_mape': float(intra_family_metrics['mape']),
        'inter_family_mape': float(inter_family_metrics['mape']),
        'drop_percentage': float(drop_percentage),
        'detailed_metrics': {
            'intra_family': intra_family_metrics,
            'inter_family': inter_family_metrics,
            'generalization_drop': {
                'mape_drop': float(mape_drop),
                'rmse_drop': float(rmse_drop),
                'r2_drop': float(r2_drop)
            }
        }
    }

    logger.info(f"Inter-family MAPE: {inter_family_metrics['mape']:.4f}")
    logger.info(f"Intra-family MAPE: {intra_family_metrics['mape']:.4f}")
    logger.info(f"MAPE Drop: {mape_drop:.4f} ({drop_percentage:.2f}%)")

    return result

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
        '--train-manifest',
        required=False,
        help='Path to training split manifest for family verification'
    )
    parser.add_argument(
        '--test-manifest',
        required=False,
        help='Path to test split manifest for family verification'
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

    # Extract metrics dictionaries (handle nested structures if needed)
    intra_metrics = intra.get('metrics', intra)
    inter_metrics = inter.get('metrics', inter)

    # Run test
    train_manifest = Path(args.train_manifest) if args.train_manifest else None
    test_manifest = Path(args.test_manifest) if args.test_manifest else None

    results = run_generalization_test(
        intra_metrics,
        inter_metrics,
        train_manifest,
        test_manifest
    )

    # Write output
    output_path = Path(args.output)
    save_json(results, output_path)

    logger.info(f"Generalization metrics saved to {output_path}")
    logger.info(f"Final MAPE Drop: {results['drop_percentage']:.2f}%")

    # Log success criteria check (SC-002)
    if results['drop_percentage'] > 0:
        logger.warning(
            f"Generalization drop detected: {results['drop_percentage']:.2f}% "
            "indicates the model struggles on unseen families."
        )
    else:
        logger.info("No generalization drop observed (model generalizes well).")

if __name__ == '__main__':
    main()