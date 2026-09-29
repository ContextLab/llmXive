import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from scipy import stats as scipy_stats
import pandas as pd
import logging
import os

from utils.config import get_project_root, get_data_processed_path

logger = logging.getLogger(__name__)


def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool], float]:
    """
    Apply Bonferroni correction for multiple comparisons.

    This function adjusts p-values to control the family-wise error rate (FWER)
    when performing multiple statistical tests. The corrected p-values are
    calculated by multiplying each raw p-value by the number of tests (m),
    capped at 1.0.

    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level for the test (default: 0.05).

    Returns:
        Tuple containing:
        - corrected_p_values: List of Bonferroni-corrected p-values.
        - significant_flags: List of booleans indicating if the corrected p-value < alpha.
        - adjusted_alpha: The Bonferroni-adjusted significance threshold (alpha / m).

    Raises:
        ValueError: If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")

    if any(not isinstance(p, (int, float)) or p < 0 or p > 1 for p in p_values):
        raise ValueError("All p-values must be floats between 0 and 1")

    m = len(p_values)
    adjusted_alpha = alpha / m

    corrected_p_values = []
    significant_flags = []

    for p in p_values:
        # Bonferroni correction: p_corrected = p * m
        corrected_p = min(p * m, 1.0)
        corrected_p_values.append(corrected_p)
        significant_flags.append(corrected_p < alpha)

    logger.info(f"Bonferroni correction applied: {m} tests, adjusted alpha = {adjusted_alpha:.6f}")
    logger.info(f"Significant results: {sum(significant_flags)}/{m}")

    return corrected_p_values, significant_flags, adjusted_alpha


def kruskal_wallis_test(group_values: List[List[float]]) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H test for independent samples.

    Non-parametric test to determine if there are statistically significant
    differences between two or more groups of an independent variable on a
    continuous or ordinal dependent variable.

    Args:
        group_values: List of lists, where each inner list contains values for a group.

    Returns:
        Tuple of (H-statistic, p-value).
    """
    if len(group_values) < 2:
        raise ValueError("At least two groups are required for Kruskal-Wallis test")

    h_stat, p_val = scipy_stats.kruskal(*group_values)
    logger.debug(f"Kruskal-Wallis test: H={h_stat:.4f}, p={p_val:.6f}")
    return h_stat, p_val


def mann_whitney_u_test(group1: List[float], group2: List[float], alternative: str = 'two-sided') -> Tuple[float, float]:
    """
    Perform Mann-Whitney U test for two independent samples.

    Non-parametric test to determine if two independent samples come from
    the same distribution.

    Args:
        group1: Values for the first group.
        group2: Values for the second group.
        alternative: Type of alternative hypothesis ('two-sided', 'less', 'greater').

    Returns:
        Tuple of (U-statistic, p-value).
    """
    u_stat, p_val = scipy_stats.mannwhitneyu(group1, group2, alternative=alternative)
    logger.debug(f"Mann-Whitney U test: U={u_stat:.4f}, p={p_val:.6f}")
    return u_stat, p_val


def ks_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test for two independent samples.

    Non-parametric test to compare the distributions of two independent samples.

    Args:
        group1: Values for the first group.
        group2: Values for the second group.

    Returns:
        Tuple of (D-statistic, p-value).
    """
    d_stat, p_val = scipy_stats.ks_2samp(group1, group2)
    logger.debug(f"KS test: D={d_stat:.4f}, p={p_val:.6f}")
    return d_stat, p_val


def nearest_neighbor_matching(data: pd.DataFrame, treatment_col: str, mass_col: str,
                              tolerance: float = 0.1) -> pd.DataFrame:
    """
    Perform nearest-neighbor matching with caliper on mass.

    Matches treated and control units based on mass similarity to control
    for confounding variables.

    Args:
        data: DataFrame containing the data.
        treatment_col: Name of the column indicating treatment status (1/0).
        mass_col: Name of the column containing mass values.
        tolerance: Maximum allowed difference in mass for a match (as fraction of mass).

    Returns:
        DataFrame with matched pairs, including a 'matched' flag.
    """
    if treatment_col not in data.columns or mass_col not in data.columns:
        raise ValueError(f"Columns {treatment_col} and {mass_col} must exist in data")

    treated = data[data[treatment_col] == 1].copy()
    control = data[data[treatment_col] == 0].copy()

    matched_indices = []

    for idx, row in treated.iterrows():
        mass = row[mass_col]
        caliper = mass * tolerance

        # Find nearest neighbor in control group within caliper
        diffs = (control[mass_col] - mass).abs()
        within_caliper = diffs <= caliper

        if within_caliper.any():
            nearest_idx = diffs[within_caliper].idxmin()
            matched_indices.append((idx, nearest_idx))

    # Create result dataframe
    result = data.copy()
    result['matched'] = False
    result['match_pair_id'] = -1

    pair_id = 0
    for treated_idx, control_idx in matched_indices:
        result.loc[treated_idx, 'matched'] = True
        result.loc[control_idx, 'matched'] = True
        result.loc[treated_idx, 'match_pair_id'] = pair_id
        result.loc[control_idx, 'match_pair_id'] = pair_id
        pair_id += 1

    logger.info(f"Nearest neighbor matching: {len(matched_indices)} pairs matched out of {len(treated)} treated units")
    return result


def linear_regression_with_mass_control(data: pd.DataFrame, dependent_var: str,
                                        independent_vars: List[str],
                                        mass_col: str) -> Dict[str, Any]:
    """
    Perform linear regression with mass as a control variable.

    Args:
        data: DataFrame containing the data.
        dependent_var: Name of the dependent variable.
        independent_vars: List of independent variables (shape parameters).
        mass_col: Name of the mass column to use as control.

    Returns:
        Dictionary containing regression results (coefficients, p-values, r_squared).
    """
    try:
        import statsmodels.api as sm
    except ImportError:
        raise ImportError("statsmodels is required for linear regression. Install with: pip install statsmodels")

    # Prepare features
    features = independent_vars + [mass_col]
    X = data[features].dropna()
    y = data.loc[X.index, dependent_var]

    if len(X) == 0:
        raise ValueError("No valid data points after dropping NaNs")

    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    results = {
        'coefficients': {},
        'p_values': {},
        'r_squared': model.rsquared,
        'adjusted_r_squared': model.rsquared_adj,
        'n_observations': model.nobs
    }

    for var in features:
        if var in model.params.index:
            results['coefficients'][var] = float(model.params[var])
            results['p_values'][var] = float(model.pvalues[var])

    logger.info(f"Linear regression completed: R²={results['r_squared']:.4f}, n={results['n_observations']}")
    return results


def run_statistical_tests(halo_data: pd.DataFrame, galaxy_data: pd.DataFrame,
                          shape_metric: str = 'triaxiality',
                          galaxy_property: str = 'sfr') -> Dict[str, Any]:
    """
    Run a suite of statistical tests on halo shape and galaxy property data.

    Args:
        halo_data: DataFrame with halo shape metrics.
        galaxy_data: DataFrame with galaxy properties.
        shape_metric: Name of the shape metric to use (e.g., 'triaxiality', 'b_a_ratio').
        galaxy_property: Name of the galaxy property to test (e.g., 'sfr', 'effective_radius').

    Returns:
        Dictionary containing test results.
    """
    # Merge datasets
    merged = pd.merge(halo_data, galaxy_data, on='halo_id', how='inner')
    merged = merged.dropna()

    if len(merged) < 10:
        raise ValueError("Insufficient data points after merging and dropping NaNs")

    results = {
        'shape_metric': shape_metric,
        'galaxy_property': galaxy_property,
        'n_observations': len(merged),
        'tests': {}
    }

    # Binning for Kruskal-Wallis
    merged['shape_bin'] = pd.cut(merged[shape_metric], bins=3, labels=['low', 'medium', 'high'])
    groups = [group[galaxy_property].values for name, group in merged.groupby('shape_bin')]

    # Kruskal-Wallis test
    try:
        h_stat, p_val = kruskal_wallis_test(groups)
        results['tests']['kruskal_wallis'] = {
            'statistic': float(h_stat),
            'p_value': float(p_val),
            'significant': p_val < 0.05
        }
    except Exception as e:
        logger.warning(f"Kruskal-Wallis test failed: {e}")
        results['tests']['kruskal_wallis'] = {'error': str(e)}

    # Mann-Whitney U test (comparing low vs high)
    try:
        low_group = merged[merged['shape_bin'] == 'low'][galaxy_property].values
        high_group = merged[merged['shape_bin'] == 'high'][galaxy_property].values
        u_stat, p_val = mann_whitney_u_test(list(low_group), list(high_group))
        results['tests']['mann_whitney_u'] = {
            'statistic': float(u_stat),
            'p_value': float(p_val),
            'significant': p_val < 0.05
        }
    except Exception as e:
        logger.warning(f"Mann-Whitney U test failed: {e}")
        results['tests']['mann_whitney_u'] = {'error': str(e)}

    # KS test
    try:
        d_stat, p_val = ks_test(list(low_group), list(high_group))
        results['tests']['ks_test'] = {
            'statistic': float(d_stat),
            'p_value': float(p_val),
            'significant': p_val < 0.05
        }
    except Exception as e:
        logger.warning(f"KS test failed: {e}")
        results['tests']['ks_test'] = {'error': str(e)}

    # Linear regression with mass control
    try:
        regression_results = linear_regression_with_mass_control(
            merged, galaxy_property, [shape_metric], 'mass'
        )
        results['tests']['linear_regression'] = regression_results
    except Exception as e:
        logger.warning(f"Linear regression failed: {e}")
        results['tests']['linear_regression'] = {'error': str(e)}

    return results


def save_statistical_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical results to a CSV file.

    Args:
        results: Dictionary containing test results.
        output_path: Path to the output CSV file.
    """
    # Flatten results for CSV
    rows = []
    for test_name, test_data in results.get('tests', {}).items():
        if 'error' in test_data:
            rows.append({
                'test': test_name,
                'metric': results['shape_metric'],
                'property': results['galaxy_property'],
                'statistic': None,
                'p_value': None,
                'error': test_data['error'],
                'significant': None
            })
        else:
            rows.append({
                'test': test_name,
                'metric': results['shape_metric'],
                'property': results['galaxy_property'],
                'statistic': test_data.get('statistic'),
                'p_value': test_data.get('p_value'),
                'error': None,
                'significant': test_data.get('significant')
            })

    # Add regression results
    if 'linear_regression' in results.get('tests', {}):
        reg_data = results['tests']['linear_regression']
        if 'error' not in reg_data:
            for var, coef in reg_data.get('coefficients', {}).items():
                rows.append({
                    'test': 'linear_regression',
                    'metric': results['shape_metric'],
                    'property': results['galaxy_property'],
                    'variable': var,
                    'coefficient': coef,
                    'p_value': reg_data.get('p_values', {}).get(var),
                    'r_squared': reg_data.get('r_squared'),
                    'error': None,
                    'significant': reg_data.get('p_values', {}).get(var, 1.0) < 0.05
                })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Statistical results saved to {output_path}")


def main():
    """
    Main entry point for running statistical analysis on sample data.
    This is primarily for testing the stats module functionality.
    """
    # Load sample data (in production, these would come from processed files)
    project_root = get_project_root()
    processed_path = get_data_processed_path()

    halo_shapes_path = processed_path / 'halo_shapes.csv'
    galaxy_props_path = processed_path / 'galaxy_properties.csv'

    if not halo_shapes_path.exists() or not galaxy_props_path.exists():
        logger.error("Required data files not found. Run ingestion and processing first.")
        return

    halo_data = pd.read_csv(halo_shapes_path)
    galaxy_data = pd.read_csv(galaxy_props_path)

    # Run tests for multiple combinations
    combinations = [
        ('triaxiality', 'sfr'),
        ('triaxiality', 'effective_radius'),
        ('b_a_ratio', 'sfr'),
        ('b_a_ratio', 'effective_radius')
    ]

    all_results = []
    for shape_metric, galaxy_property in combinations:
        logger.info(f"Running tests for {shape_metric} vs {galaxy_property}")
        results = run_statistical_tests(halo_data, galaxy_data, shape_metric, galaxy_property)
        all_results.append(results)

    # Save individual results
    output_dir = processed_path
    for i, results in enumerate(all_results):
        output_file = output_dir / f'statistical_results_{i+1}.csv'
        save_statistical_results(results, str(output_file))

    logger.info("Statistical analysis complete.")


if __name__ == '__main__':
    main()