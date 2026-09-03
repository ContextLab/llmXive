import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import json

# Import config for paths
from config import ensure_directories, get_config_summary

logger = logging.getLogger(__name__)

def check_vif(df: pd.DataFrame, covariates: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for covariates.
    Returns a dict mapping column name to VIF value.
    """
    vif_data = {}
    # Add intercept for VIF calculation
    X = df[covariates].dropna()
    if len(X) == 0:
        return vif_data
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    for col in covariates:
        if col not in X_const.columns:
            continue
        try:
            vif = variance_inflation_factor(X_const.values, list(X_const.columns).index(col))
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    return vif_data

def fit_mixed_effects_model(df: pd.DataFrame, formula: str) -> Any:
    """
    Fit a linear mixed-effects model.
    Returns the fitted model object.
    """
    # Drop rows with NaN in relevant columns
    clean_df = df.dropna(subset=['debt_score', 'total_lines_changed', 'avg_loc'])
    if 'repo_id' in df.columns:
        clean_df = clean_df.dropna(subset=['repo_id'])
    
    if len(clean_df) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for mixed-effects model.")
    
    model = smf.mixedlm(formula, clean_df, groups=clean_df["repo_id"])
    result = model.fit()
    return result

def calculate_partial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Pearson and Spearman partial correlations between total_lines_changed and debt_score,
    controlling for avg_loc.
    """
    # Drop NaNs
    clean_df = df[['total_lines_changed', 'debt_score', 'avg_loc']].dropna()
    if len(clean_df) < 3:
        return {"pearson_r": np.nan, "pearson_p": np.nan, "spearman_r": np.nan, "spearman_p": np.nan}
    
    x = clean_df['total_lines_changed']
    y = clean_df['debt_score']
    z = clean_df['avg_loc']
    
    # Partial correlation function
    def partial_corr(x, y, z):
        # Regress x on z
        res_x = sm.OLS(x, sm.add_constant(z)).fit()
        r_xz = res_x.resid
        
        # Regress y on z
        res_y = sm.OLS(y, sm.add_constant(z)).fit()
        r_yz = res_y.resid
        
        # Correlation of residuals
        r, p = stats.pearsonr(r_xz, r_yz)
        return r, p
    
    try:
        p_r, p_p = partial_corr(x, y, z)
    except Exception as e:
        logger.error(f"Partial correlation calculation failed: {e}")
        p_r, p_p = np.nan, np.nan
        
    # Spearman (approximate partial by rank transformation then partial)
    # Note: True partial Spearman is complex, often approximated by rank-transforming then partial Pearson
    try:
        x_r = x.rank()
        y_r = y.rank()
        z_r = z.rank()
        s_r, s_p = partial_corr(x_r, y_r, z_r)
    except Exception as e:
        logger.error(f"Spearman partial correlation calculation failed: {e}")
        s_r, s_p = np.nan, np.nan
        
    return {
        "pearson_r": p_r,
        "pearson_p": p_p,
        "spearman_r": s_r,
        "spearman_p": s_p
    }

def run_meta_analysis(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform meta-analysis of Fisher-transformed correlation coefficients.
    Input: List of dicts containing 'r' and 'n' (sample size) per repo/study.
    Returns: Aggregate z, p-value, and confidence interval.
    """
    if not results_list:
        return {"aggregate_r": np.nan, "z_score": np.nan, "p_value": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
    
    rs = []
    ns = []
    for item in results_list:
        if 'r' in item and 'n' in item and not np.isnan(item['r']):
            rs.append(item['r'])
            ns.append(item['n'])
    
    if len(rs) == 0:
        return {"aggregate_r": np.nan, "z_score": np.nan, "p_value": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
    
    # Fisher transformation
    # z = 0.5 * ln((1+r)/(1-r))
    # variance = 1 / (n - 3)
    zs = []
    variances = []
    for r, n in zip(rs, ns):
        # Clamp r to (-1, 1) to avoid log domain error
        r_clamped = max(min(r, 0.9999), -0.9999)
        z = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))
        var = 1.0 / (n - 3)
        zs.append(z)
        variances.append(var)
    
    zs = np.array(zs)
    variances = np.array(variances)
    
    # Weighted average
    weights = 1.0 / variances
    z_bar = np.average(zs, weights=weights)
    se_bar = np.sqrt(1.0 / np.sum(weights))
    
    # Test against 0
    z_score = z_bar / se_bar
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # 95% CI in z-space
    z_lower = z_bar - 1.96 * se_bar
    z_upper = z_bar + 1.96 * se_bar
    
    # Back-transform to r
    r_bar = (np.exp(2 * z_bar) - 1) / (np.exp(2 * z_bar) + 1)
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return {
        "aggregate_r": r_bar,
        "z_score": z_score,
        "p_value": p_value,
        "ci_lower": r_lower,
        "ci_upper": r_upper,
        "n_studies": len(rs)
    }

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: List[int]) -> pd.DataFrame:
    """
    Run sensitivity analysis by filtering data with different avg_loc thresholds.
    Returns a DataFrame of results.
    """
    results = []
    for thresh in thresholds:
        filtered_df = df[df['avg_loc'] >= thresh]
        if len(filtered_df) < 3:
            results.append({
                "threshold": thresh,
                "n_samples": len(filtered_df),
                "pearson_r": np.nan,
                "pearson_p": np.nan,
                "spearman_r": np.nan,
                "spearman_p": np.nan
            })
            continue
        
        corr_res = calculate_partial_correlations(filtered_df)
        results.append({
            "threshold": thresh,
            "n_samples": len(filtered_df),
            "pearson_r": corr_res['pearson_r'],
            "pearson_p": corr_res['pearson_p'],
            "spearman_r": corr_res['spearman_r'],
            "spearman_p": corr_res['spearman_p']
        })
    
    return pd.DataFrame(results)

def run_analysis(input_path: Path, output_dir: Path, thresholds: List[int] = [5, 10, 20]) -> None:
    """
    Main analysis runner:
    1. Load unified_metrics.csv
    2. Check VIF, fit mixed effects, calculate partial correlations
    3. Run meta-analysis
    4. Run sensitivity analysis
    5. Save results to CSVs
    """
    ensure_directories([output_dir])
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure numeric types
    numeric_cols = ['total_lines_changed', 'debt_score', 'avg_loc', 'contributor_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 1. VIF Check
    covariates = ['avg_loc', 'contributor_count'] # project_age and language need handling if present
    # If 'project_age' exists, add it. If 'language' exists, we might need dummy vars, skipping for simplicity unless present as numeric
    if 'project_age' in df.columns:
        covariates.append('project_age')
    
    vif_results = check_vif(df, covariates)
    logger.info(f"VIF Results: {vif_results}")
    
    # 2. Mixed Effects Model
    formula = "debt_score ~ total_lines_changed + avg_loc + contributor_count"
    if 'project_age' in df.columns:
        formula += " + project_age"
    # Add repo_id grouping
    
    mixed_results = {}
    try:
        model = fit_mixed_effects_model(df, formula)
        mixed_results = {
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "aic": model.aic,
            "bic": model.bic
        }
        logger.info("Mixed-effects model fitted successfully.")
    except Exception as e:
        logger.error(f"Failed to fit mixed-effects model: {e}")
        mixed_results = {"error": str(e)}
    
    # 3. Partial Correlations (Global)
    partial_corr_res = calculate_partial_correlations(df)
    
    # 4. Meta-analysis
    # We need per-repo correlations for meta-analysis. 
    # Group by repo_id, calculate r and n for each.
    meta_input = []
    if 'repo_id' in df.columns:
        grouped = df.groupby('repo_id')
        for repo, group in grouped:
            if len(group) < 3: continue
            c = calculate_partial_correlations(group)
            if not np.isnan(c['pearson_r']):
                meta_input.append({
                    "r": c['pearson_r'],
                    "n": len(group)
                })
    else:
        # If no repo_id, treat whole dataset as one study? Or fail?
        # Assuming repo_id exists as per T015 spec
        logger.warning("No repo_id found, skipping meta-analysis grouping.")
    
    meta_res = run_meta_analysis(meta_input)
    
    # 5. Sensitivity Analysis
    sens_res = run_sensitivity_analysis(df, thresholds)
    
    # Save Results
    # A. Correlation Results
    corr_results_df = pd.DataFrame([{
        "metric": "pearson_r",
        "value": partial_corr_res['pearson_r']
    }, {
        "metric": "pearson_p",
        "value": partial_corr_res['pearson_p']
    }, {
        "metric": "spearman_r",
        "value": partial_corr_res['spearman_r']
    }, {
        "metric": "spearman_p",
        "value": partial_corr_res['spearman_p']
    }])
    corr_results_df.to_csv(output_dir / "correlation_results.csv", index=False)
    
    # B. Sensitivity Analysis
    sens_res.to_csv(output_dir / "sensitivity_analysis.csv", index=False)
    
    # C. Meta Analysis
    meta_df = pd.DataFrame([meta_res])
    meta_df.to_csv(output_dir / "meta_analysis_results.csv", index=False)
    
    logger.info(f"Analysis complete. Results saved to {output_dir}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis on unified metrics.")
    parser.add_argument("--input", type=str, default="data/processed/unified_metrics.csv", help="Path to input CSV")
    parser.add_argument("--output", type=str, default="data/results", help="Output directory")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    run_analysis(input_path, output_path)

if __name__ == "__main__":
    main()