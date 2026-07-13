import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.weightstats import ttest_ind

logger = logging.getLogger(__name__)

def run_t_test(df: pd.DataFrame, group_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Perform an independent samples t-test between groups defined by group_col
    on the outcome_col.
    
    Returns:
        Dict with keys: 'statistic', 'pvalue', 'p_value', 'ci_lower', 'ci_upper', 'effect_size', 'n1', 'n2'
    """
    groups = df[group_col].unique()
    if len(groups) != 2:
        raise ValueError(f"t-test requires exactly 2 groups, found {len(groups)}: {groups}")
    
    group1_name, group2_name = groups[0], groups[1]
    g1 = df[df[group_col] == group1_name][outcome_col].dropna()
    g2 = df[df[group_col] == group2_name][outcome_col].dropna()
    
    if len(g1) < 2 or len(g2) < 2:
        raise ValueError("Not enough data points in both groups for t-test.")
    
    # Use Welch's t-test (equal_var=False) as it's more robust
    stat, pval = ttest_ind(g1, g2, equal_var=False)
    
    # Calculate 95% CI for the difference in means
    # statsmodels ttest_ind returns (t-statistic, p-value, degrees_of_freedom)
    # We need to calculate CI manually or use statsmodels's return
    # ttest_ind from statsmodels.stats.weightstats returns (t_stat, p_value, df)
    # We can use the return values to construct CI
    # Actually, ttest_ind from statsmodels doesn't directly return CI in the tuple like scipy
    # Let's use the return from statsmodels.stats.weightstats.ttest_ind which is (t-statistic, p-value, df)
    # To get CI, we can use the DescriptiveStatistics or manually calculate
    
    # Manual calculation for CI of difference in means
    mean1, mean2 = g1.mean(), g2.mean()
    diff = mean1 - mean2
    var1, var2 = g1.var(ddof=1), g2.var(ddof=1)
    n1, n2 = len(g1), len(g2)
    
    se_diff = np.sqrt(var1/n1 + var2/n2)
    # Approximate degrees of freedom (Welch-Satterthwaite)
    df_approx = (var1/n1 + var2/n2)**2 / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))
    t_crit = stats.t.ppf(0.975, df_approx)
    
    ci_lower = diff - t_crit * se_diff
    ci_upper = diff + t_crit * se_diff
    
    # Cohen's d
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = diff / pooled_std
    
    # Validate p-value
    if not (0 < pval < 1):
        logger.warning(f"Invalid p-value {pval} for t-test. Clamping or flagging.")
        # We don't clamp, we just log. The caller should handle if strictly required.
    
    # Validate CI bounds are finite
    if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
        logger.warning(f"Non-finite CI bounds for t-test: [{ci_lower}, {ci_upper}]")
    
    return {
        "statistic": float(stat),
        "pvalue": float(pval),
        "p_value": float(pval), # Alias for consistency
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "effect_size": float(cohens_d),
        "n1": int(n1),
        "n2": int(n2),
        "group1": group1_name,
        "group2": group2_name,
        "method": "independent_t_test_welch"
    }

def run_linear_regression(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Perform a simple linear regression of outcome_col on predictor_col.
    
    Returns:
        Dict with keys: 'r_squared', 'p_value', 'ci_lower', 'ci_upper', 'coefficient', 'intercept', 'n'
    """
    X = df[predictor_col].dropna()
    y = df[outcome_col].dropna()
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(X) < 3:
        raise ValueError("Not enough data points for linear regression.")
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    # Extract results
    coef = model.params[1]
    intercept = model.params[0]
    r_squared = model.rsquared
    p_value = model.pvalues[1]
    conf_int = model.conf_int(alpha=0.05)
    ci_lower = conf_int.iloc[1, 0]
    ci_upper = conf_int.iloc[1, 1]
    n = len(X)
    
    # Validate p-value
    if not (0 < p_value < 1):
        logger.warning(f"Invalid p-value {p_value} for linear regression.")
    
    # Validate CI bounds
    if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
        logger.warning(f"Non-finite CI bounds for regression coefficient: [{ci_lower}, {ci_upper}]")
    
    return {
        "r_squared": float(r_squared),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "coefficient": float(coef),
        "intercept": float(intercept),
        "n": int(n),
        "predictor": predictor_col,
        "outcome": outcome_col,
        "method": "ols_linear_regression"
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    """
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def analyze_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all baseline analyses (t-test and linear regression) on a dataset.
    
    Args:
        df: The dataset DataFrame.
        config: Configuration dict with 'group_col', 'outcome_col', 'predictor_col'.
    
    Returns:
        Dict containing results of t-test and linear regression.
    """
    results = {
        "t_test": None,
        "linear_regression": None,
        "dataset_info": {
            "rows": len(df),
            "columns": list(df.columns),
            "missing_counts": df.isnull().sum().to_dict()
        }
    }
    
    try:
        group_col = config.get('group_col')
        outcome_col = config.get('outcome_col')
        predictor_col = config.get('predictor_col')
        
        if group_col and outcome_col:
            logger.info(f"Running t-test on {outcome_col} by {group_col}")
            results["t_test"] = run_t_test(df, group_col, outcome_col)
        
        if predictor_col and outcome_col:
            logger.info(f"Running linear regression of {outcome_col} on {predictor_col}")
            results["linear_regression"] = run_linear_regression(df, predictor_col, outcome_col)
            
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results

def run_baseline_analysis(df: pd.DataFrame, config: Dict[str, Any], output_path: str) -> None:
    """
    Orchestrates the baseline analysis and writes results to a JSON file.
    
    Args:
        df: The dataset DataFrame.
        config: Configuration dict for analysis columns.
        output_path: Path to write the baseline_metrics.json file.
    """
    logger.info(f"Starting baseline analysis for dataset with {len(df)} rows")
    
    analysis_results = analyze_dataset(df, config)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Baseline metrics written to {output_path}")
    
    # Validation check
    if analysis_results.get("t_test"):
        p_val = analysis_results["t_test"].get("pvalue")
        if p_val is not None and not (0 < p_val < 1):
            logger.warning(f"Validation: T-test p-value {p_val} is not in (0, 1)")
        ci_l = analysis_results["t_test"].get("ci_lower")
        ci_u = analysis_results["t_test"].get("ci_upper")
        if not (np.isfinite(ci_l) and np.isfinite(ci_u)):
            logger.warning(f"Validation: T-test CI bounds are not finite")
            
    if analysis_results.get("linear_regression"):
        p_val = analysis_results["linear_regression"].get("p_value")
        if p_val is not None and not (0 < p_val < 1):
            logger.warning(f"Validation: Regression p-value {p_val} is not in (0, 1)")
        ci_l = analysis_results["linear_regression"].get("ci_lower")
        ci_u = analysis_results["linear_regression"].get("ci_upper")
        if not (np.isfinite(ci_l) and np.isfinite(ci_u)):
            logger.warning(f"Validation: Regression CI bounds are not finite")

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    Helper to load datasets from a raw directory.
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
        
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                datasets.append((filename, df))
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def main():
    """
    Entry point for baseline analysis script.
    Expects environment variables or arguments to define input/output.
    For T012, we assume the script is called with specific paths or uses defaults.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run baseline analysis on a dataset.")
    parser.add_argument("--input", type=str, help="Path to input CSV file")
    parser.add_argument("--output", type=str, default="data/processed/baseline_metrics.json", help="Path to output JSON file")
    parser.add_argument("--group", type=str, default="group_col", help="Name of group column")
    parser.add_argument("--outcome", type=str, default="outcome_col", help="Name of outcome column")
    parser.add_argument("--predictor", type=str, default="predictor_col", help="Name of predictor column")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if not args.input:
        logger.error("Input file path is required.")
        return
        
    if not os.path.exists(args.input):
        logger.error(f"Input file {args.input} not found.")
        return
        
    df = pd.read_csv(args.input)
    
    config = {
        "group_col": args.group,
        "outcome_col": args.outcome,
        "predictor_col": args.predictor
    }
    
    run_baseline_analysis(df, config, args.output)

if __name__ == "__main__":
    main()
