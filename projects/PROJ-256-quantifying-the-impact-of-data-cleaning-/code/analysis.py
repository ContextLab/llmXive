import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

logger = logging.getLogger(__name__)

def run_t_test(df: pd.DataFrame, outcome: str, group_col: str = 'group') -> Dict[str, Any]:
    """
    Perform an independent t-test comparing 'outcome' across 'group_col'.
    Returns p-value, 95% CI for difference in means, and Cohen's d.
    """
    if outcome not in df.columns or group_col not in df.columns:
        raise ValueError(f"Columns '{outcome}' or '{group_col}' not found in dataframe")

    groups = df.groupby(group_col)[outcome]
    if groups.ngroups < 2:
        logger.warning(f"Not enough groups to perform t-test (found {groups.ngroups})")
        return {
            "p_value": np.nan,
            "ci": [np.nan, np.nan],
            "effect_size": np.nan,
            "method": "t_test",
            "status": "skipped"
        }

    group_data = [g for _, g in groups]
    if len(group_data) != 2:
        logger.warning(f"Expected exactly 2 groups for t-test, found {len(group_data)}")
        # Fallback to ANOVA if >2 groups, but for now we stick to 2-group logic
        # or return NaN if strictly 2-group expected
        return {
            "p_value": np.nan,
            "ci": [np.nan, np.nan],
            "effect_size": np.nan,
            "method": "t_test",
            "status": "skipped"
        }

    x1, x2 = group_data[0], group_data[1]

    # T-test
    t_stat, p_val = stats.ttest_ind(x1, x2, equal_var=False) # Welch's t-test

    # 95% CI for difference in means
    mean_diff = x1.mean() - x2.mean()
    se_diff = np.sqrt((x1.var(ddof=1)/len(x1)) + (x2.var(ddof=1)/len(x2)))
    df_deg = ((x1.var(ddof=1)/len(x1)) + (x2.var(ddof=1)/len(x2)))**2 / (
        ((x1.var(ddof=1)/len(x1))**2 / (len(x1)-1)) + ((x2.var(ddof=1)/len(x2))**2 / (len(x2)-1))
    )
    t_crit = stats.t.ppf(0.975, df_deg)
    ci_lower = mean_diff - t_crit * se_diff
    ci_upper = mean_diff + t_crit * se_diff

    # Cohen's d (pooled SD)
    n1, n2 = len(x1), len(x2)
    s1_sq, s2_sq = x1.var(ddof=1), x2.var(ddof=1)
    pooled_var = ((n1 - 1) * s1_sq + (n2 - 1) * s2_sq) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    if pooled_std == 0:
        cohens_d = np.nan
    else:
        cohens_d = mean_diff / pooled_std

    return {
        "p_value": float(p_val),
        "ci": [float(ci_lower), float(ci_upper)],
        "effect_size": float(cohens_d),
        "method": "t_test",
        "status": "success",
        "n1": int(n1),
        "n2": int(n2)
    }

def run_linear_regression(df: pd.DataFrame, outcome: str, predictors: List[str]) -> Dict[str, Any]:
    """
    Perform OLS linear regression.
    Returns p-values for coefficients, R-squared, and F-statistic p-value.
    """
    if outcome not in df.columns:
        raise ValueError(f"Outcome column '{outcome}' not found")
    for p in predictors:
        if p not in df.columns:
            raise ValueError(f"Predictor column '{p}' not found")

    # Drop rows with NaN in relevant columns
    clean_df = df.dropna(subset=[outcome] + predictors)
    if len(clean_df) < 2:
        logger.warning("Not enough data points for regression after dropping NaNs")
        return {
            "r_squared": np.nan,
            "f_stat_p_value": np.nan,
            "coefficients": {},
            "method": "ols",
            "status": "skipped"
        }

    y = clean_df[outcome]
    X = clean_df[predictors]
    X = sm.add_constant(X)

    model = ols(f"{outcome} ~ {' + '.join(predictors)}", data=clean_df).fit()

    coef_pvals = {str(k): float(v) for k, v in model.pvalues.items() if k != 'const'}
    const_pval = float(model.pvalues['const']) if 'const' in model.pvalues else np.nan

    return {
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "f_statistic": float(model.fvalue),
        "f_stat_p_value": float(model.f_pvalue),
        "coefficients": {
            "intercept": float(model.params['const']) if 'const' in model.params else np.nan,
            **{str(k): float(v) for k, v in model.params.items() if k != 'const'}
        },
        "p_values": {
            "intercept": const_pval,
            **coef_pvals
        },
        "method": "ols",
        "status": "success",
        "n_obs": int(len(clean_df))
    }

def run_baseline_analysis(
    dataframe: Optional[pd.DataFrame] = None,
    outcome: str = 'outcome',
    predictors: Optional[List[str]] = None,
    group_col: str = 'group',
    raw_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Flexible entry point for baseline analysis.
    Accepts:
      1. dataframe: pre-loaded DataFrame
      2. raw_dir + output_file: path-based loading and saving
      3. dataframe + outcome/predictors: analysis with specific columns
    Returns a dictionary of metrics.
    """
    logger.info(f"Running baseline analysis with args: dataframe={dataframe is not None}, raw_dir={raw_dir}")

    df = dataframe
    if df is None and raw_dir:
        # Load from raw_dir (simplified: assumes CSV or parquet)
        # In a real scenario, this would iterate files or load a specific one
        logger.warning("raw_dir loading not fully implemented in this snippet; assuming dataframe passed or handled externally.")
        # Fallback: if raw_dir is provided but no dataframe, we can't proceed without a loader
        # For T013, we assume the caller ensures data exists or passes dataframe
        raise ValueError("Either 'dataframe' must be provided or 'raw_dir' must point to a loadable file (not implemented here).")

    if df is None:
        raise ValueError("No data provided to run_baseline_analysis")

    if predictors is None:
        predictors = []
        # Auto-detect numeric columns as predictors if not specified?
        # For now, require explicit predictors or just do t-test if group_col exists
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if group_col in df.columns and outcome in df.columns:
            # If we have a group col and outcome, default to t-test
            pass
        elif len(numeric_cols) >= 2:
            # Default to first numeric as outcome, second as predictor?
            # Too ambiguous. Let's require explicit args or at least group_col
            pass

    results = {
        "t_test": None,
        "regression": None,
        "dataset_info": {
            "n_rows": int(len(df)),
            "n_cols": int(len(df.columns)),
            "columns": list(df.columns)
        }
    }

    # Run T-Test if group_col exists
    if group_col in df.columns and outcome in df.columns:
        try:
            results["t_test"] = run_t_test(df, outcome, group_col)
        except Exception as e:
            logger.error(f"T-test failed: {e}")
            results["t_test"] = {"status": "error", "error": str(e)}

    # Run Regression if predictors provided
    if predictors:
        try:
            results["regression"] = run_linear_regression(df, outcome, predictors)
        except Exception as e:
            logger.error(f"Regression failed: {e}")
            results["regression"] = {"status": "error", "error": str(e)}

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Saved baseline metrics to {output_file}")

    return results

def main():
    """
    Entry point for direct execution (e.g., python code/analysis.py)
    This is a stub for T013 context; real orchestration happens in main.py
    """
    logging.basicConfig(level=logging.INFO)
    # Example usage if run directly (requires data)
    # df = pd.read_csv("data/raw/example.csv")
    # run_baseline_analysis(dataframe=df, output_file="data/processed/baseline_metrics.json")
    pass

if __name__ == "__main__":
    main()
