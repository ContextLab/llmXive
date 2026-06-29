"""
Multiple comparison correction utilities for hypothesis testing.

Implements Bonferroni correction and related methods to control family-wise error rate
when performing multiple hypothesis tests, addressing FR-007 requirements.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction controls the family-wise error rate (FWER) by
    dividing the significance threshold alpha by the number of tests.

    Parameters
    ----------
    p_values : List[float]
        List of raw p-values from hypothesis tests.
    alpha : float
        Desired family-wise error rate (default: 0.05).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'corrected_p_values': List of Bonferroni-corrected p-values
        - 'adjusted_alpha': The adjusted significance threshold (alpha / n_tests)
        - 'significant_indices': Indices of tests that remain significant after correction
        - 'num_tests': Total number of tests performed
        - 'num_significant': Number of tests significant after correction
        - 'correction_method': Name of the correction method used

    Notes
    -----
    The Bonferroni correction is conservative. For large numbers of tests,
    consider using the Benjamini-Hochberg procedure for false discovery rate control.
    """
    if not p_values:
        logger.warning("Empty p-values list provided to bonferroni_correction")
        return {
            'corrected_p_values': [],
            'adjusted_alpha': alpha,
            'significant_indices': [],
            'num_tests': 0,
            'num_significant': 0,
            'correction_method': 'bonferroni'
        }

    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests

    # Clip p-values to [0, 1] range to handle numerical precision issues
    p_values_clipped = [max(0.0, min(1.0, p)) for p in p_values]

    # Bonferroni correction: multiply p-values by number of tests, cap at 1.0
    corrected_p_values = [min(1.0, p * n_tests) for p in p_values_clipped]

    # Identify significant results after correction
    significant_indices = [
        i for i, p in enumerate(corrected_p_values)
        if p < adjusted_alpha
    ]

    result = {
        'corrected_p_values': corrected_p_values,
        'adjusted_alpha': adjusted_alpha,
        'significant_indices': significant_indices,
        'num_tests': n_tests,
        'num_significant': len(significant_indices),
        'correction_method': 'bonferroni'
    }

    logger.info(
        f"Bonferroni correction applied: {n_tests} tests, "
        f"adjusted alpha = {adjusted_alpha:.6f}, "
        f"{len(significant_indices)} significant"
    )

    return result


def apply_correction_if_needed(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction only if more than 3 hypothesis tests are run.

    This function implements the FR-007 requirement: correction is applied
    conditionally based on the number of tests.

    Parameters
    ----------
    p_values : List[float]
        List of raw p-values from hypothesis tests.
    alpha : float
        Desired significance level (default: 0.05).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'corrected': Boolean indicating if correction was applied
        - 'correction_result': Result dictionary from correction function
        - 'num_tests': Number of tests performed
        - 'reason': Explanation of whether correction was applied and why

    Notes
    -----
    Per FR-007: "Implement multiple-comparison correction (Bonferroni) if >3
    hypothesis tests are run". This threshold is commonly used to distinguish
    between a small number of planned comparisons and exploratory analyses.
    """
    n_tests = len(p_values)

    if n_tests > 3:
        correction_result = bonferroni_correction(p_values, alpha)
        correction_result['corrected'] = True
        correction_result['reason'] = (
            f"Bonferroni correction applied because {n_tests} tests > 3 threshold"
        )
        logger.info(correction_result['reason'])
    else:
        # No correction needed, return original p-values
        correction_result = {
            'corrected_p_values': p_values,
            'adjusted_alpha': alpha,
            'significant_indices': [
                i for i, p in enumerate(p_values) if p < alpha
            ],
            'num_tests': n_tests,
            'num_significant': sum(1 for p in p_values if p < alpha),
            'correction_method': 'none',
            'corrected': False
        }
        correction_result['reason'] = (
            f"No correction applied: {n_tests} tests <= 3 threshold"
        )
        logger.info(correction_result['reason'])

    return correction_result


def generate_correction_report(
    p_values: List[float],
    test_names: Optional[List[str]] = None,
    alpha: float = 0.05,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive report of multiple comparison correction results.

    Parameters
    ----------
    p_values : List[float]
        List of raw p-values.
    test_names : Optional[List[str]]
        Optional list of test names for reporting. If not provided, generic names
        will be used.
    alpha : float
        Significance level.
    output_path : Optional[Path]
        If provided, write JSON report to this path.

    Returns
    -------
    Dict[str, Any]
        Complete report dictionary with all correction results and metadata.
    """
    n_tests = len(p_values)
    test_labels = test_names or [f"Test_{i+1}" for i in range(n_tests)]

    correction_result = apply_correction_if_needed(p_values, alpha)

    # Build detailed report
    report = {
        'summary': {
            'num_tests': n_tests,
            'correction_applied': correction_result['corrected'],
            'correction_method': correction_result.get('correction_method', 'none'),
            'reason': correction_result.get('reason', ''),
            'original_alpha': alpha,
            'adjusted_alpha': correction_result['adjusted_alpha'],
            'num_significant_before': sum(1 for p in p_values if p < alpha),
            'num_significant_after': correction_result['num_significant']
        },
        'test_results': []
    }

    for i, (name, raw_p, corrected_p) in enumerate(zip(
        test_labels, p_values, correction_result['corrected_p_values']
    )):
        is_significant_before = raw_p < alpha
        is_significant_after = corrected_p < correction_result['adjusted_alpha']

        report['test_results'].append({
            'test_name': name,
            'raw_p_value': raw_p,
            'corrected_p_value': corrected_p,
            'significant_before_correction': is_significant_before,
            'significant_after_correction': is_significant_after,
            'index': i
        })

    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            import json
            json.dump(report, f, indent=2)
        logger.info(f"Correction report written to {output_path}")

    return report


def main():
    """
    Demonstrate Bonferroni correction functionality with example data.

    This function runs when the script is executed directly and provides
    a practical example of the correction workflow.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example: Simulate p-values from multiple hypothesis tests
    # These could come from comparing salience effects across different conditions
    example_p_values = [0.001, 0.02, 0.04, 0.08, 0.15, 0.03]
    test_names = [
        "Salience_effect_young",
        "Salience_effect_elderly",
        "Salience_effect_males",
        "Salience_effect_females",
        "Salience_effect_pets",
        "Salience_effect_social_status"
    ]

    print("=" * 60)
    print("Multiple Comparison Correction (Bonferroni) Demo")
    print("=" * 60)
    print(f"\nNumber of tests: {len(example_p_values)}")
    print(f"Original p-values: {example_p_values}")

    # Generate full report
    report = generate_correction_report(
        p_values=example_p_values,
        test_names=test_names,
        alpha=0.05,
        output_path=Path("data/reports/correction_report.json")
    )

    print(f"\nCorrection applied: {report['summary']['correction_applied']}")
    print(f"Method: {report['summary']['correction_method']}")
    print(f"Reason: {report['summary']['reason']}")
    print(f"Adjusted alpha: {report['summary']['adjusted_alpha']:.6f}")
    print(f"\nSignificant tests before correction: {report['summary']['num_significant_before']}")
    print(f"Significant tests after correction: {report['summary']['num_significant_after']}")

    print("\nDetailed Results:")
    print("-" * 60)
    for result in report['test_results']:
        status = "SIGNIFICANT" if result['significant_after_correction'] else "not significant"
        print(f"{result['test_name']}:")
        print(f"  Raw p-value: {result['raw_p_value']:.4f}")
        print(f"  Corrected p-value: {result['corrected_p_value']:.4f}")
        print(f"  Status after correction: {status}")

    print("\n" + "=" * 60)
    print("Report saved to: data/reports/correction_report.json")
    print("=" * 60)

    return report


if __name__ == "__main__":
    main()
