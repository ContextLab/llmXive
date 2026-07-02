"""
Correlation Analysis Module for Alpha Oscillations and Working Memory Capacity Study.

This module implements statistical analysis including VIF calculation, collinearity
detection, partial correlations, FDR correction, LOSO cross-validation, and split-half
reliability analysis.

IMPORTANT: This analysis uses discrete electrode-metric pairs. Per plan.md Complexity
Tracking section, Cluster-Based Permutation Testing is explicitly REJECTED for this
study design. We use Benjamini-Hochberg FDR correction instead.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Import from project utilities
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging_config import setup_logging, get_logger
from utils.validation import load_and_validate_csv, exit_on_validation_failure

# Setup logger
logger = get_logger(__name__)

def load_metric_data(file_path: str, required_columns: List[str]) -> pd.DataFrame:
    """
    Load and validate metric data from CSV file.

    Args:
        file_path: Path to the CSV file
        required_columns: List of columns that must be present

    Returns:
        DataFrame with the metric data
    """
    logger.info(f"Loading metric data from {file_path}")
    df = load_and_validate_csv(file_path, required_columns)
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def merge_metrics(alpha_power_file: str, plv_file: str, wm_file: str) -> pd.DataFrame:
    """
    Merge alpha power, PLV, and working memory capacity metrics.

    Args:
        alpha_power_file: Path to alpha power CSV
        plv_file: Path to PLV CSV
        wm_file: Path to WM capacity CSV

    Returns:
        Merged DataFrame with all metrics per subject
    """
    logger.info("Merging metrics from multiple sources")

    alpha_df = load_metric_data(alpha_power_file, ['subject_id', 'electrode', 'alpha_power'])
    plv_df = load_metric_data(plv_file, ['subject_id', 'pair_id', 'plv_value'])
    wm_df = load_metric_data(wm_file, ['subject_id', 'k_score'])

    # Pivot alpha power to have one column per electrode
    alpha_pivot = alpha_df.pivot(index='subject_id', columns='electrode', values='alpha_power').reset_index()
    alpha_pivot.columns.name = None

    # Pivot PLV to have one column per pair
    plv_pivot = plv_df.pivot(index='subject_id', columns='pair_id', values='plv_value').reset_index()
    plv_pivot.columns.name = None

    # Merge all dataframes
    merged = alpha_pivot.merge(plv_pivot, on='subject_id', how='inner')
    merged = merged.merge(wm_df[['subject_id', 'k_score']], on='subject_id', how='inner')

    logger.info(f"Merged dataset has {len(merged)} subjects and {len(merged.columns)} features")
    return merged

def calculate_vif(df: pd.DataFrame, feature_columns: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.

    Args:
        df: DataFrame with features
        feature_columns: List of column names to calculate VIF for

    Returns:
        Dictionary mapping feature names to VIF values
    """
    logger.info("Calculating Variance Inflation Factors")

    vif_data = {}
    X = df[feature_columns].values

    for i, col in enumerate(feature_columns):
        # Create design matrix with this column as dependent
        y = X[:, i]
        X_other = np.column_stack([X[:, j] for j in range(X.shape[1]) if j != i])

        if X_other.shape[1] == 0:
            vif_data[col] = 1.0
            continue

        # Fit linear model
        try:
            # Add intercept
            X_other_with_intercept = np.column_stack([np.ones(X_other.shape[0]), X_other])
            beta = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)[0]
            y_pred = X_other_with_intercept @ beta

            # Calculate R-squared
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                vif_data[col] = float('inf')
            else:
                vif_data[col] = 1.0 / (1 - r_squared)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')

    return vif_data

def detect_collinearity(vif_data: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Detect features with high collinearity based on VIF threshold.

    Args:
        vif_data: Dictionary of VIF values
        threshold: VIF threshold for flagging (default 5.0)

    Returns:
        List of feature names with VIF > threshold
    """
    collinear_features = [k for k, v in vif_data.items() if v > threshold]
    if collinear_features:
        logger.warning(f"Detected collinearity in features: {collinear_features} (VIF > {threshold})")
    else:
        logger.info("No significant collinearity detected (all VIF <= 5.0)")
    return collinear_features

def prepare_pca_components(df: pd.DataFrame, feature_columns: List[str], n_components: int = 2) -> Tuple[np.ndarray, List[str]]:
    """
    Prepare PCA components for collinear features.

    Args:
        df: DataFrame with features
        feature_columns: List of feature column names
        n_components: Number of PCA components to extract

    Returns:
        Tuple of (component matrix, component names)
    """
    from sklearn.decomposition import PCA

    logger.info(f"Preparing {n_components} PCA components for collinear features")
    X = df[feature_columns].values

    # Standardize
    X_std = (X - X.mean(axis=0)) / X.std(axis=0)

    pca = PCA(n_components=n_components)
    components = pca.fit_transform(X_std)

    component_names = [f'PC{i+1}' for i in range(n_components)]
    logger.info(f"PCA explained variance: {pca.explained_variance_ratio_}")

    return components, component_names

def calculate_partial_correlation(df: pd.DataFrame, x_col: str, y_col: str, control_cols: List[str]) -> Dict[str, Any]:
    """
    Calculate partial correlation between x and y, controlling for other variables.

    Args:
        df: DataFrame with all variables
        x_col: Name of first variable
        y_col: Name of second variable
        control_cols: List of control variable names

    Returns:
        Dictionary with correlation coefficient, p-value, and sample size
    """
    logger.info(f"Calculating partial correlation: {x_col} vs {y_col} (controlling for {control_cols})")

    # Get data
    x = df[x_col].values
    y = df[y_col].values
    controls = df[control_cols].values if control_cols else np.array([]).reshape(len(df), 0)

    # Calculate residuals
    if controls.shape[1] > 0:
        # Regress x on controls
        X_control = np.column_stack([np.ones(len(df)), controls])
        beta_x = np.linalg.lstsq(X_control, x, rcond=None)[0]
        x_resid = x - X_control @ beta_x

        # Regress y on controls
        beta_y = np.linalg.lstsq(X_control, y, rcond=None)[0]
        y_resid = y - X_control @ beta_y
    else:
        x_resid = x
        y_resid = y

    # Calculate correlation of residuals
    r, p_value = stats.pearsonr(x_resid, y_resid)

    result = {
        'correlation': float(r),
        'p_value': float(p_value),
        'n': len(df),
        'control_variables': control_cols
    }

    logger.info(f"Partial correlation: r={r:.4f}, p={p_value:.4f}")
    return result

def apply_fdr_correction(p_values: List[float], method: str = 'fdr_bh') -> Tuple[List[float], List[bool]]:
    """
    Apply False Discovery Rate (Benjamini-Hochberg) correction to p-values.

    Per plan.md Complexity Tracking section: Cluster-Based Permutation Testing is
    explicitly REJECTED for discrete electrode-metric pairs. We use FDR correction
    instead to handle multiple comparisons.

    Args:
        p_values: List of raw p-values from hypothesis tests
        method: Correction method (default 'fdr_bh' for Benjamini-Hochberg)

    Returns:
        Tuple of (adjusted p-values, boolean mask of significant results)
    """
    logger.info(f"Applying FDR correction ({method}) to {len(p_values)} tests")

    if len(p_values) == 0:
        return [], []

    # Use statsmodels for FDR correction
    rejected, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method=method)

    logger.info(f"FDR correction complete: {sum(rejected)} of {len(p_values)} tests significant at q < 0.05")

    return list(p_corrected), list(rejected)

def run_loso_cross_validation(df: pd.DataFrame, X_cols: List[str], y_col: str, 
                              correlation_func) -> Dict[str, Any]:
    """
    Run Leave-One-Subject-Out cross-validation for correlation analysis.

    Per FR-008: This implements subject-level LOSO (not trial-level) as specified in Plan.

    Args:
        df: DataFrame with features and target
        X_cols: List of feature column names
        y_col: Target variable column name
        correlation_func: Function to calculate correlation (e.g., calculate_partial_correlation)

    Returns:
        Dictionary with cross-validation results
    """
    logger.info(f"Running LOSO cross-validation with {len(df)} subjects")

    n_subjects = len(df)
    correlations = []
    p_values = []

    for i in range(n_subjects):
        # Leave one subject out
        train_idx = [j for j in range(n_subjects) if j != i]
        test_idx = [i]

        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]

        if len(train_df) < 10:  # Minimum sample size for correlation
            logger.warning(f"Skipping fold {i}: only {len(train_df)} training samples")
            continue

        # Calculate correlation on training set
        result = correlation_func(train_df, X_cols[0], y_col, X_cols[1:] if len(X_cols) > 1 else [])
        correlations.append(result['correlation'])
        p_values.append(result['p_value'])

        if i % 10 == 0:
            logger.info(f"LOSO fold {i}/{n_subjects} complete")

    # Calculate cross-validated statistics
    mean_r = np.mean(correlations)
    std_r = np.std(correlations)
    mean_p = np.mean(p_values)

    result = {
        'n_subjects': n_subjects,
        'mean_correlation': float(mean_r),
        'std_correlation': float(std_r),
        'mean_p_value': float(mean_p),
        'all_correlations': correlations,
        'all_p_values': p_values
    }

    logger.info(f"LOSO CV complete: mean r={mean_r:.4f} (SD={std_r:.4f})")
    return result

def run_split_half_reliability(df: pd.DataFrame, X_col: str, y_col: str) -> Dict[str, Any]:
    """
    Calculate split-half reliability for the correlation analysis.

    Args:
        df: DataFrame with features and target
        X_col: Feature column name
        y_col: Target column name

    Returns:
        Dictionary with reliability metrics
    """
    logger.info("Calculating split-half reliability")

    n = len(df)
    indices = np.arange(n)
    np.random.shuffle(indices)

    # Split data in half
    half1_idx = indices[:n//2]
    half2_idx = indices[n//2:]

    df1 = df.iloc[half1_idx]
    df2 = df.iloc[half2_idx]

    if len(df1) < 5 or len(df2) < 5:
        logger.warning("Insufficient data for split-half reliability")
        return {'status': 'INSUFFICIENT_DATA', 'reliability': None}

    # Calculate correlation in each half
    r1, p1 = stats.pearsonr(df1[X_col], df1[y_col])
    r2, p2 = stats.pearsonr(df2[X_col], df2[y_col])

    # Spearman-Brown prophecy formula
    reliability = (2 * r1 * r2) / (r1 * r2 + 1) if (r1 * r2 + 1) != 0 else 0

    result = {
        'half1_correlation': float(r1),
        'half2_correlation': float(r2),
        'reliability_coefficient': float(reliability),
        'n_half1': len(df1),
        'n_half2': len(df2)
    }

    logger.info(f"Split-half reliability: r={reliability:.4f}")
    return result

def main():
    """
    Main function to run correlation analysis pipeline.

    This function:
    1. Loads alpha power, PLV, and WM capacity metrics
    2. Merges datasets by subject
    3. Calculates VIF and handles collinearity
    4. Computes partial correlations
    5. Applies FDR correction (Benjamini-Hochberg)
    6. Runs LOSO cross-validation
    7. Calculates split-half reliability
    8. Saves results to data/results/
    """
    logger.info("=" * 60)
    logger.info("Starting Correlation Analysis Pipeline")
    logger.info("=" * 60)

    # Configuration
    base_dir = Path(__file__).parent.parent
    metrics_dir = base_dir / "data" / "metrics"
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    alpha_file = metrics_dir / "alpha_power.csv"
    plv_file = metrics_dir / "plv.csv"
    wm_file = metrics_dir / "wm_capacity.csv"

    # Check for required files
    if not alpha_file.exists() or not plv_file.exists() or not wm_file.exists():
        logger.error("Missing required metric files. Run metric extraction first.")
        sys.exit(1)

    # Load and merge data
    merged_df = merge_metrics(str(alpha_file), str(plv_file), str(wm_file))

    if len(merged_df) < 30:
        logger.error(f"Insufficient subjects for analysis (N={len(merged_df)}). Minimum 30 required.")
        sys.exit(1)

    # Identify feature columns (exclude subject_id and target)
    feature_cols = [col for col in merged_df.columns if col not in ['subject_id', 'k_score']]

    if not feature_cols:
        logger.error("No feature columns found in merged dataset")
        sys.exit(1)

    # Calculate VIF
    vif_data = calculate_vif(merged_df, feature_cols)
    collinear_features = detect_collinearity(vif_data)

    # Handle collinearity
    if collinear_features:
        logger.warning("Collinearity detected. Preparing PCA components.")
        pca_components, pca_names = prepare_pca_components(merged_df, collinear_features, n_components=2)
        # Add PCA components to dataframe
        for i, name in enumerate(pca_names):
            merged_df[name] = pca_components[:, i]
        # Use PCA components instead of collinear features
        analysis_features = [col for col in feature_cols if col not in collinear_features] + pca_names
    else:
        analysis_features = feature_cols

    # Calculate partial correlations for each feature
    correlation_results = []
    p_values_raw = []

    for feature in analysis_features:
        result = calculate_partial_correlation(merged_df, feature, 'k_score', 
                                             [f for f in analysis_features if f != feature])
        result['feature'] = feature
        correlation_results.append(result)
        p_values_raw.append(result['p_value'])

    # Apply FDR correction
    # NOTE: Per plan.md Complexity Tracking section, Cluster-Based Permutation Testing
    # is explicitly REJECTED for discrete electrode-metric pairs. We use FDR correction.
    p_values_corrected, is_significant = apply_fdr_correction(p_values_raw)

    # Update results with corrected p-values
    for i, result in enumerate(correlation_results):
        result['p_value_fdr'] = p_values_corrected[i]
        result['is_significant_fdr'] = is_significant[i]

    # Run LOSO cross-validation
    if len(analysis_features) >= 1:
        loso_results = run_loso_cross_validation(
            merged_df, 
            analysis_features[:3] if len(analysis_features) >= 3 else analysis_features, 
            'k_score',
            calculate_partial_correlation
        )
    else:
        loso_results = {'status': 'NO_FEATURES'}

    # Run split-half reliability
    if len(analysis_features) > 0:
        reliability_results = run_split_half_reliability(merged_df, analysis_features[0], 'k_score')
    else:
        reliability_results = {'status': 'NO_FEATURES'}

    # Save results
    results = {
        'correlation_results': correlation_results,
        'vif_analysis': vif_data,
        'collinear_features': collinear_features,
        'loso_cv': loso_results,
        'split_half_reliability': reliability_results,
        'fdr_method': 'benjamini-hochberg',
        'note': 'Cluster-Based Permutation Testing explicitly rejected per plan.md'
    }

    output_file = results_dir / "correlation_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Results saved to {output_file}")
    logger.info("=" * 60)
    logger.info("Correlation Analysis Pipeline Complete")
    logger.info("=" * 60)

    return results

if __name__ == "__main__":
    main()