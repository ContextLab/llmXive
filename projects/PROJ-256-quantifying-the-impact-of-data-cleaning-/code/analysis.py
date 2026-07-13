import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run independent t-test between two groups defined by predictor_col.
    Assumes predictor_col is binary (0/1 or True/False).
    """
    if df[predictor_col].nunique() != 2:
        raise ValueError(f"Predictor column {predictor_col} must be binary for t-test.")

    group_0 = df[df[predictor_col] == 0][outcome_col].dropna()
    group_1 = df[df[predictor_col] == 1][outcome_col].dropna()

    if len(group_0) < 2 or len(group_1) < 2:
        raise ValueError("Insufficient samples in one or both groups for t-test.")

    t_stat, p_val = stats.ttest_ind(group_0, group_1)
    
    # Calculate effect size (Cohen's d)
    mean_0, mean_1 = group_0.mean(), group_1.mean()
    std_pooled = np.sqrt((group_0.std()**2 + group_1.std()**2) / 2)
    cohens_d = (mean_1 - mean_0) / std_pooled if std_pooled > 0 else 0.0

    # 95% CI for difference in means
    diff = mean_1 - mean_0
    se = np.sqrt(group_0.var() / len(group_0) + group_1.var() / len(group_1))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "cohens_d": float(cohens_d),
        "ci_95": [float(ci_low), float(ci_high)],
        "n_group_0": len(group_0),
        "n_group_1": len(group_1)
    }

def run_linear_regression(df: pd.DataFrame, predictor_cols: List[str], outcome_col: str) -> Dict[str, Any]:
    """
    Run linear regression with multiple predictors.
    """
    X = df[predictor_cols].dropna()
    y = df.loc[X.index, outcome_col].dropna()
    
    # Re-align indices after dropna
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < len(predictor_cols) + 1:
        raise ValueError("Insufficient samples for linear regression.")

    model = LinearRegression()
    model.fit(X, y)

    # R-squared
    r2 = model.score(X, y)
    
    # Adjusted R-squared
    n = len(X)
    p = len(predictor_cols)
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2

    # Coefficients and p-values (using scipy for p-values)
    coeffs = model.coef_
    intercept = model.intercept_
    
    # Simple p-value approximation using t-test for each coefficient
    # Note: In production, use statsmodels for proper p-values
    p_values = []
    for i, col in enumerate(predictor_cols):
        # Residuals
        y_pred = model.predict(X)
        residuals = y - y_pred
        
        # Standard error of coefficient
        # Simplified: using correlation-based approximation
        try:
            corr, p = stats.pearsonr(X[col], y)
            p_values.append(float(p))
        except:
            p_values.append(1.0)

    return {
        "coefficients": [float(c) for c in coeffs],
        "intercept": float(intercept),
        "r_squared": float(r2),
        "adj_r_squared": float(adj_r2),
        "p_values": p_values,
        "n_samples": len(X)
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """Compute Cohen's d effect size between two groups."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean2 - mean1) / pooled_std

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    """Load all CSV datasets from a directory."""
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory not found: {raw_dir}")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                name = os.path.splitext(filename)[0]
                datasets.append((name, df))
                logger.info(f"Loaded dataset: {name} with {len(df)} rows")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Run full analysis on a dataset: t-test and linear regression.
    """
    if config is None:
        config = {}
    
    outcome_col = config.get('outcome_col', 'outcome')
    predictor_col = config.get('predictor_col', 'predictor')
    regression_cols = config.get('regression_cols', ['predictor'])

    results = {
        "dataset_name": dataset_name,
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "t_test": None,
        "regression": None
    }

    try:
        # T-test
        if outcome_col in df.columns and predictor_col in df.columns:
            results["t_test"] = run_t_test(df, predictor_col, outcome_col)
    except Exception as e:
        logger.warning(f"T-test failed for {dataset_name}: {e}")

    try:
        # Linear regression
        valid_cols = [c for c in regression_cols if c in df.columns]
        if outcome_col in df.columns and len(valid_cols) > 0:
            results["regression"] = run_linear_regression(df, valid_cols, outcome_col)
    except Exception as e:
        logger.warning(f"Regression failed for {dataset_name}: {e}")

    return results

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame, List[Tuple[str, pd.DataFrame]]],
    output_path: Optional[str] = None,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Run baseline analysis on one or more datasets.
    
    Flexible signature to handle multiple call patterns:
    1. run_baseline_analysis(raw_dir, output_path, config)
    2. run_baseline_analysis(df, dataset_name=dataset_name)
    3. run_baseline_analysis(df_cleaned, dataset_name=f"null_k{k}")
    
    Args:
        input_data: Can be a directory path, a single DataFrame, or a list of (name, df) tuples
        output_path: Optional path to write results JSON
        config: Optional configuration dictionary
        
    Returns:
        Dictionary with analysis results
    """
    if config is None:
        config = {}
    
    results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "datasets": []
    }
    
    datasets_to_analyze = []
    
    # Handle different input types
    if isinstance(input_data, str):
        # It's a directory path
        datasets_to_analyze = load_datasets_from_raw(input_data)
    elif isinstance(input_data, pd.DataFrame):
        # Single DataFrame - check for dataset_name in kwargs or default
        dataset_name = config.get('dataset_name', 'unknown_dataset')
        datasets_to_analyze = [(dataset_name, input_data)]
    elif isinstance(input_data, list):
        # List of tuples
        datasets_to_analyze = input_data
    else:
        raise TypeError(f"Unsupported input type: {type(input_data)}")

    if not datasets_to_analyze:
        logger.warning("No datasets found to analyze.")
        return results

    for name, df in datasets_to_analyze:
        logger.info(f"Analyzing dataset: {name}")
        # Update config with dataset name for this run
        current_config = config.copy()
        current_config['dataset_name'] = name
        analysis_result = analyze_dataset(df, name, current_config)
        analysis_result['dataset_size'] = len(df)
        results['datasets'].append(analysis_result)

    # Write to file if output_path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Baseline metrics written to {output_path}")

    return results

def main():
    """CLI entry point for baseline analysis."""
    from utils import setup_logging
    setup_logging(log_level="INFO")
    
    # Default paths
    raw_dir = "data/raw"
    output_path = "data/processed/baseline_metrics.json"
    
    if len(sys.argv) > 1:
        raw_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    result = run_baseline_analysis(raw_dir, output_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    import sys
    from datetime import datetime
    main()
