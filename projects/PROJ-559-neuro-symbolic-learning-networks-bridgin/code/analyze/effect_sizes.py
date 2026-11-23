"""
Effect Sizes Analysis for Neuro-Symbolic Learning Networks.

Implements Cohen's d calculation with 95% Confidence Intervals for pairwise
comparisons between experimental conditions (neural, symbolic, neuro-symbolic).
Validates CI width constraints per SC-003.
"""
import os
import sys
import json
import logging
import math
import argparse
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CI_WIDTH_THRESHOLD = 0.20
ALPHA = 0.05

def load_effect_size_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation logs or merged data for effect size calculation.

    Args:
        input_path: Path to the CSV containing simulation logs (e.g., data/derived/simulation_logs.csv)

    Returns:
        DataFrame with columns: condition, correctness, rt_seconds, comprehension_rating
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    required_cols = ['condition', 'correct']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    # Ensure condition is a string and correct is numeric
    df['condition'] = df['condition'].astype(str)
    df['correct'] = pd.to_numeric(df['correct'], errors='coerce')

    # Drop rows with missing correctness
    df = df.dropna(subset=['correct'])

    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> Dict[str, float]:
    """
    Calculate Cohen's d and 95% Confidence Interval for two groups.

    Formula: d = (mean1 - mean2) / pooled_std
    Pooled std: sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))

    CI calculation uses the non-central t-distribution approximation.
    For simplicity and robustness in CPU-only environments, we use the
    standard error of d approximation: SE_d = sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))

    Args:
        group1: Series of values for group 1
        group2: Series of values for group 2

    Returns:
        Dict with 'cohens_d', 'ci_lower', 'ci_upper', 'ci_width', 'n1', 'n2'
    """
    n1 = len(group1)
    n2 = len(group2)

    if n1 < 2 or n2 < 2:
        raise ValueError("Each group must have at least 2 samples for variance calculation")

    mean1 = group1.mean()
    mean2 = group2.mean()
    std1 = group1.std(ddof=1)
    std2 = group2.std(ddof=1)

    # Pooled standard deviation
    pooled_var = ((n1 - 1) * (std1 ** 2) + (n2 - 1) * (std2 ** 2)) / (n1 + n2 - 2)
    pooled_std = math.sqrt(pooled_var)

    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Cohen's d is undefined.")
        return {
            'cohens_d': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'ci_width': 0.0,
            'n1': n1,
            'n2': n2,
            'pooled_std': 0.0
        }

    d = (mean1 - mean2) / pooled_std

    # Standard error of d (approximation)
    # SE_d = sqrt( (n1+n2)/(n1*n2) + d^2 / (2*(n1+n2)) )
    se_d = math.sqrt((n1 + n2) / (n1 * n2) + (d ** 2) / (2 * (n1 + n2)))

    # 95% CI: d +/- 1.96 * SE_d (using Z approximation for large N)
    # For small N, t-distribution would be more accurate, but Z is acceptable for N>30
    z_score = 1.96
    ci_lower = d - (z_score * se_d)
    ci_upper = d + (z_score * se_d)
    ci_width = ci_upper - ci_lower

    return {
        'cohens_d': d,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'ci_width': ci_width,
        'n1': n1,
        'n2': n2,
        'pooled_std': pooled_std,
        'mean1': mean1,
        'mean2': mean2
    }

def run_pairwise_effect_sizes(df: pd.DataFrame, metric: str = 'correct') -> List[Dict[str, Any]]:
    """
    Compute Cohen's d for all pairwise comparisons between conditions.

    Args:
        df: DataFrame with 'condition' and metric columns
        metric: Name of the metric column to analyze (default: 'correct')

    Returns:
        List of dicts containing comparison details and statistics
    """
    if metric not in df.columns:
        raise ValueError(f"Metric column '{metric}' not found in dataframe")

    conditions = df['condition'].unique()
    comparisons = []

    if len(conditions) < 2:
        logger.warning("Less than 2 conditions found. Cannot perform pairwise comparisons.")
        return comparisons

    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            cond1 = conditions[i]
            cond2 = conditions[j]

            group1 = df[df['condition'] == cond1][metric]
            group2 = df[df['condition'] == cond2][metric]

            try:
                result = calculate_cohens_d(group1, group2)
                result['condition_1'] = cond1
                result['condition_2'] = cond2
                result['metric'] = metric
                comparisons.append(result)
                logger.info(f"Comparison {cond1} vs {cond2}: d={result['cohens_d']:.4f}, "
                            f"CI=[{result['ci_lower']:.4f}, {result['ci_upper']:.4f}], "
                            f"width={result['ci_width']:.4f}")
            except ValueError as e:
                logger.error(f"Error computing effect size for {cond1} vs {cond2}: {e}")

    return comparisons

def validate_ci_width(comparisons: List[Dict[str, Any]], threshold: float = CI_WIDTH_THRESHOLD) -> Dict[str, Any]:
    """
    Validate that all 95% CI widths are within the specified threshold.

    Args:
        comparisons: List of effect size comparison dicts
        threshold: Maximum allowed CI width (default: 0.20)

    Returns:
        Dict with 'passed' (bool), 'violations' (list), and 'summary'
    """
    violations = []
    for comp in comparisons:
        if comp['ci_width'] > threshold:
            violations.append({
                'comparison': f"{comp['condition_1']} vs {comp['condition_2']}",
                'ci_width': comp['ci_width'],
                'threshold': threshold
            })

    passed = len(violations) == 0
    return {
        'passed': passed,
        'violations': violations,
        'total_comparisons': len(comparisons),
        'threshold': threshold
    }

def generate_effect_size_report(comparisons: List[Dict[str, Any]], 
                                validation: Dict[str, Any],
                                output_path: str) -> None:
    """
    Generate a JSON report of effect sizes and validation results.

    Args:
        comparisons: List of effect size comparison dicts
        validation: Validation result dict
        output_path: Path to write the JSON report
    """
    report = {
        'effect_sizes': comparisons,
        'validation': validation,
        'metadata': {
            'threshold': CI_WIDTH_THRESHOLD,
            'alpha': ALPHA,
            'generated_at': pd.Timestamp.now().isoformat()
        }
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Effect size report written to {output_path}")

def main():
    """Main entry point for effect size analysis."""
    parser = argparse.ArgumentParser(description="Compute Cohen's d effect sizes for pairwise comparisons.")
    parser.add_argument('--input', '-i', type=str, default='data/derived/simulation_logs.csv',
                        help='Path to input simulation logs CSV')
    parser.add_argument('--output', '-o', type=str, default='data/derived/effect_sizes_report.json',
                        help='Path to output JSON report')
    parser.add_argument('--metric', '-m', type=str, default='correct',
                        help='Metric to analyze (default: correct)')
    parser.add_argument('--threshold', '-t', type=float, default=CI_WIDTH_THRESHOLD,
                        help=f'CI width threshold (default: {CI_WIDTH_THRESHOLD})')

    args = parser.parse_args()

    try:
        # Load data
        logger.info(f"Loading data from {args.input}")
        df = load_effect_size_data(args.input)

        # Compute pairwise effect sizes
        logger.info("Computing pairwise effect sizes...")
        comparisons = run_pairwise_effect_sizes(df, metric=args.metric)

        if not comparisons:
            logger.warning("No comparisons could be computed. Exiting.")
            sys.exit(0)

        # Validate CI widths
        logger.info("Validating CI widths...")
        validation = validate_ci_width(comparisons, threshold=args.threshold)

        # Generate report
        logger.info(f"Generating report at {args.output}")
        generate_effect_size_report(comparisons, validation, args.output)

        # Print summary
        print(f"\n--- Effect Size Analysis Summary ---")
        print(f"Total comparisons: {len(comparisons)}")
        print(f"CI width threshold: {args.threshold}")
        print(f"Validation passed: {validation['passed']}")
        if not validation['passed']:
            print(f"Violations: {len(validation['violations'])}")
            for v in validation['violations']:
                print(f"  - {v['comparison']}: width={v['ci_width']:.4f} > {v['threshold']}")

        # Exit with error if validation failed
        if not validation['passed']:
            logger.error("CI width validation failed. Some intervals are too wide.")
            sys.exit(1)

        logger.info("Effect size analysis completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
