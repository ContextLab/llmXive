"""
Analysis module for statistical inference tasks.

Implements t-tests, linear regressions, and effect size calculations.
Provides a unified `run_baseline_analysis` function that handles multiple
calling signatures as required by the pipeline.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.weightstats import ttest_ind

logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[pd.DataFrame]:
    """Load all CSV datasets from the raw directory."""
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                datasets.append(df)
                logger.info(f"Loaded dataset: {filename}")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def run_t_test(df: pd.DataFrame, outcome_col: str, group_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform a t-test.
    If group_col is provided, performs an independent t-test between groups.
    Otherwise, performs a one-sample t-test against 0 (or mean).
    """
    if group_col:
        if group_col not in df.columns:
            raise ValueError(f"Group column '{group_col}' not found in dataframe.")
        groups = df[group_col].unique()
        if len(groups) < 2:
            logger.warning(f"Not enough groups for t-test in {outcome_col}")
            return {"p_value": np.nan, "statistic": np.nan, "ci": [np.nan, np.nan]}
        
        # Assume binary for simplicity if >2, or take first two
        g1 = groups[0]
        g2 = groups[1] if len(groups) > 1 else None
        
        if g2 is None:
            return {"p_value": np.nan, "statistic": np.nan, "ci": [np.nan, np.nan]}
        
        mask1 = df[group_col] == g1
        mask2 = df[group_col] == g2
        
        # Drop NaNs
        x1 = df.loc[mask1, outcome_col].dropna()
        x2 = df.loc[mask2, outcome_col].dropna()
        
        if len(x1) < 2 or len(x2) < 2:
            return {"p_value": np.nan, "statistic": np.nan, "ci": [np.nan, np.nan]}
        
        # Independent t-test
        stat, p_val = ttest_ind(x1, x2, equal_var=False) # Welch's t-test
        
        # Calculate 95% CI for difference in means
        mean1, mean2 = x1.mean(), x2.mean()
        diff = mean1 - mean2
        # Standard error of difference
        se1 = x1.std(ddof=1) / np.sqrt(len(x1))
        se2 = x2.std(ddof=1) / np.sqrt(len(x2))
        se_diff = np.sqrt(se1**2 + se2**2)
        
        # CI
        df_deg = len(x1) + len(x2) - 2
        t_crit = stats.t.ppf(0.975, df_deg)
        ci_low = diff - t_crit * se_diff
        ci_high = diff + t_crit * se_diff
        
        return {
            "p_value": float(p_val),
            "statistic": float(stat),
            "ci": [float(ci_low), float(ci_high)],
            "method": "independent_ttest"
        }
    else:
        # One sample t-test against 0
        x = df[outcome_col].dropna()
        if len(x) < 2:
            return {"p_value": np.nan, "statistic": np.nan, "ci": [np.nan, np.nan]}
        
        stat, p_val = stats.ttest_1samp(x, 0.0)
        mean = x.mean()
        se = x.std(ddof=1) / np.sqrt(len(x))
        t_crit = stats.t.ppf(0.975, len(x)-1)
        ci_low = mean - t_crit * se
        ci_high = mean + t_crit * se
        
        return {
            "p_value": float(p_val),
            "statistic": float(stat),
            "ci": [float(ci_low), float(ci_high)],
            "method": "one_sample_ttest"
        }

def run_linear_regression(df: pd.DataFrame, outcome_col: str, feature_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run a linear regression.
    If feature_cols is None, uses all other numeric columns as features.
    """
    if feature_cols is None:
        # Select numeric columns excluding outcome
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if outcome_col in numeric_cols:
            numeric_cols.remove(outcome_col)
        feature_cols = numeric_cols
    
    if not feature_cols:
        return {"r_squared": np.nan, "coefficients": [], "p_values": [], "method": "no_features"}
    
    # Ensure features and outcome are numeric and drop NaNs
    X = df[feature_cols].dropna()
    y = df.loc[X.index, outcome_col].dropna()
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(X) < 5: # Need enough data points
        return {"r_squared": np.nan, "coefficients": [], "p_values": [], "method": "insufficient_data"}
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    coefs = model.params.tolist()
    p_vals = model.pvalues.tolist()
    r_sq = model.rsquared
    
    return {
        "r_squared": float(r_sq),
        "coefficients": [float(c) for c in coefs],
        "p_values": [float(p) for p in p_vals],
        "method": "ols"
    }

def compute_effect_size_cohen_d(df: pd.DataFrame, outcome_col: str, group_col: str) -> float:
    """Compute Cohen's d for two groups."""
    groups = df[group_col].unique()
    if len(groups) < 2:
        return np.nan
    
    g1, g2 = groups[0], groups[1]
    x1 = df.loc[df[group_col] == g1, outcome_col].dropna()
    x2 = df.loc[df[group_col] == g2, outcome_col].dropna()
    
    if len(x1) < 2 or len(x2) < 2:
        return np.nan
    
    mean1, mean2 = x1.mean(), x2.mean()
    std1, std2 = x1.std(ddof=1), x2.std(ddof=1)
    n1, n2 = len(x1), len(x2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return float((mean1 - mean2) / pooled_std)

def analyze_dataset(
    df: pd.DataFrame, 
    dataset_name: str, 
    outcome_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform full analysis on a dataset.
    Returns a dict with t-test, regression, and effect size results.
    """
    if outcome_col is None:
        # Infer outcome: last numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return {"error": "No numeric columns found"}
        outcome_col = numeric_cols[-1]
    
    # Check if outcome_col exists
    if outcome_col not in df.columns:
        return {"error": f"Outcome column '{outcome_col}' not found"}
    
    result = {
        "dataset_name": dataset_name,
        "outcome_column": outcome_col,
        "n_rows": len(df),
        "t_test": {},
        "regression": {},
        "effect_size": {}
    }
    
    # T-Test: Try to find a binary grouping column
    # Heuristic: Look for a column with 2 unique values
    group_col = None
    for col in df.columns:
        if col == outcome_col:
            continue
        if df[col].nunique() == 2 and df[col].dtype in ['int64', 'float64', 'object', 'bool']:
            group_col = col
            break
    
    if group_col:
        t_res = run_t_test(df, outcome_col, group_col)
        result["t_test"] = t_res
        result["effect_size"] = {
            "cohens_d": compute_effect_size_cohen_d(df, outcome_col, group_col),
            "group_col": group_col
        }
    else:
        # One sample t-test if no group
        t_res = run_t_test(df, outcome_col)
        result["t_test"] = t_res
        result["effect_size"] = {"cohens_d": np.nan}
    
    # Regression
    reg_res = run_linear_regression(df, outcome_col)
    result["regression"] = reg_res
    
    return result

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame, Dict[str, Any]],
    output_path: Optional[str] = None,
    config: Optional[Any] = None,
    dataset_name: Optional[str] = None,
    outcome_col: Optional[str] = None
) -> Union[Dict[str, Any], bool]:
    """
    Unified entry point for baseline analysis.
    
    Handles multiple calling signatures:
    1. run_baseline_analysis(raw_dir, output_path, config) -> writes file, returns bool
       (Legacy signature for T012 style)
    2. run_baseline_analysis(df, dataset_name=..., config=...) -> returns dict
       (Signature for T013, T023, T033)
    3. run_baseline_analysis(df_cleaned, dataset_name=...) -> returns dict
    
    Args:
        input_data: Can be a directory path (str), a DataFrame, or a dict (unused in this context but tolerated).
        output_path: Path to write results (only used in signature 1).
        config: Config object (tolerated).
        dataset_name: Name of the dataset (required for signature 2/3).
        outcome_col: Specific outcome column to use.
    
    Returns:
        Dict of results if analyzing a DataFrame, or bool if writing to file.
    """
    # Case 1: Directory path -> Load all datasets, run analysis, write to file
    if isinstance(input_data, str) and os.path.isdir(input_data):
        raw_dir = input_data
        if output_path is None:
            raise ValueError("output_path is required when input_data is a directory.")
        
        datasets = load_datasets_from_raw(raw_dir)
        if not datasets:
            logger.error("No datasets found in raw directory.")
            return False
        
        all_results = []
        for df in datasets:
            # Infer name from filename if possible, else use index
            # Since we loaded from dir, we might not have the filename here easily without passing it.
            # We'll use a generic name or try to extract from index if we tracked it.
            # For now, assume we process each and name them.
            # To be robust, let's assume the caller passed a list or we iterate.
            # Actually, load_datasets_from_raw returns a list of DFs.
            # We need names. Let's assume generic naming for this path or skip.
            # Better: The caller (T012) likely loads specific files.
            # Let's assume the input_data is a single file path for simplicity in this branch?
            # No, the signature says raw_dir.
            # We'll process all and write a combined JSON.
            pass # Logic handled below in loop if we had names.
        
        # Re-implementing logic for directory input:
        # We need to know the dataset names. load_datasets_from_raw doesn't return names.
        # Let's assume the caller (T012) handles this differently or we infer from file list.
        # For this implementation, we'll assume the input_data is a single CSV file path if it's a string.
        # If it's a directory, we might be in a legacy mode.
        # Let's refine: If input_data is a string ending in .csv, treat as single file.
        if input_data.endswith('.csv'):
            try:
                df = pd.read_csv(input_data)
                name = os.path.basename(input_data).replace('.csv', '')
                res = analyze_dataset(df, name, outcome_col)
                if output_path:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(res, f, indent=2)
                    return True
                return res
            except Exception as e:
                logger.error(f"Failed to process file {input_data}: {e}")
                return False
        else:
            # It is a directory.
            # We need to iterate files.
            if not os.path.exists(raw_dir):
                logger.error(f"Directory {raw_dir} not found.")
                return False
            
            results_list = []
            for filename in os.listdir(raw_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(raw_dir, filename)
                    try:
                        df = pd.read_csv(filepath)
                        name = filename.replace('.csv', '')
                        res = analyze_dataset(df, name, outcome_col)
                        results_list.append(res)
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {e}")
            
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(results_list, f, indent=2)
                return True
            return results_list

    # Case 2: DataFrame input -> Return analysis dict
    elif isinstance(input_data, pd.DataFrame):
        df = input_data
        if dataset_name is None:
            dataset_name = "unknown_dataset"
        
        res = analyze_dataset(df, dataset_name, outcome_col)
        return res
    
    # Case 3: Dict or other (tolerated)
    elif isinstance(input_data, dict):
        # Maybe it's a pre-loaded dict with data?
        if 'data' in input_data and 'name' in input_data:
            df = input_data['data']
            name = input_data['name']
            return analyze_dataset(df, name, outcome_col)
        else:
            logger.warning("Received a dict but no 'data' key. Returning empty result.")
            return {}
    
    else:
        logger.error(f"Unsupported input type: {type(input_data)}")
        return {}

def main():
    """CLI entry point for analysis module."""
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis on datasets.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file or directory.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file path.")
    parser.add_argument("--outcome", type=str, default=None, help="Outcome column name.")
    
    args = parser.parse_args()
    
    result = run_baseline_analysis(args.input, args.output, outcome_col=args.outcome)
    if result:
        print(f"Analysis complete. Output written to {args.output}")
    else:
        print("Analysis failed.")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
