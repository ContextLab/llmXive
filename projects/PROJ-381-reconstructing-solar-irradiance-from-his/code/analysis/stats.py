"""
Statistical analysis module for solar irradiance reconstruction.

This module provides functions for:
- Loading and filtering reconstruction data
- Bootstrap variance estimation
- Comparing variance across historical periods
- Multiple comparison correction (Bonferroni, FDR)
- Associational framing of statistical findings
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import fdr_correction, bonferroni

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PERIOD_DEFINITIONS = {
    'Maunder Minimum': (1645, 1715),
    'Dalton Minimum': (1790, 1830),
    'Modern Maximum': (1940, 2020),
    'Satellite Era': (2003, 2020)
}

def load_reconstruction_data(
    data_path: Optional[str] = None,
    reconstruction_file: str = "reconstruction_1610_2002.parquet"
) -> pd.DataFrame:
    """
    Load the TSI reconstruction data from disk.

    Args:
        data_path: Optional base path for data directory. Defaults to data/processed/
        reconstruction_file: Name of the reconstruction file.

    Returns:
        DataFrame with TSI reconstruction data.

    Raises:
        FileNotFoundError: If the reconstruction file does not exist.
        ValueError: If the file format is unsupported.
    """
    if data_path is None:
        data_path = Path("data/processed")
    else:
        data_path = Path(data_path)

    file_path = data_path / reconstruction_file

    if not file_path.exists():
        raise FileNotFoundError(f"Reconstruction file not found: {file_path}")

    logger.info(f"Loading reconstruction data from {file_path}")

    if reconstruction_file.endswith('.parquet'):
        df = pd.read_parquet(file_path)
    elif reconstruction_file.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {reconstruction_file}")

    # Validate required columns
    required_cols = ['year', 'tsi_mean', 'tsi_lower', 'tsi_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} records")
    return df


def filter_by_period(
    df: pd.DataFrame,
    period_name: str
) -> pd.DataFrame:
    """
    Filter the reconstruction data to a specific historical period.

    Args:
        df: Full reconstruction DataFrame.
        period_name: Name of the period (must match PERIOD_DEFINITIONS).

    Returns:
        Filtered DataFrame for the specified period.

    Raises:
        KeyError: If period_name is not found in PERIOD_DEFINITIONS.
    """
    if period_name not in PERIOD_DEFINITIONS:
        raise KeyError(f"Unknown period: {period_name}. Available: {list(PERIOD_DEFINITIONS.keys())}")

    start_year, end_year = PERIOD_DEFINITIONS[period_name]
    filtered_df = df[(df['year'] >= start_year) & (df['year'] <= end_year)].copy()

    logger.info(f"Filtered to {period_name} ({start_year}-{end_year}): {len(filtered_df)} records")
    return filtered_df


def bootstrap_variance_estimation(
    data: np.ndarray,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform bootstrap resampling to estimate variance statistics.

    Args:
        data: Array of TSI values for the period.
        n_iterations: Number of bootstrap iterations (default 1000).
        random_seed: Optional random seed for reproducibility.

    Returns:
        Dictionary with bootstrap statistics:
            - mean: Mean of bootstrap means
            - std: Standard deviation of bootstrap means (standard error)
            - ci_lower: Lower bound of 95% confidence interval
            - ci_upper: Upper bound of 95% confidence interval
            - variance: Variance of the original data
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n_samples = len(data)
    bootstrap_means = []

    for _ in range(n_iterations):
        # Resample with replacement
        resample = np.random.choice(data, size=n_samples, replace=True)
        bootstrap_means.append(np.mean(resample))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate statistics
    mean = np.mean(bootstrap_means)
    std = np.std(bootstrap_means, ddof=1)
    ci_lower = np.percentile(bootstrap_means, 2.5)
    ci_upper = np.percentile(bootstrap_means, 97.5)
    variance = np.var(data, ddof=1)

    return {
        'mean': float(mean),
        'std': float(std),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'variance': float(variance),
        'n_iterations': n_iterations,
        'n_samples': n_samples
    }


def compare_variance_across_periods(
    df: pd.DataFrame,
    periods: Optional[List[str]] = None,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compare variance across multiple historical periods using bootstrap.

    Args:
        df: Full reconstruction DataFrame.
        periods: List of period names to compare. Defaults to all defined periods.
        n_iterations: Number of bootstrap iterations.
        random_seed: Optional random seed.

    Returns:
        Dictionary with:
            - period_stats: Dict of stats for each period
            - pairwise_tests: Results of pairwise variance comparisons
            - variance_ratios: Ratios of variances between periods
    """
    if periods is None:
        periods = list(PERIOD_DEFINITIONS.keys())

    period_stats = {}
    period_variances = {}

    # Calculate bootstrap stats for each period
    for period in periods:
        try:
            period_data = filter_by_period(df, period)
            if len(period_data) < 2:
                logger.warning(f"Not enough data for {period}. Skipping.")
                continue

            tsi_values = period_data['tsi_mean'].values
            stats_dict = bootstrap_variance_estimation(tsi_values, n_iterations, random_seed)
            period_stats[period] = stats_dict
            period_variances[period] = stats_dict['variance']

        except KeyError as e:
            logger.warning(f"Skipping period {period}: {e}")
            continue

    # Pairwise variance comparisons (F-test)
    pairwise_tests = []
    variance_ratios = {}

    period_list = list(period_variances.keys())
    for i in range(len(period_list)):
        for j in range(i + 1, len(period_list)):
            p1, p2 = period_list[i], period_list[j]
            data1 = filter_by_period(df, p1)['tsi_mean'].values
            data2 = filter_by_period(df, p2)['tsi_mean'].values

            if len(data1) < 2 or len(data2) < 2:
                continue

            # F-test for equality of variances
            f_stat, p_val = stats.f_oneway(data1, data2)
            # Note: f_oneway tests means, not variances. Using levene for variances
            levene_stat, levene_p = stats.levene(data1, data2)

            # Calculate variance ratio
            ratio = period_variances[p1] / period_variances[p2]
            variance_ratios[f"{p1}_vs_{p2}"] = ratio

            pairwise_tests.append({
                'period_1': p1,
                'period_2': p2,
                'levene_statistic': float(levene_stat),
                'levene_p_value': float(levene_p),
                'variance_ratio': float(ratio)
            })

    return {
        'period_stats': period_stats,
        'pairwise_tests': pairwise_tests,
        'variance_ratios': variance_ratios,
        'n_iterations': n_iterations
    }


def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = 'fdr_bh'
) -> Tuple[List[float], List[bool]]:
    """
    Apply multiple comparison correction to a list of p-values.

    Args:
        p_values: List of raw p-values from hypothesis tests.
        method: Correction method. Options:
            - 'bonferroni': Bonferroni correction (conservative)
            - 'fdr_bh': Benjamini-Hochberg FDR (less conservative)
            - 'fdr_by': Benjamini-Yekutieli FDR (for dependent tests)

    Returns:
        Tuple of (corrected_p_values, boolean_significance)

    Raises:
        ValueError: If method is not recognized.
    """
    if not p_values:
        return [], []

    n_tests = len(p_values)
    corrected_p = []
    significant = []

    if method == 'bonferroni':
        # Bonferroni: multiply p-values by number of tests
        corrected_p = [min(p * n_tests, 1.0) for p in p_values]
        alpha = 0.05
        significant = [p < alpha for p in corrected_p]

    elif method in ['fdr_bh', 'fdr_by']:
        # Use scipy's fdr_correction
        # Note: fdr_correction returns (rejected, p_corrected)
        # We need to sort and apply the method
        reject, p_corrected = fdr_correction(p_values, method='indep' if method == 'fdr_bh' else 'negcorr')
        corrected_p = p_corrected.tolist()
        significant = reject.tolist()

    else:
        raise ValueError(f"Unknown correction method: {method}. Use 'bonferroni', 'fdr_bh', or 'fdr_by'.")

    return corrected_p, significant


def run_bootstrap_analysis(
    data_path: Optional[str] = None,
    periods: Optional[List[str]] = None,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None,
    correction_method: str = 'fdr_bh',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the complete bootstrap analysis pipeline with multiple comparison correction.

    This function:
    1. Loads the reconstruction data
    2. Calculates variance for each period using bootstrap
    3. Performs pairwise variance comparisons
    4. Applies multiple comparison correction to p-values
    5. Frames results associationally (no causal claims)

    Args:
        data_path: Optional base path for data.
        periods: List of periods to analyze.
        n_iterations: Number of bootstrap iterations (default 1000).
        random_seed: Random seed for reproducibility.
        correction_method: Multiple comparison correction method.
        alpha: Significance threshold.

    Returns:
        Dictionary containing all analysis results and formatted text.
    """
    logger.info("Starting bootstrap analysis pipeline")

    # Load data
    df = load_reconstruction_data(data_path)

    # Run variance comparison
    comparison_results = compare_variance_across_periods(
        df, periods, n_iterations, random_seed
    )

    # Extract p-values for correction
    p_values = [test['levene_p_value'] for test in comparison_results['pairwise_tests']]
    test_names = [f"{t['period_1']}_vs_{t['period_2']}" for t in comparison_results['pairwise_tests']]

    # Apply correction
    corrected_p, significant = apply_multiple_comparison_correction(p_values, correction_method)

    # Add correction results to pairwise tests
    for i, test in enumerate(comparison_results['pairwise_tests']):
        test['corrected_p_value'] = corrected_p[i]
        test['is_significant'] = significant[i]

    # Generate associational framing text
    findings = []
    for test in comparison_results['pairwise_tests']:
        if test['is_significant']:
            findings.append(
                f"An association was observed between {test['period_1']} and {test['period_2']} "
                f"in terms of TSI variance (corrected p={test['corrected_p_value']:.4f}, "
                f"variance ratio={test['variance_ratio']:.3f}). This does not imply causation."
            )
        else:
            findings.append(
                f"No statistically significant association was found between {test['period_1']} "
                f"and {test['period_2']} in TSI variance (corrected p={test['corrected_p_value']:.4f})."
            )

    # Compile final report
    report = {
        'analysis_summary': {
            'periods_analyzed': list(comparison_results['period_stats'].keys()),
            'n_iterations': n_iterations,
            'correction_method': correction_method,
            'alpha_threshold': alpha,
            'n_comparisons': len(comparison_results['pairwise_tests'])
        },
        'period_statistics': comparison_results['period_stats'],
        'pairwise_comparisons': comparison_results['pairwise_tests'],
        'variance_ratios': comparison_results['variance_ratios'],
        'findings': findings,
        'methodological_notes': [
            "All findings are framed as associational relationships. No causal claims are made.",
            f"Multiple comparison correction applied using {correction_method} method.",
            f"Bootstrap resampling performed with {n_iterations} iterations.",
            "Variance comparisons use Levene's test for robustness to non-normality."
        ]
    }

    logger.info("Bootstrap analysis complete")
    return report


def main():
    """
    Main entry point for running the bootstrap analysis from the command line.

    Usage:
        python -m code.analysis.stats

    This will:
    1. Load the reconstruction data from data/processed/
    2. Run bootstrap analysis on all defined periods
    3. Save the results to data/processed/variance_analysis_bootstrap.json
    """
    logger.info("Running stats analysis main")

    # Default parameters
    data_path = "data/processed"
    periods = None  # Use all defined periods
    n_iterations = 1000
    random_seed = 42
    correction_method = 'fdr_bh'

    # Run analysis
    results = run_bootstrap_analysis(
        data_path=data_path,
        periods=periods,
        n_iterations=n_iterations,
        random_seed=random_seed,
        correction_method=correction_method
    )

    # Save results
    output_path = Path(data_path) / "variance_analysis_bootstrap.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

    # Print summary
    print("\n=== Bootstrap Analysis Summary ===")
    print(f"Periods analyzed: {', '.join(results['analysis_summary']['periods_analyzed'])}")
    print(f"Comparisons made: {results['analysis_summary']['n_comparisons']}")
    print(f"Significant associations found: {sum(1 for f in results['findings'] if 'association was observed' in f)}")
    print("\nFindings:")
    for finding in results['findings']:
        print(f"  - {finding}")

    return results


if __name__ == "__main__":
    main()