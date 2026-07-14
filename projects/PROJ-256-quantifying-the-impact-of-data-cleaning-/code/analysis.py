"""
Analysis module for statistical testing and baseline analysis.
Implements t-tests, linear regression, and effect size calculations.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import scipy.stats as stats
from sklearn.linear_model import LinearRegression
from utils import setup_logging, pin_random_seed, compute_file_checksum
from config import Config, get_config

logger = setup_logging()

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load datasets from the raw data directory.
    
    Args:
        raw_dir: Path to the raw data directory.
    
    Returns:
        List of dictionaries containing dataset info (name, df, checksum).
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
        return datasets

    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                checksum = compute_file_checksum(filepath)
                datasets.append({
                    'name': os.path.splitext(filename)[0],
                    'df': df,
                    'checksum': checksum,
                    'path': filepath
                })
                logger.info(f"Loaded dataset: {filename} (rows: {len(df)}, checksum: {checksum[:8]}...)")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")

    return datasets

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Identify numerical columns in a DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify categorical columns in a DataFrame."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run an independent samples t-test.
    
    Args:
        df: DataFrame containing the data.
        predictor_col: Name of the binary predictor column.
        outcome_col: Name of the outcome column.
    
    Returns:
        Dictionary with p-value, confidence interval, and effect size.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        raise ValueError(f"Columns {predictor_col} or {outcome_col} not found in dataset.")
    
    # Ensure binary predictor
    unique_vals = df[predictor_col].unique()
    if len(unique_vals) != 2:
        logger.warning(f"Predictor {predictor_col} is not binary. Skipping t-test.")
        return {'p_value': None, 'ci': None, 'effect_size': None, 'error': 'Not binary'}
    
    group_0 = df[df[predictor_col] == unique_vals[0]][outcome_col].dropna()
    group_1 = df[df[predictor_col] == unique_vals[1]][outcome_col].dropna()
    
    if len(group_0) < 2 or len(group_1) < 2:
        logger.warning("One of the groups has fewer than 2 samples. Skipping t-test.")
        return {'p_value': None, 'ci': None, 'effect_size': None, 'error': 'Insufficient samples'}
    
    # Welch's t-test (assumes unequal variances)
    t_stat, p_val = stats.ttest_ind(group_0, group_1, equal_var=False)
    
    # 95% CI for difference in means
    mean_diff = group_1.mean() - group_0.mean()
    # Standard error of difference
    se_diff = np.sqrt(group_0.var() / len(group_0) + group_1.var() / len(group_1))
    # Degrees of freedom (Welch-Satterthwaite)
    df_val = (group_0.var()**2 / len(group_0)) + (group_1.var()**2 / len(group_1))
    df_val /= (group_0.var()**2 / (len(group_0)**2 * (len(group_0) - 1))) + \
              (group_1.var()**2 / (len(group_1)**2 * (len(group_1) - 1)))
    
    t_crit = stats.t.ppf(0.975, df_val)
    ci_lower = mean_diff - t_crit * se_diff
    ci_upper = mean_diff + t_crit * se_diff
    
    # Cohen's d
    pooled_std = np.sqrt(((len(group_0) - 1) * group_0.var() + (len(group_1) - 1) * group_1.var()) / (len(group_0) + len(group_1) - 2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / pooled_std
    
    # Validate results
    if not (0 < p_val < 1):
        logger.warning(f"P-value {p_val} out of bounds (0, 1).")
        p_val = max(0.0, min(1.0, p_val)) # Clamp for safety
    
    if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
        logger.warning(f"CI bounds [{ci_lower}, {ci_upper}] are not finite.")
        ci_lower, ci_upper = None, None
    
    return {
        'p_value': float(p_val),
        'ci': [float(ci_lower), float(ci_upper)] if ci_lower is not None else None,
        'effect_size': float(cohens_d),
        't_statistic': float(t_stat),
        'degrees_of_freedom': float(df_val)
    }

def run_linear_regression(df: pd.DataFrame, predictor_cols: List[str], outcome_col: str) -> Dict[str, Any]:
    """
    Run a linear regression.
    
    Args:
        df: DataFrame containing the data.
        predictor_cols: List of predictor column names.
        outcome_col: Name of the outcome column.
    
    Returns:
        Dictionary with R-squared, coefficients, and p-values for coefficients.
    """
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column {outcome_col} not found in dataset.")
    for col in predictor_cols:
        if col not in df.columns:
            raise ValueError(f"Predictor column {col} not found in dataset.")
    
    X = df[predictor_cols].dropna()
    y = df.loc[X.index, outcome_col].dropna()
    
    # Align indices after dropna
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(X) < len(predictor_cols) + 1:
        logger.warning("Insufficient samples for regression.")
        return {'r_squared': None, 'coefficients': [], 'p_values': [], 'error': 'Insufficient samples'}
    
    model = LinearRegression()
    model.fit(X, y)
    
    r_squared = model.score(X, y)
    coefficients = model.coef_.tolist()
    intercept = float(model.intercept_)
    
    # Calculate p-values for coefficients using statsmodels-like approach (approx)
    # We'll use a simple t-test for each coefficient against 0
    # Residuals
    residuals = y - model.predict(X)
    n = len(y)
    p = len(predictor_cols)
    mse = np.sum(residuals**2) / (n - p - 1)
    
    # Covariance matrix of coefficients: MSE * (X'X)^-1
    try:
        X_with_intercept = np.column_stack([np.ones(len(X)), X])
        XtX_inv = np.linalg.inv(X_with_intercept.T @ X_with_intercept)
        var_covar = mse * XtX_inv
        
        std_errors = np.sqrt(np.diag(var_covar))
        # t-statistics
        t_stats = np.append(intercept, coefficients) / std_errors
        # p-values (two-tailed)
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - p - 1))
        
        # Validate p-values
        p_values = [max(0.0, min(1.0, float(p))) for p in p_values]
        
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in regression. P-values not computed.")
        p_values = [None] * (p + 1)
    
    return {
        'r_squared': float(r_squared),
        'coefficients': coefficients,
        'intercept': intercept,
        'p_values': p_values,
        'std_errors': std_errors.tolist() if 'std_errors' in locals() else []
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Compute Cohen's d effect size.
    
    Args:
        group1: Series for group 1.
        group2: Series for group 2.
    
    Returns:
        Cohen's d value.
    """
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(), group2.var()
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean2 - mean1) / pooled_std

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Run full analysis on a single dataset.
    
    Args:
        df: DataFrame to analyze.
        dataset_name: Name of the dataset.
        config: Configuration object.
    
    Returns:
        Dictionary containing analysis results.
    """
    if config is None:
        config = get_config()
    
    # Identify numeric columns for outcome and binary for predictor
    # Heuristic: Last numeric column is outcome, first binary-like column is predictor
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        logger.warning(f"Not enough numeric columns in {dataset_name} for analysis.")
        return {'dataset': dataset_name, 'error': 'Insufficient numeric columns'}
    
    # Simple heuristic: try to find a binary column
    binary_col = None
    for col in numeric_cols:
        if df[col].nunique() == 2:
            binary_col = col
            break
    
    if binary_col is None:
        # Fallback: use first column as predictor, second as outcome
        binary_col = numeric_cols[0]
        outcome_col = numeric_cols[1]
        logger.warning(f"No binary column found. Using {binary_col} as predictor.")
    else:
        outcome_col = [c for c in numeric_cols if c != binary_col][0]
    
    logger.info(f"Analyzing {dataset_name}: Predictor={binary_col}, Outcome={outcome_col}")
    
    t_test_result = run_t_test(df, binary_col, outcome_col)
    regression_result = run_linear_regression(df, [binary_col], outcome_col)
    
    return {
        'dataset_name': dataset_name,
        'predictor': binary_col,
        'outcome': outcome_col,
        'n_rows': len(df),
        't_test': t_test_result,
        'regression': regression_result
    }

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame],
    output_file: Optional[str] = None,
    dataset_name: Optional[str] = None,
    config: Optional[Config] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Run a linear regression.

    Args:
        df: DataFrame containing the data.
        predictor_cols: List of predictor column names.
        outcome_col: Name of the outcome column.

    Returns:
        Dictionary with coefficients, R-squared, and p-values.
    """
    if outcome_col not in df.columns:
        logger.warning(f"Outcome column {outcome_col} not found.")
        return {}

    # Encode categorical predictors if any
    df_encoded = df.copy()
    categorical_cols = [c for c in predictor_cols if c in df_encoded.select_dtypes(include=['object', 'category']).columns]
    
    Handles multiple calling conventions:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    3. run_baseline_analysis(df_cleaned, dataset_name=..., config=config) -> returns dict
    
    Args:
        input_data: Path to raw directory OR a DataFrame.
        output_file: Path to output JSON file (required if input_data is a path).
        dataset_name: Name of the dataset (required if input_data is a DataFrame).
        config: Configuration object.
    
    Returns:
        If input was a path: True if successful, False otherwise.
        If input was a DataFrame: Dictionary of results.
    """
    if config is None:
        config = get_config()
    
    # Case 1: input_data is a path (string)
    if isinstance(input_data, str):
        if not output_file:
            raise ValueError("output_file is required when input_data is a path.")
        
        raw_dir = input_data
        datasets = load_datasets_from_raw(raw_dir)
        
        if not datasets:
            logger.error(f"No datasets found in {raw_dir}")
            return False
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'source_directory': raw_dir,
            'datasets': []
        }
        
        for ds in datasets:
            result = analyze_dataset(ds['df'], ds['name'], config)
            result['checksum'] = ds['checksum']
            all_results['datasets'].append(result)
        
        # Write to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Baseline metrics written to {output_file}")
        return True
    
    # Case 2: input_data is a DataFrame
    elif isinstance(input_data, pd.DataFrame):
        if not dataset_name:
            raise ValueError("dataset_name is required when input_data is a DataFrame.")
        
        result = analyze_dataset(input_data, dataset_name, config)
        return result
    
    else:
        raise TypeError("input_data must be a string (path) or pandas DataFrame.")

def main():
    """Main entry point for analysis module."""
    logger = setup_logging("INFO")
    config = get_config()
    
    # Example: Run on raw data if exists
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    if os.path.exists(raw_dir):
        success = run_baseline_analysis(raw_dir, output_file, config=config)
        if success:
            logger.info("Analysis complete.")
        else:
            logger.error("Analysis failed.")
    else:
        logger.warning(f"Raw data directory {raw_dir} not found. Skipping analysis.")

if __name__ == "__main__":
    main()
