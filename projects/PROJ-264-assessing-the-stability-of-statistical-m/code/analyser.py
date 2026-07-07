import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from utils import safe_execute

logger = logging.getLogger(__name__)


def load_raw_evaluations(path: Path) -> pd.DataFrame:
    """Load raw evaluation results from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Raw evaluations file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['dataset_id', 'model_name', 'fold_id', 'repeat_id', 'accuracy', 'f1_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    return df


def load_dataset_properties(path: Path) -> pd.DataFrame:
    """Load dataset properties (n_samples, n_features, etc.) from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset properties file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['dataset_id', 'n_samples', 'n_features']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    return df


def calculate_cv(std_val: float, mean_val: float) -> float:
    """Calculate Coefficient of Variation (CV = std / mean)."""
    if mean_val == 0:
        return float('inf') if std_val > 0 else 0.0
    return std_val / abs(mean_val)


def aggregate_metrics(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate raw evaluations to compute mean_accuracy, cv_accuracy, mean_f1, cv_f1
    per (dataset_id, model_name).
    """
    if raw_df.empty:
        logger.warning("Empty raw evaluations dataframe provided to aggregate_metrics")
        return pd.DataFrame(columns=['dataset_id', 'model_name', 'mean_accuracy', 'cv_accuracy', 'mean_f1', 'cv_f1'])

    agg_df = raw_df.groupby(['dataset_id', 'model_name']).agg(
        mean_accuracy=('accuracy', 'mean'),
        std_accuracy=('accuracy', 'std'),
        mean_f1=('f1_score', 'mean'),
        std_f1=('f1_score', 'std')
    ).reset_index()

    # Handle NaN std (single fold/repeat cases) -> treat as 0 variance
    agg_df['std_accuracy'] = agg_df['std_accuracy'].fillna(0.0)
    agg_df['std_f1'] = agg_df['std_f1'].fillna(0.0)

    agg_df['cv_accuracy'] = agg_df.apply(
        lambda row: calculate_cv(row['std_accuracy'], row['mean_accuracy']), axis=1
    )
    agg_df['cv_f1'] = agg_df.apply(
        lambda row: calculate_cv(row['std_f1'], row['mean_f1']), axis=1
    )

    return agg_df[['dataset_id', 'model_name', 'mean_accuracy', 'cv_accuracy', 'mean_f1', 'cv_f1']]


def calculate_correlations(
    metrics_df: pd.DataFrame,
    props_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate Pearson (primary) and Spearman (secondary) correlations between
    CV metrics and dataset properties (n_samples, n_features).
    """
    if metrics_df.empty or props_df.empty:
        logger.warning("Empty metrics or properties dataframe provided to calculate_correlations")
        return pd.DataFrame()

    merged = pd.merge(metrics_df, props_df, on='dataset_id', how='inner')
    if merged.empty:
        logger.warning("No overlapping dataset_ids between metrics and properties")
        return pd.DataFrame()

    results = []
    cv_cols = ['cv_accuracy', 'cv_f1']
    prop_cols = ['n_samples', 'n_features']

    for cv_col in cv_cols:
        for prop_col in prop_cols:
            valid_data = merged[[cv_col, prop_col]].dropna()
            if len(valid_data) < 3:
                logger.warning(f"Not enough data points for correlation: {cv_col} vs {prop_col}")
                continue

            x = valid_data[prop_col].values
            y = valid_data[cv_col].values

            # Primary: Pearson
            pearson_r, pearson_p = stats.pearsonr(x, y)
            # Secondary: Spearman
            spearman_r, spearman_p = stats.spearmanr(x, y)

            results.append({
                'metric': cv_col,
                'property': prop_col,
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_r': spearman_r,
                'spearman_p': spearman_p
            })

    return pd.DataFrame(results)


def compute_regression_residuals(
    metrics_df: pd.DataFrame,
    props_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute residuals from log-log linear regression of log(CV) against log(n_samples) and log(n_features).
    This is a secondary metric. Pearson r remains the primary output per FR-004.
    """
    if metrics_df.empty or props_df.empty:
        logger.warning("Empty metrics or properties dataframe provided to compute_regression_residuals")
        return pd.DataFrame()

    merged = pd.merge(metrics_df, props_df, on='dataset_id', how='inner')
    if merged.empty:
        logger.warning("No overlapping dataset_ids between metrics and properties for regression")
        return pd.DataFrame()

    results = []
    cv_cols = ['cv_accuracy', 'cv_f1']
    prop_cols = ['n_samples', 'n_features']

    for cv_col in cv_cols:
        for prop_col in prop_cols:
            # Prepare data: log(CV) and log(property)
            # Filter out zero or negative values which are invalid for log
            valid_data = merged[[cv_col, prop_col]].dropna()
            valid_data = valid_data[valid_data[cv_col] > 0]
            valid_data = valid_data[valid_data[prop_col] > 0]

            if len(valid_data) < 3:
                logger.warning(f"Not enough valid data points for log-log regression: {cv_col} vs {prop_col}")
                continue

            log_cv = np.log(valid_data[cv_col].values)
            log_prop = np.log(valid_data[prop_col].values)

            # Fit linear regression: y = mx + c
            # Using scipy.stats.linregress
            slope, intercept, r_value, p_value, std_err = stats.linregress(log_prop, log_cv)

            # Calculate residuals: actual_y - predicted_y
            predicted_log_cv = slope * log_prop + intercept
            residuals = log_cv - predicted_log_cv

            # Store residuals per dataset_id
            for idx, row in valid_data.iterrows():
                results.append({
                    'dataset_id': row['dataset_id'],
                    'metric': cv_col,
                    'property': prop_col,
                    'log_cv': log_cv[list(valid_data.index).index(idx)],
                    'log_property': log_prop[list(valid_data.index).index(idx)],
                    'predicted_log_cv': predicted_log_cv[list(valid_data.index).index(idx)],
                    'residual': residuals[list(valid_data.index).index(idx)],
                    'regression_slope': slope,
                    'regression_r': r_value,
                    'regression_p': p_value
                })

    return pd.DataFrame(results)


def run_correlation_analysis(
    raw_path: Path,
    props_path: Path,
    output_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run full correlation analysis:
    1. Aggregate metrics
    2. Calculate correlations (Pearson primary, Spearman secondary)
    3. Compute regression residuals (secondary metric)
    4. Save results to CSV files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info(f"Loading raw evaluations from {raw_path}")
    raw_df = load_raw_evaluations(raw_path)
    logger.info(f"Loading dataset properties from {props_path}")
    props_df = load_dataset_properties(props_path)

    # Aggregate
    logger.info("Aggregating metrics...")
    metrics_df = aggregate_metrics(raw_df)
    logger.info(f"Aggregated metrics for {len(metrics_df)} (dataset, model) pairs")

    # Correlations
    logger.info("Calculating correlations...")
    corr_df = calculate_correlations(metrics_df, props_df)
    corr_path = output_dir / 'correlation_results.csv'
    if not corr_df.empty:
        corr_df.to_csv(corr_path, index=False)
        logger.info(f"Saved correlation results to {corr_path}")
    else:
        logger.warning("No correlations calculated; skipping save.")

    # Regression Residuals
    logger.info("Computing regression residuals...")
    residual_df = compute_regression_residuals(metrics_df, props_df)
    residual_path = output_dir / 'regression_residuals.csv'
    if not residual_df.empty:
        residual_df.to_csv(residual_path, index=False)
        logger.info(f"Saved regression residuals to {residual_path}")
    else:
        logger.warning("No regression residuals calculated; skipping save.")

    return metrics_df, corr_df, residual_df


def main():
    """Main entry point for correlation analysis."""
    setup_logging()
    base_dir = Path(__file__).parent.parent
    raw_path = base_dir / 'results' / 'raw_evaluations.csv'
    props_path = base_dir / 'data' / 'processed' / 'dataset_properties.csv'
    output_dir = base_dir / 'results'

    try:
        metrics_df, corr_df, residual_df = run_correlation_analysis(
            raw_path, props_path, output_dir
        )
        logger.info("Correlation analysis completed successfully.")
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()