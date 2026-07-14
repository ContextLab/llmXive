import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from utils import pin_random_seed, setup_logging
from config import Config, get_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Core Statistical Functions
# ---------------------------------------------------------------------

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[pd.DataFrame, str]]:
    """
    Load all CSV files from the raw directory.
    Returns a list of tuples: (DataFrame, dataset_name_without_extension).
    """
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist. Returning empty list.")
        return []

    datasets = []
    for filename in os.listdir(raw_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                name = os.path.splitext(filename)[0]
                datasets.append((df, name))
                logger.info(f"Loaded dataset: {name} with shape {df.shape}")
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")
    return datasets

def run_t_test(df: pd.DataFrame, outcome_col: str, group_col: str) -> Dict[str, Any]:
    """
    Perform an independent samples t-test.
    Returns dict with p-value, CI, and effect size (Cohen's d).
    """
    if outcome_col not in df.columns or group_col not in df.columns:
        logger.warning(f"Columns {outcome_col} or {group_col} not found. Skipping t-test.")
        return {
            "p_value": None,
            "ci_low": None,
            "ci_high": None,
            "effect_size": None,
            "n1": 0,
            "n2": 0
        }

    # Drop rows with missing values in relevant columns
    clean_df = df[[outcome_col, group_col]].dropna()
    if len(clean_df) < 2:
        logger.warning("Not enough data for t-test.")
        return {
            "p_value": None,
            "ci_low": None,
            "ci_high": None,
            "effect_size": None,
            "n1": 0,
            "n2": 0
        }

    groups = clean_df[group_col].unique()
    if len(groups) != 2:
        logger.warning(f"Expected 2 groups, found {len(groups)}. Skipping t-test.")
        return {
            "p_value": None,
            "ci_low": None,
            "ci_high": None,
            "effect_size": None,
            "n1": 0,
            "n2": 0
        }

    g1 = clean_df[clean_df[group_col] == groups[0]][outcome_col]
    g2 = clean_df[clean_df[group_col] == groups[1]][outcome_col]

    if len(g1) < 2 or len(g2) < 2:
        logger.warning("One group has insufficient data for t-test.")
        return {
            "p_value": None,
            "ci_low": None,
            "ci_high": None,
            "effect_size": None,
            "n1": len(g1),
            "n2": len(g2)
        }

    # T-test
    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False) # Welch's t-test

    # Confidence Interval for difference in means
    mean_diff = g1.mean() - g2.mean()
    # Pooled standard error approximation for CI
    se = np.sqrt((g1.var() / len(g1)) + (g2.var() / len(g2)))
    ci_low = mean_diff - 1.96 * se
    ci_high = mean_diff + 1.96 * se

    # Cohen's d
    # Pooled standard deviation
    n1, n2 = len(g1), len(g2)
    pooled_std = np.sqrt(((n1 - 1) * g1.var() + (n2 - 1) * g2.var()) / (n1 + n2 - 2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / pooled_std

    # Validation
    if not (0 < p_val < 1):
        logger.warning(f"Invalid p-value {p_val} for {outcome_col}. Clamping.")
        p_val = max(0.0, min(1.0, p_val))

    return {
        "p_value": float(p_val),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "effect_size": float(cohens_d),
        "n1": int(n1),
        "n2": int(n2)
    }

def run_linear_regression(df: pd.DataFrame, outcome_col: str, feature_cols: List[str]) -> Dict[str, Any]:
    """
    Perform linear regression.
    Returns dict with p-values for coefficients, R-squared, and CI for coefficients.
    """
    if outcome_col not in df.columns:
        logger.warning(f"Outcome column {outcome_col} not found.")
        return {
            "r_squared": None,
            "coefficients": [],
            "p_values": [],
            "ci_bounds": []
        }

    # Filter valid features
    valid_features = [c for c in feature_cols if c in df.columns]
    if not valid_features:
        logger.warning("No valid feature columns found.")
        return {
            "r_squared": None,
            "coefficients": [],
            "p_values": [],
            "ci_bounds": []
        }

    # Drop NaNs
    subset_cols = [outcome_col] + valid_features
    clean_df = df[subset_cols].dropna()

    if len(clean_df) < 5:
        logger.warning("Insufficient data for regression.")
        return {
            "r_squared": None,
            "coefficients": [],
            "p_values": [],
            "ci_bounds": []
        }

    X = clean_df[valid_features]
    y = clean_df[outcome_col]

    # Add intercept
    X_sm = sm.add_constant(X)
    model = sm.OLS(y, X_sm).fit()

    coefs = []
    p_vals = []
    ci_bounds = []
    r_sq = model.rsquared

    for i, name in enumerate(X_sm.columns):
        coef = model.params[name]
        p_val = model.pvalues[name]
        ci = model.conf_int().loc[name]
        
        # Validation
        if not (0 < p_val < 1):
            p_val = max(0.0, min(1.0, p_val))

        coefs.append(float(coef))
        p_vals.append(float(p_val))
        ci_bounds.append([float(ci[0]), float(ci[1])])

    return {
        "r_squared": float(r_sq),
        "coefficients": coefs,
        "p_values": p_vals,
        "ci_bounds": ci_bounds,
        "feature_names": valid_features
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Compute Cohen's d effect size.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(), group2.var()
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def analyze_dataset(df: pd.DataFrame, dataset_name: str, outcome_col: str = "outcome", group_col: str = "group", feature_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run all analyses on a single dataset.
    """
    if feature_cols is None:
        # Heuristic: all numeric columns except outcome and group
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c not in [outcome_col, group_col]]

    results = {
        "dataset_name": dataset_name,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "t_test": None,
        "regression": None
    }

    # T-test
    t_res = run_t_test(df, outcome_col, group_col)
    if t_res["p_value"] is not None:
        results["t_test"] = t_res

    # Regression
    reg_res = run_linear_regression(df, outcome_col, feature_cols)
    if reg_res["r_squared"] is not None:
        results["regression"] = reg_res

    return results

def run_baseline_analysis(*args, **kwargs) -> Union[bool, Dict[str, Any]]:
    """
    Flexible entry point for baseline analysis.
    
    Signatures supported:
    1. run_baseline_analysis(raw_dir, output_path, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=...) -> returns dict (for re-analysis)
    3. run_baseline_analysis(raw_dir, output_path) -> writes file, returns bool
    4. run_baseline_analysis(df, dataset_name=...) -> returns dict
    
    This function handles the routing logic to ensure compatibility with all callers.
    """
    logger.debug(f"run_baseline_analysis called with args={args}, kwargs={kwargs}")

    # Case 1 & 3: Directory-based analysis (writing to file)
    # Expected: (raw_dir, output_path) or (raw_dir, output_path, config) or (raw_dir, output_path=output_path)
    if len(args) >= 2 or 'raw_dir' in kwargs:
        raw_dir = args[0] if len(args) > 0 else kwargs.get('raw_dir')
        output_path = args[1] if len(args) > 1 else kwargs.get('output_path')
        
        # Config is optional in this path
        config = None
        if len(args) > 2:
            config = args[2]
        elif 'config' in kwargs:
            config = kwargs.get('config')
        
        if not raw_dir or not output_path:
            logger.error("run_baseline_analysis: raw_dir and output_path are required for directory mode.")
            return False

        logger.info(f"Running baseline analysis on {raw_dir}, output to {output_path}")
        datasets = load_datasets_from_raw(raw_dir)
        
        if not datasets:
            logger.warning("No datasets found. Writing empty report.")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump({"datasets": [], "metadata": {"source": raw_dir}}, f, indent=2)
            return True

        all_results = []
        for df, name in datasets:
            try:
                res = analyze_dataset(df, name)
                all_results.append(res)
            except Exception as e:
                logger.error(f"Error analyzing {name}: {e}")
                continue

        report = {
            "datasets": all_results,
            "metadata": {
                "source": raw_dir,
                "timestamp": str(pd.Timestamp.now())
            }
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Baseline analysis complete. Wrote {len(all_results)} datasets to {output_path}")
        return True

    # Case 2 & 4: DataFrame-based analysis (returning dict)
    # Expected: (df, dataset_name=..., config=...) or (df, dataset_name=...)
    if len(args) >= 1 and isinstance(args[0], pd.DataFrame):
        df = args[0]
        dataset_name = kwargs.get('dataset_name', 'unknown')
        
        res = analyze_dataset(df, dataset_name)
        return res

    logger.error("run_baseline_analysis: Could not determine execution mode from arguments.")
    return False

def main():
    """
    CLI entry point for standalone execution of baseline analysis.
    Usage: python code/analysis.py <raw_dir> <output_path>
    """
    setup_logging("INFO")
    
    if len(sys.argv) < 3:
        logger.error("Usage: python code/analysis.py <raw_dir> <output_path>")
        sys.exit(1)
    
    raw_dir = sys.argv[1]
    output_path = sys.argv[2]
    
    success = run_baseline_analysis(raw_dir, output_path)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
