"""
Verification module for SNR bin coverage and tolerance compliance.

This module implements the verification logic for Task T013a:
- Verify that stratified bins (8-14, 14-20, 20-30, 30-50) collectively cover [8, 50].
- Verify that individual injected signals meet the ±0.5 SNR tolerance.
"""

import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Constants defined from the project specification
TARGET_SNR_RANGE: Tuple[float, float] = (8.0, 50.0)
SNR_BINS: List[Tuple[float, float]] = [
    (8.0, 14.0),
    (14.0, 20.0),
    (20.0, 30.0),
    (30.0, 50.0)
]
SNR_TOLERANCE: float = 0.5

logger = logging.getLogger(__name__)


def verify_bin_coverage(
    actual_snr_values: List[float],
    target_bins: List[Tuple[float, float]] = SNR_BINS,
    full_range: Tuple[float, float] = TARGET_SNR_RANGE
) -> Dict[str, Any]:
    """
    Verify that the provided SNR values collectively cover the full target range
    and that each bin is populated.

    Args:
        actual_snr_values: List of measured SNR values from injected signals.
        target_bins: List of (min, max) tuples defining the stratified bins.
        full_range: The overall expected range (min, max).

    Returns:
        Dictionary with verification results:
        - 'full_range_covered': bool
        - 'bin_coverage': Dict[bin_index, 'covered' | 'empty']
        - 'details': Human-readable summary
    """
    if not actual_snr_values:
        return {
            'full_range_covered': False,
            'bin_coverage': {i: 'empty' for i in range(len(target_bins))},
            'details': 'No SNR values provided.'
        }

    snr_array = np.array(actual_snr_values)
    min_snr = float(np.min(snr_array))
    max_snr = float(np.max(snr_array))

    # Check full range coverage
    # We consider the range covered if min <= lower_bound and max >= upper_bound
    lower_bound, upper_bound = full_range
    full_range_covered = (min_snr <= lower_bound) and (max_snr >= upper_bound)

    # Check each bin
    bin_coverage = {}
    bin_counts = {i: 0 for i in range(len(target_bins))}
    bin_min_max = {i: (float('inf'), float('-inf')) for i in range(len(target_bins))}

    for snr in snr_array:
        for i, (b_min, b_max) in enumerate(target_bins):
            # Include lower bound, exclude upper bound, except for last bin
            if i == len(target_bins) - 1:
                in_bin = (snr >= b_min) and (snr <= b_max)
            else:
                in_bin = (snr >= b_min) and (snr < b_max)

            if in_bin:
                bin_counts[i] += 1
                bin_min_max[i] = (
                    min(bin_min_max[i][0], snr),
                    max(bin_min_max[i][1], snr)
                )

    coverage_details = {}
    for i in range(len(target_bins)):
        if bin_counts[i] > 0:
            coverage_details[i] = 'covered'
        else:
            coverage_details[i] = 'empty'

    # Construct details string
    details_lines = [
        f"Full Range Check: [{min_snr:.2f}, {max_snr:.2f}] vs Target [{lower_bound}, {upper_bound}]",
        f"  -> {'PASS' if full_range_covered else 'FAIL'}",
        "Bin Coverage:"
    ]

    for i, (b_min, b_max) in enumerate(target_bins):
        status = coverage_details[i]
        count = bin_counts[i]
        if status == 'covered':
          # Get the range of values actually found in this bin
          found_min, found_max = bin_min_max[i]
          details_lines.append(
              f"  Bin {i} ({b_min}-{b_max}): {count} signals, range [{found_min:.2f}, {found_max:.2f}] -> {status.upper()}"
          )
        else:
            details_lines.append(f"  Bin {i} ({b_min}-{b_max}): 0 signals -> {status.upper()}")

    return {
        'full_range_covered': full_range_covered,
        'bin_coverage': coverage_details,
        'bin_counts': bin_counts,
        'details': '\n'.join(details_lines)
    }


def verify_snr_tolerance(
    target_snr_values: List[float],
    actual_snr_values: List[float],
    tolerance: float = SNR_TOLERANCE
) -> Dict[str, Any]:
    """
    Verify that each injected signal's measured SNR is within the specified tolerance
    of its target SNR.

    Args:
        target_snr_values: List of target SNR values used for injection.
        actual_snr_values: List of measured SNR values from the generated data.
        tolerance: Maximum allowed absolute difference (default 0.5).

    Returns:
        Dictionary with verification results:
        - 'all_within_tolerance': bool
        - 'violations': List of dicts with index, target, actual, diff
        - 'summary': Human-readable summary
    """
    if len(target_snr_values) != len(actual_snr_values):
        raise ValueError(
            f"Length mismatch: target ({len(target_snr_values)}) != actual ({len(actual_snr_values)})"
        )

    target_arr = np.array(target_snr_values)
    actual_arr = np.array(actual_snr_values)
    diffs = np.abs(actual_arr - target_arr)

    violations = []
    for i, (target, actual, diff) in enumerate(zip(target_arr, actual_arr, diffs)):
        if diff > tolerance:
            violations.append({
                'index': i,
                'target': float(target),
                'actual': float(actual),
                'diff': float(diff)
            })

    all_within = len(violations) == 0

    summary_lines = [
        f"Tolerance Check: |Actual - Target| <= {tolerance}",
        f"Total Signals: {len(target_arr)}",
        f"Violations: {len(violations)} ({len(violations)/len(target_arr)*100:.2f}%)",
        f"Result: {'PASS' if all_within else 'FAIL'}"
    ]

    if violations:
        summary_lines.append("Violations (first 5):")
        for v in violations[:5]:
            summary_lines.append(
                f"  Idx {v['index']}: Target={v['target']:.2f}, Actual={v['actual']:.2f}, Diff={v['diff']:.3f}"
            )
        if len(violations) > 5:
            summary_lines.append(f"  ... and {len(violations) - 5} more.")

    return {
        'all_within_tolerance': all_within,
        'violations': violations,
        'max_diff': float(np.max(diffs)),
        'mean_diff': float(np.mean(diffs)),
        'summary': '\n'.join(summary_lines)
    }


def validate_dataset(
    dataset_path: str,
    target_snr_field: str = 'target_snr',
    actual_snr_field: str = 'measured_snr'
) -> Dict[str, Any]:
    """
    Load an HDF5 dataset and run both bin coverage and tolerance verification.

    Args:
        dataset_path: Path to the HDF5 file containing the waveform dataset.
        target_snr_field: Name of the field containing target SNR values.
        actual_snr_field: Name of the field containing measured SNR values.

    Returns:
        Combined verification report.
    """
    import h5py

    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path} to verify T013a...")

    with h5py.File(path, 'r') as f:
        # Check if fields exist
        if target_snr_field not in f:
            raise KeyError(f"Field '{target_snr_field}' not found in {dataset_path}")
        if actual_snr_field not in f:
            raise KeyError(f"Field '{actual_snr_field}' not found in {dataset_path}")

        target_snr = list(f[target_snr_field][:])
        actual_snr = list(f[actual_snr_field][:])

    logger.info(f"Loaded {len(target_snr)} signals.")

    coverage_result = verify_bin_coverage(actual_snr)
    tolerance_result = verify_snr_tolerance(target_snr, actual_snr)

    return {
        'dataset_path': str(path),
        'signal_count': len(target_snr),
        'bin_coverage': coverage_result,
        'snr_tolerance': tolerance_result,
        'overall_pass': coverage_result['full_range_covered'] and tolerance_result['all_within_tolerance']
    }


def main():
    """
    CLI entry point for T013a verification.
    Usage: python -m src.verify_snr_bins --dataset data/processed/waveforms_pilot_123.h5
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Verify SNR bin coverage and tolerance (T013a)")
    parser.add_argument(
        '--dataset',
        type=str,
        required=True,
        help='Path to the HDF5 dataset to verify'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to save JSON report (optional)'
    )

    args = parser.parse_args()

    try:
        report = validate_dataset(args.dataset)
        print("\n" + "="*60)
        print("T013a VERIFICATION REPORT")
        print("="*60)
        print(report['bin_coverage']['details'])
        print("\n" + report['snr_tolerance']['summary'])
        print("\n" + "="*60)
        print(f"OVERALL STATUS: {'PASS' if report['overall_pass'] else 'FAIL'}")
        print("="*60)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.output}")

        return 0 if report['overall_pass'] else 1

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    exit(main())
