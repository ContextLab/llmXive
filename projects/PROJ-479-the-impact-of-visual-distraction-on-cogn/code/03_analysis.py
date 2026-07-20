import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

# Local imports from utils
from utils import get_logger, set_random_seed, get_global_seed

# Configure logging
logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """
    Load the final analysis dataset.
    Expects: data/processed/final_analysis_data.csv
    """
    path = "data/processed/final_analysis_data.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis data file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded analysis data with {len(df)} rows and {len(df.columns)} columns.")
    return df

def sm_add_constant(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Add a constant term to the feature matrix for statsmodels.
    Returns a new DataFrame with the constant column added as 'const'.
    """
    X = df[features].copy()
    return sm.add_constant(X)

def calculate_correlations(df: pd.DataFrame, predictors: List[str], outcome: str) -> Dict[str, Any]:
    """
    Calculate Pearson correlation and p-value for each predictor against the outcome.
    Returns a dictionary of results.
    """
    results = {}
    for pred in predictors:
        # Filter out NaNs for this specific calculation
        valid_mask = df[pred].notna() & df[outcome].notna()
        if valid_mask.sum() < 2:
            logger.warning(f"Insufficient valid data for {pred} vs {outcome}. Skipping.")
            results[pred] = {"r": np.nan, "p": np.nan, "n": 0}
            continue

        x = df.loc[valid_mask, pred]
        y = df.loc[valid_mask, outcome]

        r, p = stats.pearsonr(x, y)
        results[pred] = {
            "r": float(r),
            "p": float(p),
            "n": int(valid_mask.sum())
        }
    return results

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    Handles NaNs by dropping rows for VIF calculation only.
    """
    # Drop NaNs for VIF calculation
    df_vif = df[features].dropna()
    if len(df_vif) < len(features) + 1:
        logger.warning("Not enough data points to calculate VIF reliably.")
        return {f: np.nan for f in features}

    X = sm.add_constant(df_vif)
    vif_data = {}
    for i, feature in enumerate(features):
        # statsmodels VIF calculation
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = float(vif)
        except Exception as e:
            logger.error(f"VIF calculation failed for {feature}: {e}")
            vif_data[feature] = float('nan')
    return vif_data

def save_vif_report(vif_data: Dict[str, float], path: str = "results/statistics/vif_report.json"):
    """Save VIF report to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(vif_data, f, indent=2)
    logger.info(f"VIF report saved to {path}")

def run_pca(df: pd.DataFrame, features: List[str], n_components: int = 1) -> Tuple[pd.DataFrame, Any]:
    """
    Run PCA on the specified features.
    Returns the DataFrame with the new component column and the PCA object.
    """
    from sklearn.decomposition import PCA
    
    # Drop NaNs for PCA fitting
    df_pca = df[features].dropna()
    if len(df_pca) < 2:
        raise ValueError("Not enough data to run PCA.")
    
    pca = PCA(n_components=n_components)
    components = pca.fit_transform(df_pca)
    
    # Create a Series for the component to merge back
    component_series = pd.Series(components[:, 0], index=df_pca.index, name='pca_component_1')
    
    # Merge back to original df (preserves NaNs where data was missing)
    df_result = df.copy()
    df_result = df_result.join(component_series)
    
    logger.info(f"PCA fitted. Explained variance: {pca.explained_variance_ratio_[0]:.4f}")
    return df_result, pca

def run_regression_with_pca(df: pd.DataFrame, outcome: str, pca_col: str = 'pca_component_1') -> Dict[str, Any]:
    """
    Run linear regression using the PCA component as predictor.
    """
    # Filter valid rows
    mask = df[pca_col].notna() & df[outcome].notna()
    if mask.sum() < 2:
        raise ValueError("Insufficient data for regression with PCA.")
    
    X = df.loc[mask, [pca_col]]
    X = sm.add_constant(X)
    y = df.loc[mask, outcome]
    
    model = sm.OLS(y, X).fit()
    
    return {
        "predictor": pca_col,
        "outcome": outcome,
        "beta": float(model.params[pca_col]),
        "intercept": float(model.params['const']),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "p_value": float(model.pvalues[pca_col]),
        "ci_lower": float(model.conf_int().loc[pca_col, 0]),
        "ci_upper": float(model.conf_int().loc[pca_col, 1])
    }

def run_regression_standard(df: pd.DataFrame, predictor: str, outcome: str) -> Dict[str, Any]:
    """
    Run linear regression for a standard predictor-outcome pair.
    """
    mask = df[predictor].notna() & df[outcome].notna()
    if mask.sum() < 2:
        raise ValueError(f"Insufficient data for regression: {predictor} vs {outcome}.")
    
    X = df.loc[mask, [predictor]]
    X = sm.add_constant(X)
    y = df.loc[mask, outcome]
    
    model = sm.OLS(y, X).fit()
    
    return {
        "predictor": predictor,
        "outcome": outcome,
        "beta": float(model.params[predictor]),
        "intercept": float(model.params['const']),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "p_value": float(model.pvalues[predictor]),
        "ci_lower": float(model.conf_int().loc[predictor, 0]),
        "ci_upper": float(model.conf_int().loc[predictor, 1])
    }

def bootstrap_correlation(df: pd.DataFrame, predictor: str, outcome: str, n_iter: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform bootstrap resampling for correlation confidence intervals.
    """
    set_random_seed(seed)
    mask = df[predictor].notna() & df[outcome].notna()
    data = df.loc[mask, [predictor, outcome]].values
    
    if len(data) < 2:
        return {"ci_lower": np.nan, "ci_upper": np.nan}
    
    boot_r = []
    for _ in range(n_iter):
        idx = np.random.choice(len(data), len(data), replace=True)
        sample = data[idx]
        r, _ = stats.pearsonr(sample[:, 0], sample[:, 1])
        boot_r.append(r)
    
    ci_lower = float(np.percentile(boot_r, 2.5))
    ci_upper = float(np.percentile(boot_r, 97.5))
    
    return {"ci_lower": ci_lower, "ci_upper": ci_upper}

def apply_holm_bonferroni(p_values: List[float], p_names: List[str]) -> Dict[str, List[float]]:
    """
    Apply Holm-Bonferroni correction.
    Returns dict with 'adjusted_p' and 'rejected' (boolean).
    """
    if not p_values:
        return {"adjusted_p": [], "rejected": []}
    
    # multipletests returns (reject, p_corrected, p_raw, alphac_Sidak, alphac_Holm)
    # We want method='holm'
    reject, p_corrected, _, _ = multipletests(p_values, method='holm')
    
    return {
        "adjusted_p": [float(p) for p in p_corrected],
        "rejected": [bool(r) for r in reject]
    }

def save_statistics(stats_data: Dict[str, Any], path: str = "results/statistics/statistics.json"):
    """Save final statistics to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(stats_data, f, indent=2)
    logger.info(f"Statistics saved to {path}")

def save_multiplicity_table(pairs: List[Tuple[str, str]], raw_ps: List[float], adj_ps: List[float], path: str = "results/statistics/multiplicity_table.csv"):
    """Save multiplicity correction table to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = []
    for (pred, out), rp, ap in zip(pairs, raw_ps, adj_ps):
        data.append({
            "test_name": f"{pred}_vs_{out}",
            "raw_p": rp,
            "adjusted_p": ap,
            "metric_pair": f"{pred} - {out}"
        })
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    logger.info(f"Multiplicity table saved to {path}")

def generate_alpha_justification() -> str:
    """Generate the alpha threshold justification text."""
    return """
    ## Alpha Threshold Justification

    The p-value is a measure of the evidence against a null hypothesis. It represents the probability of observing results as extreme as, or more extreme than, those observed, assuming the null hypothesis is true.

    The threshold of p < 0.05 is a widely accepted community standard in psychological and social sciences for determining statistical significance. This threshold balances the risk of Type I errors (false positives) with the need to detect meaningful effects.

    As established by the American Psychological Association: "Wilkinson, L., & Task Force on Statistical Inference. (1999). Statistical methods in psychology journals: Guidelines and explanations. American Psychologist, 54(8), 594–604." This standard provides a consistent benchmark for evaluating research findings across studies.

    While this threshold is conventional, it is not absolute. Researchers must interpret p-values in the context of effect sizes, confidence intervals, and theoretical plausibility. The use of p < 0.05 facilitates comparison across the literature while maintaining a reasonable level of rigor.
    """

def generate_methods_citations() -> str:
    """Generate methods citations text."""
    return """
    ## Methods Citations

    - **OpenCV Edge Detection**: {{claim:c_ad853b44}} (Wikidata Q165277, https://www.wikidata.org/wiki/Q165277)
    - **Color Entropy**: Cover, T. M., & Thomas, J. A. (n.d.). Elements of Information Theory. Wiley-Interscience.
    - **YOLOv5**: Jocher, G. (2020). Ultralytics YOLOv5. https://github.com/ultralytics/yolov5
    """

def run_binning_analysis(df: pd.DataFrame, predictors: List[str], outcome: str, strategies: List[str] = ['quartiles', 'deciles']) -> pd.DataFrame:
    """
    Run correlation analysis with different binning strategies.
    """
    results = []
    for pred in predictors:
        for strategy in strategies:
            # Filter valid data
            mask = df[pred].notna() & df[outcome].notna()
            if mask.sum() < 4:
                continue
            
            x = df.loc[mask, pred]
            y = df.loc[mask, outcome]
            
            if strategy == 'quartiles':
                bins = pd.qcut(x, q=4, duplicates='drop')
            elif strategy == 'deciles':
                bins = pd.qcut(x, q=10, duplicates='drop')
            else:
                continue
            
            # Calculate correlation on binned data (using bin midpoints or just the original values within bins)
            # Here we calculate correlation of the original values within the binned groups to see stability
            # But typically binning analysis checks correlation of bin means or similar.
            # Let's calculate correlation of the original values but grouped by bin to see if the trend holds.
            # Actually, standard binning analysis often calculates correlation on the binned averages.
            # Let's do correlation on the binned averages.
            df_temp = pd.DataFrame({'x': x, 'y': y, 'bin': bins})
            grouped = df_temp.groupby('bin').mean()
            
            if len(grouped) < 2:
                continue
            
            r, p = stats.pearsonr(grouped['x'], grouped['y'])
            results.append({
                'binning_strategy': strategy,
                'predictor': pred,
                'outcome': outcome,
                'pearson_r': float(r),
                'p_value': float(p)
            })
    
    return pd.DataFrame(results)

def save_binning_results(df_results: pd.DataFrame, path: str = "results/sensitivity/binning_results.csv"):
    """Save binning results to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df_results.to_csv(path, index=False)
    logger.info(f"Binning results saved to {path}")

def main():
    """Main execution function for T031 and related analysis tasks."""
    set_random_seed(42)
    logger.info("Starting statistical analysis pipeline...")

    # 1. Load Data
    try:
        df = load_analysis_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    predictors = ['edge_density', 'color_entropy', 'object_count']
    outcome = 'reaction_time'

    # 2. Calculate Correlations (T031)
    logger.info("Calculating Pearson correlations...")
    corr_results = calculate_correlations(df, predictors, outcome)
    
    # 3. Calculate VIF (T032)
    logger.info("Calculating VIF...")
    vif_data = calculate_vif(df, predictors)
    save_vif_report(vif_data)

    # 4. Check VIF and decide on PCA (T034a)
    max_vif = max(vif_data.values()) if vif_data else 0
    use_pca = max_vif >= 5
    logger.info(f"Max VIF: {max_vif:.2f}. Use PCA: {use_pca}")

    # 5. Run PCA if needed (T033)
    final_df = df
    if use_pca:
        logger.info("Running PCA due to high VIF...")
        valid_features = [f for f in predictors if f in df.columns]
        final_df, pca_obj = run_pca(final_df, valid_features)

    # 6. Run Regression (T031, T034b)
    regression_results = []
    if use_pca:
        logger.info("Running regression with PCA component...")
        try:
            reg_res = run_regression_with_pca(final_df, outcome, 'pca_component_1')
            regression_results.append(reg_res)
        except Exception as e:
            logger.error(f"PCA Regression failed: {e}")
    else:
        logger.info("Running standard regressions...")
        for pred in predictors:
            try:
                reg_res = run_regression_standard(final_df, pred, outcome)
                regression_results.append(reg_res)
            except Exception as e:
                logger.warning(f"Regression failed for {pred}: {e}")

    # 7. Bootstrap (T041)
    bootstrap_results = {}
    for pred in predictors:
        if pred in final_df.columns:
            boot = bootstrap_correlation(final_df, pred, outcome)
            bootstrap_results[pred] = boot

    # 8. Multiplicity Correction (T035)
    p_values = [r['p'] for r in regression_results if not np.isnan(r.get('p', np.nan))]
    p_names = [r['predictor'] for r in regression_results if not np.isnan(r.get('p', np.nan))]
    if p_values:
        correction = apply_holm_bonferroni(p_values, p_names)
    else:
        correction = {"adjusted_p": [], "rejected": []}

    # 9. Save Multiplicity Table (T036)
    pairs = [(r['predictor'], r['outcome']) for r in regression_results]
    raw_ps = [r['p_value'] for r in regression_results]
    adj_ps = correction['adjusted_p']
    save_multiplicity_table(pairs, raw_ps, adj_ps)

    # 10. Binning Analysis (T042)
    binning_df = run_binning_analysis(final_df, predictors, outcome)
    save_binning_results(binning_df)

    # 11. Generate Justifications (T037, T037b)
    alpha_just = generate_alpha_justification()
    methods_cit = generate_methods_citations()

    # 12. Assemble Final Statistics (T039b)
    final_stats = {
        "correlations": corr_results,
        "regressions": regression_results,
        "bootstrap": bootstrap_results,
        "holm_bonferroni": correction,
        "vif": vif_data,
        "use_pca": use_pca,
        "justification": alpha_just,
        "citations": methods_cit
    }
    save_statistics(final_stats)

    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()