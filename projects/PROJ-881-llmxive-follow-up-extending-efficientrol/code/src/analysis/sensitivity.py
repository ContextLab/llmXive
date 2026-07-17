"""
Sensitivity analysis module for multiple-comparison correction and FDR calculation.

This module implements:
1. Bonferroni and Benjamini-Hochberg (BH) correction for p-values
2. False Discovery Rate (FDR) calculation
3. Comparison against nominal alpha level (0.05) to verify SC-005

Dependencies:
- statsmodels for multiple comparison procedures
- scipy for statistical functions
"""

import logging
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NOMINAL_ALPHA = 0.05
CORRECTION_METHODS = ['bonferroni', 'bh']


class SensitivityAnalysisResult:
    """Container for sensitivity analysis results."""

    def __init__(
        self,
        raw_p_values: List[float],
        corrected_p_values: Dict[str, List[float]],
        fdr_estimates: Dict[str, float],
        significant_counts: Dict[str, int],
        total_tests: int,
        alpha_level: float = NOMINAL_ALPHA,
        method_details: Optional[Dict[str, Any]] = None
    ):
        self.raw_p_values = raw_p_values
        self.corrected_p_values = corrected_p_values
        self.fdr_estimates = fdr_estimates
        self.significant_counts = significant_counts
        self.total_tests = total_tests
        self.alpha_level = alpha_level
        self.method_details = method_details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            'raw_p_values': self.raw_p_values,
            'corrected_p_values': self.corrected_p_values,
            'fdr_estimates': self.fdr_estimates,
            'significant_counts': self.significant_counts,
            'total_tests': self.total_tests,
            'alpha_level': self.alpha_level,
            'method_details': self.method_details
        }

    def __repr__(self) -> str:
        return (
            f"SensitivityAnalysisResult(total_tests={self.total_tests}, "
            f"alpha={self.alpha_level}, fdr={self.fdr_estimates})"
        )


def apply_bonferroni_correction(p_values: List[float]) -> Tuple[List[float], int]:
    """
    Apply Bonferroni correction to p-values.

    The Bonferroni correction multiplies each p-value by the number of tests,
    capping the result at 1.0.

    Args:
        p_values: List of raw p-values from statistical tests.

    Returns:
        Tuple of (corrected_p_values, count_significant_at_alpha)
    """
    if not p_values:
        return [], 0

    n_tests = len(p_values)
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    significant_count = sum(1 for p in corrected if p < NOMINAL_ALPHA)

    return corrected, significant_count


def apply_bh_correction(p_values: List[float]) -> Tuple[List[float], int]:
    """
    Apply Benjamini-Hochberg (BH) correction to p-values.

    The BH procedure controls the False Discovery Rate (FDR) by ranking
    p-values and applying a step-up procedure.

    Args:
        p_values: List of raw p-values from statistical tests.

    Returns:
        Tuple of (corrected_p_values, count_significant_at_alpha)
    """
    if not p_values:
        return [], 0

    # Use statsmodels for BH correction
    # multipletests returns (reject, p_corrected, p_corrected_fdr, alphac_Sidak, alphac_BH)
    _, p_corrected, _, _, _ = multipletests(
        p_values,
        alpha=NOMINAL_ALPHA,
        method='fdr_bh'
    )

    significant_count = sum(1 for p in p_corrected if p < NOMINAL_ALPHA)

    return list(p_corrected), significant_count


def calculate_fdr(raw_p_values: List[float], threshold: float = NOMINAL_ALPHA) -> float:
    """
    Calculate the estimated False Discovery Rate (FDR).

    FDR = E[V/R] where V is false discoveries and R is total discoveries.
    Using the Benjamini-Hochberg procedure, the FDR is estimated as:
    FDR ≈ (m * alpha) / R where m is total tests, alpha is threshold, R is rejections.

    Args:
        raw_p_values: List of raw p-values.
        threshold: Significance threshold (default 0.05).

    Returns:
        Estimated FDR value.
    """
    if not raw_p_values:
        return 0.0

    m = len(raw_p_values)
    rejections = sum(1 for p in raw_p_values if p < threshold)

    if rejections == 0:
        return 0.0

    # Standard FDR estimate: (m * alpha) / R
    fdr_estimate = (m * threshold) / rejections
    return min(fdr_estimate, 1.0)


def analyze_sensitivity(
    p_values: List[float],
    correction_methods: Optional[List[str]] = None,
    alpha_level: float = NOMINAL_ALPHA
) -> SensitivityAnalysisResult:
    """
    Perform full sensitivity analysis with multiple correction methods.

    This function:
    1. Applies Bonferroni and BH corrections to the input p-values
    2. Calculates FDR estimates for each method
    3. Counts significant results at the specified alpha level
    4. Compares results against the nominal alpha level to verify SC-005

    Args:
        p_values: List of raw p-values from statistical tests.
        correction_methods: List of correction methods to apply. Defaults to ['bonferroni', 'bh'].
        alpha_level: Nominal significance level (default 0.05).

    Returns:
        SensitivityAnalysisResult containing all correction results and FDR estimates.

    Raises:
        ValueError: If p_values contains invalid values (negative or > 1).
        ValueError: If an unknown correction method is specified.
    """
    if not p_values:
        logger.warning("Empty p-values list provided. Returning empty result.")
        return SensitivityAnalysisResult(
            raw_p_values=[],
            corrected_p_values={},
            fdr_estimates={},
            significant_counts={},
            total_tests=0,
            alpha_level=alpha_level
        )

    # Validate p-values
    for i, p in enumerate(p_values):
        if not (0.0 <= p <= 1.0):
            raise ValueError(
                f"Invalid p-value at index {i}: {p}. "
                f"P-values must be in range [0, 1]."
            )

    if correction_methods is None:
        correction_methods = CORRECTION_METHODS

    # Validate correction methods
    for method in correction_methods:
        if method not in CORRECTION_METHODS:
            raise ValueError(
                f"Unknown correction method: {method}. "
                f"Supported methods: {CORRECTION_METHODS}"
            )

    corrected_p_values = {}
    significant_counts = {}
    fdr_estimates = {}
    method_details = {}

    for method in correction_methods:
        logger.info(f"Applying {method} correction to {len(p_values)} p-values...")

        if method == 'bonferroni':
            corrected, sig_count = apply_bonferroni_correction(p_values)
            fdr = calculate_fdr(corrected, alpha_level)
            method_details[method] = {
                'description': 'Bonferroni correction (family-wise error rate control)',
                'formula': 'p_corrected = min(p * m, 1.0)'
            }
        elif method == 'bh':
            corrected, sig_count = apply_bh_correction(p_values)
            fdr = calculate_fdr(corrected, alpha_level)
            method_details[method] = {
                'description': 'Benjamini-Hochberg correction (FDR control)',
                'formula': 'Step-up procedure based on ranked p-values'
            }

        corrected_p_values[method] = corrected
        significant_counts[method] = sig_count
        fdr_estimates[method] = fdr

        logger.info(
            f"{method}: {sig_count}/{len(p_values)} significant at alpha={alpha_level}, "
            f"estimated FDR={fdr:.4f}"
        )

    # SC-005 Verification: Compare FDR against nominal alpha
    verification_results = {}
    for method in correction_methods:
        fdr = fdr_estimates[method]
        is_verified = fdr <= alpha_level
        verification_results[method] = {
            'fdr': fdr,
            'alpha_level': alpha_level,
            'verified': is_verified,
            'message': (
                f"FDR ({fdr:.4f}) {'<=' if is_verified else '>'} alpha ({alpha_level}). "
                f"SC-005 {'VERIFIED' if is_verified else 'NOT VERIFIED'} for {method}."
            )
        }
        logger.info(verification_results[method]['message'])

    method_details['verification'] = verification_results

    return SensitivityAnalysisResult(
        raw_p_values=p_values,
        corrected_p_values=corrected_p_values,
        fdr_estimates=fdr_estimates,
        significant_counts=significant_counts,
        total_tests=len(p_values),
        alpha_level=alpha_level,
        method_details=method_details
    )


def load_p_values_from_analysis_results(
    result_file_path: Union[str, Path]
) -> List[float]:
    """
    Load p-values from a logistic regression analysis result file.

    Expects a JSON file with structure:
    {
        "results": [
            {"p_value": 0.03, ...},
            ...
        ]
    }

    Args:
        result_file_path: Path to the JSON file containing analysis results.

    Returns:
        List of p-values extracted from the results.

    Raises:
        FileNotFoundError: If the result file does not exist.
        ValueError: If the file format is invalid or p-values cannot be extracted.
    """
    result_path = Path(result_file_path)

    if not result_path.exists():
        raise FileNotFoundError(f"Result file not found: {result_path}")

    with open(result_path, 'r') as f:
        data = json.load(f)

    if 'results' not in data:
        raise ValueError("Invalid result file format: missing 'results' key")

    p_values = []
    for i, item in enumerate(data['results']):
        if 'p_value' not in item:
            logger.warning(f"Skipping result {i}: missing 'p_value' field")
            continue

        try:
            p_val = float(item['p_value'])
            p_values.append(p_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid p_value at index {i}: {item['p_value']}") from e

    if not p_values:
        raise ValueError("No valid p-values found in the result file")

    logger.info(f"Loaded {len(p_values)} p-values from {result_path}")
    return p_values


def write_sensitivity_report(
    result: SensitivityAnalysisResult,
    output_path: Union[str, Path]
) -> None:
    """
    Write sensitivity analysis results to a JSON file.

    Args:
        result: SensitivityAnalysisResult object to serialize.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        'summary': {
            'total_tests': result.total_tests,
            'alpha_level': result.alpha_level,
            'fdr_estimates': result.fdr_estimates,
            'significant_counts': result.significant_counts
        },
        'detailed_results': result.to_dict(),
        'sc005_verification': result.method_details.get('verification', {})
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sensitivity analysis report written to {output_path}")


def main() -> None:
    """
    Main entry point for sensitivity analysis.

    Usage:
        python -m src.analysis.sensitivity --input <result_file.json> --output <report.json>

    This script:
    1. Loads p-values from a logistic regression analysis result file
    2. Applies Bonferroni and BH corrections
    3. Calculates FDR estimates
    4. Verifies SC-005 (FDR <= alpha)
    5. Writes a detailed report to JSON
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Perform sensitivity analysis with multiple-comparison correction'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the logistic regression analysis result file (JSON)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=False,
        default='projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/results/sensitivity_report.json',
        help='Path to the output sensitivity analysis report (JSON)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=NOMINAL_ALPHA,
        help=f'Nominal alpha level (default: {NOMINAL_ALPHA})'
    )

    args = parser.parse_args()

    logger.info(f"Starting sensitivity analysis with input: {args.input}")
    logger.info(f"Alpha level: {args.alpha}")

    try:
        # Load p-values
        p_values = load_p_values_from_analysis_results(args.input)
        logger.info(f"Loaded {len(p_values)} p-values")

        # Perform sensitivity analysis
        result = analyze_sensitivity(
            p_values=p_values,
            correction_methods=['bonferroni', 'bh'],
            alpha_level=args.alpha
        )

        # Write report
        write_sensitivity_report(result, args.output)

        # Print summary
        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total tests: {result.total_tests}")
        print(f"Alpha level: {result.alpha_level}")
        print()
        for method in result.corrected_p_values:
            print(f"{method.upper()}:")
            print(f"  Significant: {result.significant_counts[method]}/{result.total_tests}")
            print(f"  Estimated FDR: {result.fdr_estimates[method]:.4f}")
            verification = result.method_details['verification'][method]
            print(f"  SC-005: {verification['message']}")
        print("=" * 60)

        logger.info("Sensitivity analysis completed successfully")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()
