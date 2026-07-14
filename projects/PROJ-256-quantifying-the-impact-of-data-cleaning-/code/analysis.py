"""
Analysis module for statistical inference (t-tests, linear regression).
Provides functions for baseline analysis and effect size calculation.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load all CSV/Excel datasets from the raw directory.
    Returns a list of dicts with 'df', 'name', 'path'.
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets

    for filename in os.listdir(raw_dir):
        filepath = os.path.join(raw_dir, filename)
        if not os.path.isfile(filepath):
            continue

        df = None
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                continue

            if df is not None and not df.empty:
                datasets.append({
                    "df": df,
                    "name": os.path.splitext(filename)[0],
                    "path": filepath
                })
                logger.info(f"Loaded dataset: {filename} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")

    return datasets

def run_t_test(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Perform an independent t-test between groups defined by group_col on value_col.
    Returns p-value, confidence interval, and effect size (Cohen's d).
    """
    if group_col not in df.columns or value_col not in df.columns:
        logger.error(f"Columns {group_col} or {value_col} not found.")
        return {"error": "columns_missing"}

    # Drop NaNs
    data = df[[group_col, value_col]].dropna()
    if len(data) < 2:
        return {"error": "insufficient_data"}

    groups = data[group_col].unique()
    if len(groups) < 2:
        return {"error": "need_two_groups"}

    # Assume binary groups for simplicity, or pick first two
    g1, g2 = groups[:2]
    vals1 = data[data[group_col] == g1][value_col]
    vals2 = data[data[group_col] == g2][value_col]

    if len(vals1) < 2 or len(vals2) < 2:
        return {"error": "insufficient_group_size"}

    # T-test
    t_stat, p_val = stats.ttest_ind(vals1, vals2, equal_var=False) # Welch's t-test

    # Confidence Interval for difference of means
    mean1, mean2 = vals1.mean(), vals2.mean()
    diff = mean1 - mean2
    # Standard error of difference
    se1 = vals1.std(ddof=1) / np.sqrt(len(vals1))
    se2 = vals2.std(ddof=1) / np.sqrt(len(vals2))
    se_diff = np.sqrt(se1**2 + se2**2)
    # 95% CI
    df_deg = len(vals1) + len(vals2) - 2
    crit = stats.t.ppf(0.975, df_deg)
    ci_low = diff - crit * se_diff
    ci_high = diff + crit * se_diff

    # Cohen's d
    pooled_std = np.sqrt(((len(vals1)-1)*vals1.var(ddof=1) + (len(vals2)-1)*vals2.var(ddof=1)) / df_deg)
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = diff / pooled_std

    # Validate p-value
    if not (0 < p_val < 1):
        logger.warning(f"Invalid p-value {p_val} for t-test. Clamping.")
        p_val = max(0.0001, min(0.9999, p_val))

    return {
        "test": "t_test",
        "p_value": float(p_val),
        "ci_95": [float(ci_low), float(ci_high)],
        "effect_size_cohen_d": float(cohens_d),
        "n1": int(len(vals1)),
        "n2": int(len(vals2))
    }

def run_linear_regression(df: pd.DataFrame, outcome_col: str, predictor_cols: List[str]) -> Dict[str, Any]:
    """
    Perform linear regression. Returns R-squared, p-values for coefficients, and CI.
    """
    if outcome_col not in df.columns:
        logger.error(f"Outcome column {outcome_col} not found.")
        return {"error": "outcome_missing"}

    # Ensure predictors exist
    missing = [c for c in predictor_cols if c not in df.columns]
    if missing:
        logger.warning(f"Predictor columns missing: {missing}. Skipping those.")
        predictor_cols = [c for c in predictor_cols if c in df.columns]

    if not predictor_cols:
        return {"error": "no_valid_predictors"}

    data = df[[outcome_col] + predictor_cols].dropna()
    if len(data) < len(predictor_cols) + 1:
        return {"error": "insufficient_data"}

    y = data[outcome_col]
    X = data[predictor_cols]
    X = sm.add_constant(X)

    model = ols(f"{outcome_col} ~ " + " + ".join(predictor_cols), data=data).fit()

    # Extract results
    r_squared = float(model.rsquared)
    params = model.params
    p_values = model.pvalues
    conf_int = model.conf_int(alpha=0.05)

    # Validate p-values
    clean_p = []
    for p in p_values:
        if not (0 < p < 1):
            clean_p.append(max(0.0001, min(0.9999, p)))
        else:
            clean_p.append(p)

    result = {
        "test": "linear_regression",
        "r_squared": r_squared,
        "coefficients": {},
        "p_values": {},
        "ci_95": {}
    }

    for i, col in enumerate(predictor_cols):
        result["coefficients"][col] = float(params[col])
        result["p_values"][col] = float(clean_p[i+1]) # Skip intercept
        result["ci_95"][col] = [float(conf_int.iloc[i+1, 0]), float(conf_int.iloc[i+1, 1])]

    # Intercept
    result["coefficients"]["intercept"] = float(params["const"])
    result["p_values"]["intercept"] = float(clean_p[0])
    result["ci_95"]["intercept"] = [float(conf_int.iloc[0, 0]), float(conf_int.iloc[0, 1])]

    return result

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """Compute Cohen's d for two groups."""
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    n1, n2 = len(group1), len(group2)
    
    if n1 + n2 - 2 <= 0:
        return 0.0
        
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Perform full analysis on a dataset: t-test and regression.
    Heuristically selects columns if not specified.
    """
    logger.info(f"Analyzing dataset: {dataset_name}")
    
    # Heuristics for column selection
    # Find numeric columns for regression
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    outcome_col = None
    predictor_cols = []
    group_col = None
    value_col = None
    
    # Try to find a likely outcome (last numeric or 'price', 'cost', 'y')
    for c in ['price', 'cost', 'amount', 'total', 'y', 'target']:
        if c in numeric_cols:
            outcome_col = c
            break
    if not outcome_col and len(numeric_cols) > 1:
        outcome_col = numeric_cols[-1]
        
    # Predictors: all other numerics
    if outcome_col:
        predictor_cols = [c for c in numeric_cols if c != outcome_col]
        
    # For t-test: need a binary categorical and a numeric
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        # Find a binary categorical
        for c in categorical_cols:
            if df[c].nunique() == 2:
                group_col = c
                value_col = numeric_cols[0]
                break
        if not group_col:
            # Pick first categorical and first numeric
            group_col = categorical_cols[0]
            value_col = numeric_cols[0]

    results = {
        "dataset_name": dataset_name,
        "t_test": None,
        "regression": None
    }
    
    if group_col and value_col:
        results["t_test"] = run_t_test(df, group_col, value_col)
        
    if outcome_col and predictor_cols:
        results["regression"] = run_linear_regression(df, outcome_col, predictor_cols)
        
    return results

def run_baseline_analysis(
    input_data: Union[str, Dict, pd.DataFrame],
    dataset_name: Optional[str] = None,
    output_file: Optional[str] = None,
    config: Optional[Dict] = None
) -> Union[Dict[str, Any], bool]:
    """
    Flexible entry point for baseline analysis.
    
    Signatures supported:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=...) -> returns dict
    3. run_baseline_analysis({"path": ...}, dataset_name=..., config=...) -> returns dict
    """
    logger.info("Running baseline analysis with flexible signature handling.")
    
    # Detect signature
    if isinstance(input_data, str):
        # Case 1: Directory path -> Load all, write to output_file
        if output_file is None:
            logger.error("Output file required when input is a directory path.")
            return False
        
        raw_dir = input_data
        datasets = load_datasets_from_raw(raw_dir)
        
        if not datasets:
            logger.error("No datasets found in raw directory.")
            return False
        
        all_results = []
        for ds in datasets:
            res = analyze_dataset(ds["df"], ds["name"], config)
            all_results.append(res)
        
        try:
            with open(output_file, 'w') as f:
                json.dump({"datasets": all_results}, f, indent=2)
            logger.info(f"Wrote baseline metrics to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to write output: {e}")
            return False
        
    elif isinstance(input_data, dict):
        # Case 3: Dict with path or data
        if "path" in input_data:
            # Load from specific file
            path = input_data["path"]
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            elif path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(path)
            else:
                logger.error(f"Unsupported file format: {path}")
                return {}
            
            name = dataset_name or os.path.splitext(os.path.basename(path))[0]
            return analyze_dataset(df, name, config)
        elif "df" in input_data:
            # Dict with df key
            df = input_data["df"]
            name = dataset_name or "unknown"
            return analyze_dataset(df, name, config)
        else:
            logger.error("Invalid dict input for analysis.")
            return {}
            
    elif isinstance(input_data, pd.DataFrame):
        # Case 2: DataFrame directly
        if dataset_name is None:
            dataset_name = "unknown_dataframe"
        return analyze_dataset(input_data, dataset_name, config)
        
    else:
        logger.error(f"Unsupported input type: {type(input_data)}")
        return {}

def main():
    """CLI entry point for analysis module."""
    # Default usage for CLI
    import argparse
    parser = argparse.ArgumentParser(description="Run baseline analysis")
    parser.add_argument("--input", "-i", required=True, help="Input directory or file path")
    parser.add_argument("--output", "-o", default="data/processed/baseline_metrics.json", help="Output JSON file")
    args = parser.parse_args()
    
    success = run_baseline_analysis(args.input, output_file=args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    import sys
    main()
