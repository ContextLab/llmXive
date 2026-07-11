"""
analyze.py - Statistical Analysis Module

This module provides functions to perform statistical tests (t-test, ANOVA,
chi-squared, regression) on datasets, handling missing data, and calculating
metrics such as p-values, confidence intervals, and effect size biases.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestIndPower
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise


def handle_missing_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Perform listwise deletion of rows with missing values.

    Args:
        df (pd.DataFrame): Input dataframe.

    Returns:
        Tuple[pd.DataFrame, Dict[str, int]]: Cleaned dataframe and a dict
            containing 'N_original' and 'N_after_deletion'.
    """
    n_original = len(df)
    df_clean = df.dropna()
    n_after_deletion = len(df_clean)

    logger.info(f"Listwise deletion: Original N={n_original}, After deletion N={n_after_deletion}")

    if n_original > 0:
        power_loss = (n_original - n_after_deletion) / n_original
        logger.info(f"Power loss due to missing data: {power_loss:.4f}")
    else:
        power_loss = 0.0

    return df_clean, {
        'N_original': n_original,
        'N_after_deletion': n_after_deletion,
        'power_loss': power_loss
    }


def run_ttest(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    true_diff: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform a two-sample t-test.

    Args:
        data (pd.DataFrame): Input dataframe.
        group_col (str): Name of the column containing group labels.
        value_col (str): Name of the column containing values to test.
        true_diff (float, optional): True difference in means for bias calculation.

    Returns:
        Dict[str, Any]: Dictionary containing p-value, CI bounds, effect size (Cohen's d),
            and effect size bias if true_diff is provided.
    """
    if group_col not in data.columns or value_col not in data.columns:
        raise ValueError(f"Columns {group_col} or {value_col} not found in data.")

    groups = data[group_col].unique()
    if len(groups) != 2:
        raise ValueError(f"Expected 2 groups, found {len(groups)} in column '{group_col}'.")

    group1 = data[data[group_col] == groups[0]][value_col]
    group2 = data[data[group_col] == groups[1]][value_col]

    # Remove NaNs just in case
    group1 = group1.dropna()
    group2 = group2.dropna()

    if len(group1) < 2 or len(group2) < 2:
        logger.warning("Insufficient data for t-test in one or both groups.")
        return {
            'p_value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'cohens_d': np.nan,
            'bias': np.nan,
            'status': 'insufficient_data'
        }

    # Perform t-test
    t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)  # Welch's t-test

    # Calculate 95% CI for mean difference
    mean_diff = group1.mean() - group2.mean()
    se_diff = np.sqrt(group1.var() / len(group1) + group2.var() / len(group2))
    df = (group1.var() / len(group1) + group2.var() / len(group2))**2 / (
        (group1.var() / len(group1))**2 / (len(group1) - 1) +
        (group2.var() / len(group2))**2 / (len(group2) - 1)
    )
    t_crit = stats.t.ppf(0.975, df)
    ci_lower = mean_diff - t_crit * se_diff
    ci_upper = mean_diff + t_crit * se_diff

    # Calculate Cohen's d
    pooled_std = np.sqrt(((len(group1) - 1) * group1.var() + (len(group2) - 1) * group2.var()) / (len(group1) + len(group2) - 2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / pooled_std

    # Calculate bias if true_diff is provided
    bias = None
    if true_diff is not None:
        bias = cohens_d - true_diff

    return {
        'p_value': p_value,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'cohens_d': cohens_d,
        'bias': bias,
        'status': 'success'
    }


def run_anova(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    true_eta2: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform a one-way ANOVA.

    Args:
        data (pd.DataFrame): Input dataframe.
        group_col (str): Name of the column containing group labels.
        value_col (str): Name of the column containing values to test.
        true_eta2 (float, optional): True Eta-squared for bias calculation.

    Returns:
        Dict[str, Any]: Dictionary containing F-statistic, p-value, and effect size bias.
    """
    if group_col not in data.columns or value_col not in data.columns:
        raise ValueError(f"Columns {group_col} or {value_col} not found in data.")

    groups = data[group_col].unique()
    if len(groups) < 2:
        raise ValueError(f"Expected at least 2 groups, found {len(groups)}.")

    # Prepare groups for ANOVA
    group_data = [data[data[group_col] == g][value_col].dropna() for g in groups]

    if any(len(g) < 2 for g in group_data):
        logger.warning("Insufficient data in one or more groups for ANOVA.")
        return {
            'f_statistic': np.nan,
            'p_value': np.nan,
            'eta_squared': np.nan,
            'bias': np.nan,
            'status': 'insufficient_data'
        }

    f_stat, p_value = stats.f_oneway(*group_data)

    # Calculate Eta-squared
    ss_between = 0
    ss_total = 0
    grand_mean = data[value_col].mean()
    for g in group_data:
        ss_between += len(g) * (g.mean() - grand_mean)**2
        ss_total += sum((g - grand_mean)**2)

    if ss_total == 0:
        eta2 = 0.0
    else:
        eta2 = ss_between / ss_total

    bias = None
    if true_eta2 is not None:
        bias = eta2 - true_eta2

    return {
        'f_statistic': f_stat,
        'p_value': p_value,
        'eta_squared': eta2,
        'bias': bias,
        'status': 'success'
    }


def run_chi_squared(
    data: pd.DataFrame,
    col1: str,
    col2: str,
    true_cramers_v: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform a chi-squared test of independence.

    Args:
        data (pd.DataFrame): Input dataframe.
        col1 (str): Name of the first categorical column.
        col2 (str): Name of the second categorical column.
        true_cramers_v (float, optional): True Cramér's V for bias calculation.

    Returns:
        Dict[str, Any]: Dictionary containing statistic, p-value, and effect size bias.
    """
    if col1 not in data.columns or col2 not in data.columns:
        raise ValueError(f"Columns {col1} or {col2} not found in data.")

    # Create contingency table
    contingency_table = pd.crosstab(data[col1], data[col2])

    if contingency_table.size == 0:
        logger.warning("Contingency table is empty.")
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'cramers_v': np.nan,
            'bias': np.nan,
            'status': 'empty_table'
        }

    chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    # Calculate Cramér's V
    n = contingency_table.sum().sum()
    k = min(contingency_table.shape) - 1
    if k == 0 or n == 0:
        cramers_v = 0.0
    else:
        cramers_v = np.sqrt(chi2_stat / (n * k))

    bias = None
    if true_cramers_v is not None:
        bias = cramers_v - true_cramers_v

    return {
        'statistic': chi2_stat,
        'p_value': p_value,
        'cramers_v': cramers_v,
        'bias': bias,
        'status': 'success'
    }


def run_regression(
    data: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    true_coef: Optional[float] = None
) -> Dict[str, Any]:
    """
    Fit a linear regression model.

    Args:
        data (pd.DataFrame): Input dataframe.
        target_col (str): Name of the target variable column.
        feature_cols (List[str]): List of feature column names.
        true_coef (float, optional): True coefficient for bias calculation (assumes single feature for simplicity).

    Returns:
        Dict[str, Any]: Dictionary containing coefficients, CI, p-values, and bias.
    """
    if target_col not in data.columns:
        raise ValueError(f"Target column {target_col} not found in data.")
    if not all(col in data.columns for col in feature_cols):
        raise ValueError(f"One or more feature columns not found in data.")

    # Prepare data
    y = data[target_col].dropna()
    X = data[feature_cols].loc[y.index]
    X = add_constant(X)

    if len(y) < 2:
        logger.warning("Insufficient data for regression.")
        return {
            'coef': np.nan,
            'p_value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'bias': np.nan,
            'status': 'insufficient_data'
        }

    model = OLS(y, X).fit()

    # Extract results (assuming single feature for bias calculation if true_coef provided)
    if len(feature_cols) == 1 and true_coef is not None:
        coef_idx = 1  # Skip intercept
        coef = model.params[coef_idx]
        bias = coef - true_coef
        p_val = model.pvalues[coef_idx]
        conf_int = model.conf_int().loc[coef_idx]
    else:
        # For multiple features or no true_coef, return first feature's stats or aggregate
        if len(feature_cols) >= 1:
            coef_idx = 1
            coef = model.params[coef_idx]
            p_val = model.pvalues[coef_idx]
            conf_int = model.conf_int().loc[coef_idx]
            bias = None
        else:
            return {
                'coef': np.nan,
                'p_value': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'bias': np.nan,
                'status': 'no_features'
            }

    return {
        'coef': coef,
        'p_value': p_val,
        'ci_lower': conf_int[0],
        'ci_upper': conf_int[1],
        'bias': bias,
        'status': 'success'
    }


def calculate_ci_coverage(
    results: List[Dict[str, Any]],
    true_value: float,
    ci_key: str = 'ci'
) -> float:
    """
    Calculate the proportion of confidence intervals that contain the true value.

    Args:
        results (List[Dict[str, Any]]): List of result dictionaries containing CI bounds.
        true_value (float): The true population parameter.
        ci_key (str): Key to access CI bounds (assumes 'ci_lower' and 'ci_upper' exist).

    Returns:
        float: Coverage rate.
    """
    if not results:
        return 0.0

    covered = 0
    for r in results:
        if 'ci_lower' in r and 'ci_upper' in r:
            if r['ci_lower'] <= true_value <= r['ci_upper']:
                covered += 1

    return covered / len(results)


def main():
    """Main entry point for the analysis module."""
    parser = argparse.ArgumentParser(description="Run statistical analyses on datasets.")
    parser.add_argument('--config', type=str, required=True, help='Path to configuration file.')
    parser.add_argument('--input', type=str, required=True, help='Path to input dataset.')
    parser.add_argument('--output', type=str, required=True, help='Path to output results JSON.')
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        df = pd.read_csv(args.input)

        # Handle missing data
        df_clean, stats_info = handle_missing_data(df)

        # Example: Run t-test (configuration would dictate actual test)
        # This is a placeholder; real implementation would read test specs from config
        if 'test_type' in config and config['test_type'] == 'ttest':
            result = run_ttest(
                df_clean,
                config['group_col'],
                config['value_col'],
                true_diff=config.get('true_diff')
            )
        elif 'test_type' in config and config['test_type'] == 'anova':
            result = run_anova(
                df_clean,
                config['group_col'],
                config['value_col'],
                true_eta2=config.get('true_eta2')
            )
        elif 'test_type' in config and config['test_type'] == 'chi2':
            result = run_chi_squared(
                df_clean,
                config['col1'],
                config['col2'],
                true_cramers_v=config.get('true_cramers_v')
            )
        elif 'test_type' in config and config['test_type'] == 'regression':
            result = run_regression(
                df_clean,
                config['target_col'],
                config['feature_cols'],
                true_coef=config.get('true_coef')
            )
        else:
            logger.warning("No valid test type specified in config. Skipping analysis.")
            result = {'status': 'skipped'}

        # Combine missing data stats and test result
        final_output = {
            'missing_data_stats': stats_info,
            'test_result': result
        }

        # Write output
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(final_output, f, indent=2)

        logger.info(f"Analysis complete. Results saved to {args.output}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == '__main__':
    main()