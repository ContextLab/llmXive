import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests

from utils.logging_utils import get_logger
from config import get_output_dir, get_cutoff_date

logger = get_logger(__name__)

def load_metric_data() -> pd.DataFrame:
    """
    Load the aggregated module metrics from the results directory.
    Expects a file like 'data/results/module_metrics.csv' containing:
    repo, module, gini, gini_sq, size_kloc, age_months, bug_density
    """
    output_dir = get_output_dir()
    metrics_path = Path(output_dir) / "results" / "module_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Expected metrics file not found at {metrics_path}. "
                                "Please ensure T024 and T026 have completed successfully.")
    
    df = pd.read_csv(metrics_path)
    
    # Ensure numeric types
    numeric_cols = ['gini', 'gini_sq', 'size_kloc', 'age_months', 'bug_density']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where critical analysis columns are NaN
    df = df.dropna(subset=['gini', 'bug_density'])
    
    logger.info(f"Loaded {len(df)} valid module records for analysis.")
    return df

def calculate_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation and p-value between two columns.
    """
    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Align indices if they differ after dropna (though usually same df)
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(x) < 2:
        logger.warning(f"Insufficient data for correlation between {x_col} and {y_col}.")
        return 0.0, 1.0
    
    corr, p_value = stats.spearmanr(x, y)
    return corr, p_value

def calculate_correlation_confidence_interval(corr: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for correlation coefficient using Fisher transformation.
    """
    if n <= 3:
        return -1.0, 1.0
    
    z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
    se = 1 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    z_low = z - z_crit * se
    z_high = z + z_crit * se
    
    ci_low = (np.exp(2 * z_low) - 1) / (np.exp(2 * z_low) + 1)
    ci_high = (np.exp(2 * z_high) - 1) / (np.exp(2 * z_high) + 1)
    
    return ci_low, ci_high

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for predictors.
    Predictors: Gini, Gini², Size, Age.
    """
    predictors = ['gini', 'gini_sq', 'size_kloc', 'age_months']
    # Filter to only available columns
    available_preds = [p for p in predictors if p in df.columns]
    
    if len(available_preds) < 2:
        logger.warning("Not enough predictors for VIF calculation.")
        return pd.DataFrame()
    
    # Prepare data for VIF (drop NaNs in any predictor)
    vif_df = df[available_preds].dropna()
    
    if len(vif_df) < 2:
        logger.warning("Insufficient data for VIF calculation.")
        return pd.DataFrame()
    
    vif_data = []
    for i, col in enumerate(available_preds):
        vif_val = variance_inflation_factor(vif_df.values, i)
        vif_data.append({
            'predictor': col,
            'vif': vif_val,
            'infinite': np.isinf(vif_val),
            'high_collinearity': vif_val >= 5
        })
    
    return pd.DataFrame(vif_data)

def test_non_linearity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Test for non-linearity by comparing linear vs quadratic models.
    Model 1: bug_density ~ gini + size_kloc + age_months
    Model 2: bug_density ~ gini + gini_sq + size_kloc + age_months
    
    Returns:
        Dictionary with LRT p-value and t-test p-value for Gini².
    """
    if 'gini_sq' not in df.columns:
        logger.warning("Gini² column not found. Skipping non-linearity test.")
        return {'lrt_p_value': None, 'gini_sq_t_p_value': None}
    
    # Drop rows with NaNs in any relevant column
    model_df = df[['bug_density', 'gini', 'gini_sq', 'size_kloc', 'age_months']].dropna()
    
    if len(model_df) < 10:
        logger.warning("Insufficient data for non-linearity test.")
        return {'lrt_p_value': None, 'gini_sq_t_p_value': None}
    
    try:
        # Linear Model
        formula_lin = "bug_density ~ gini + size_kloc + age_months"
        model_lin = ols(formula_lin, data=model_df).fit()
        
        # Quadratic Model
        formula_quad = "bug_density ~ gini + gini_sq + size_kloc + age_months"
        model_quad = ols(formula_quad, data=model_df).fit()
        
        # Likelihood Ratio Test
        # LRT statistic = 2 * (logLik_quad - logLik_lin)
        # Note: OLS logLik is available in results
        lrt_stat = 2 * (model_quad.llf - model_lin.llf)
        # Degrees of freedom difference is 1 (added gini_sq)
        lrt_p_value = 1 - stats.chi2.cdf(lrt_stat, 1)
        
        # T-test for Gini² coefficient
        # Get the p-value for the 'gini_sq' term from the quadratic model summary
        # params order might vary, safer to access by name if possible or by index
        # Using pvalues dict from results
        gini_sq_pval = model_quad.pvalues.get('gini_sq')
        
        return {
            'lrt_p_value': lrt_p_value,
            'gini_sq_t_p_value': gini_sq_pval,
            'linear_aic': model_lin.aic,
            'quadratic_aic': model_quad.aic
        }
        
    except Exception as e:
        logger.error(f"Error during non-linearity test: {e}")
        return {'lrt_p_value': None, 'gini_sq_t_p_value': None, 'error': str(e)}

def apply_multiple_comparison_correction(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply multiple comparison correction (Bonferroni or Benjamini-Hochberg).
    """
    if not p_values:
        return []
    
    # Ensure valid p-values (0 to 1)
    p_values = [max(0.0, min(1.0, p)) for p in p_values]
    
    _, corrected, _, _ = multipletests(p_values, alpha=0.05, method=method)
    # multipletests returns (reject, pvals_corrected, ...). We want corrected p-values.
    # Actually, the function returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    # Let's re-call to get corrected p-values specifically
    _, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method=method)
    
    return pvals_corrected

def perform_sensitivity_analysis_pvalue(df: pd.DataFrame, output_path: Path):
    """
    Perform p-value sensitivity analysis.
    Sweep Set: {0.01, 0.05, 0.1}
    Output: CSV with columns: cutoff, count_significant, count_total
    """
    cutoffs = [0.01, 0.05, 0.1]
    results = []
    
    # We need a set of p-values to sweep. 
    # Assuming we have correlations calculated or we calculate them on the fly?
    # The task description implies we are sweeping the significance threshold for existing tests.
    # However, typically sensitivity analysis on p-values in this context means:
    # "How many correlations are significant at different alpha levels?"
    # But we only have ONE correlation (Gini vs Bug Density) per repo or aggregate?
    # Looking at T027/T028, we calculate correlation.
    # If we have a list of correlations (e.g. per repo), we can count how many are significant.
    # If we have only one aggregate correlation, the count is binary (1 or 0).
    # Given the output format "count_significant", it implies multiple tests (e.g. per repo).
    
    # Let's assume we calculate correlation per repo.
    # We need a column 'repo' in df.
    if 'repo' not in df.columns:
        logger.warning("No 'repo' column found. Cannot perform per-repo sensitivity analysis.")
        # Fallback: if single aggregate, just report the one p-value
        # But the output format suggests aggregation.
        # Let's try to group by repo if possible, otherwise treat as single test.
        pass

    # Strategy: If 'repo' exists, group by repo, calculate correlation, get p-value.
    # Then sweep thresholds.
    # If 'repo' does not exist, we might have a single global correlation.
    # In that case, for each cutoff, count_significant is 1 if p < cutoff else 0. count_total is 1.
    
    p_values_list = []
    
    if 'repo' in df.columns:
        # Calculate correlation per repo
        for repo, group in df.groupby('repo'):
            if len(group) < 3:
                continue
            try:
                _, p_val = calculate_spearman_correlation(group, 'gini', 'bug_density')
                p_values_list.append(p_val)
            except:
                continue
    else:
        # Global correlation
        _, p_val = calculate_spearman_correlation(df, 'gini', 'bug_density')
        p_values_list.append(p_val)
    
    if not p_values_list:
        logger.warning("No p-values generated for sensitivity analysis.")
        # Write empty or header only?
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['cutoff', 'count_significant', 'count_total'])
        return

    for cutoff in cutoffs:
        count_sig = sum(1 for p in p_values_list if p < cutoff)
        count_total = len(p_values_list)
        results.append({
            'cutoff': cutoff,
            'count_significant': count_sig,
            'count_total': count_total
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['cutoff', 'count_significant', 'count_total'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"P-value sensitivity analysis written to {output_path}")

def perform_sensitivity_analysis_rho(df: pd.DataFrame, output_path: Path):
    """
    Perform correlation magnitude sensitivity analysis.
    Sweep Set: {0.2, 0.3, 0.4} as defined in SC-011.
    Output: CSV with columns: cutoff, count_significant, count_total.
    
    Logic:
    1. Calculate Spearman correlation (rho) for each unit of analysis (e.g., per repo).
    2. For each cutoff in {0.2, 0.3, 0.4}, count how many correlations have |rho| >= cutoff.
    """
    cutoffs = [0.2, 0.3, 0.4]
    results = []
    
    # Identify the unit of analysis.
    # If 'repo' column exists, we calculate per repo.
    # Otherwise, we treat the whole dataset as one unit (count_total=1).
    
    rho_values = []
    
    if 'repo' in df.columns:
        for repo, group in df.groupby('repo'):
            if len(group) < 3:
                continue
            try:
                rho, _ = calculate_spearman_correlation(group, 'gini', 'bug_density')
                rho_values.append(rho)
            except Exception as e:
                logger.debug(f"Could not calculate correlation for repo {repo}: {e}")
    else:
        # Single aggregate correlation
        try:
            rho, _ = calculate_spearman_correlation(df, 'gini', 'bug_density')
            rho_values.append(rho)
        except Exception as e:
            logger.error(f"Could not calculate aggregate correlation: {e}")
    
    if not rho_values:
        logger.warning("No correlation values generated for sensitivity analysis.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['cutoff', 'count_significant', 'count_total'])
        return

    for cutoff in cutoffs:
        # Count significant if |rho| >= cutoff
        count_sig = sum(1 for r in rho_values if abs(r) >= cutoff)
        count_total = len(rho_values)
        results.append({
            'cutoff': cutoff,
            'count_significant': count_sig,
            'count_total': count_total
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['cutoff', 'count_significant', 'count_total'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Correlation magnitude sensitivity analysis written to {output_path}")

def run_full_analysis():
    """
    Orchestrates the full statistical analysis pipeline.
    """
    output_dir = get_output_dir()
    results_path = Path(output_dir) / "results"
    results_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting full statistical analysis...")
    
    # Load Data
    df = load_metric_data()
    
    # 1. Spearman Correlation
    corr, p_val = calculate_spearman_correlation(df, 'gini', 'bug_density')
    ci_low, ci_high = calculate_correlation_confidence_interval(corr, len(df))
    logger.info(f"Spearman Correlation (Gini vs Bug Density): {corr:.4f} (p={p_val:.4f}, 95% CI [{ci_low:.4f}, {ci_high:.4f}])")
    
    # 2. VIF
    vif_df = calculate_vif(df)
    if not vif_df.empty:
        logger.info("VIF Results:")
        for _, row in vif_df.iterrows():
            logger.info(f"  {row['predictor']}: VIF={row['vif']:.2f} {'(High Collinearity)' if row['high_collinearity'] else ''}")
    
    # 3. Non-linearity
    nl_results = test_non_linearity(df)
    if nl_results.get('gini_sq_t_p_value') is not None:
        logger.info(f"Non-linearity (Gini² t-test p-value): {nl_results['gini_sq_t_p_value']:.4f}")
    
    # 4. Sensitivity Analysis (P-value) - T032
    pval_sens_path = results_path / "sensitivity_pvalue.csv"
    perform_sensitivity_analysis_pvalue(df, pval_sens_path)
    
    # 5. Sensitivity Analysis (Rho magnitude) - T033
    rho_sens_path = results_path / "sensitivity_rho.csv"
    perform_sensitivity_analysis_rho(df, rho_sens_path)
    
    # 6. Save summary
    summary = {
        "correlation": {
            "rho": corr,
            "p_value": p_val,
            "ci_95": [ci_low, ci_high]
        },
        "vif": vif_df.to_dict(orient='records') if not vif_df.empty else [],
        "non_linearity": nl_results,
        "sensitivity_files": {
            "p_value": str(pval_sens_path),
            "rho": str(rho_sens_path)
        }
    }
    
    summary_path = results_path / "analysis_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis complete. Summary saved to {summary_path}")
    return summary

def main():
    """
    Entry point for the statistical analysis script.
    """
    try:
        run_full_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
