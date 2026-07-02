import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats

# Local imports based on API surface
# Note: Assuming data models are accessible via relative import or sys.path setup
# as per project structure conventions
try:
    from config import get_data_root, ensure_directories
except ImportError:
    # Fallback for direct execution or different path setup
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_data_root, ensure_directories

from utils.logger import get_logger, log_exception

# Setup logger
logger = get_logger(__name__)

def load_metrics_data(metrics_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the combined metrics dataframe from the store.
    Expected columns include structural metrics and avalanche exponents.
    """
    if metrics_path is None:
        data_root = get_data_root()
        metrics_path = data_root / "results" / "participant_metrics.csv"
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded metrics data for {len(df)} participants from {metrics_path}")
    return df

def compute_spearman_correlations(df: pd.DataFrame, 
                                  structural_cols: List[str], 
                                  avalanche_col: str) -> Dict[str, Dict[str, float]]:
    """
    Computes Spearman rank correlation between structural metrics and avalanche exponents.
    Returns a dictionary of results.
    """
    results = {}
    for col in structural_cols:
        if col not in df.columns or avalanche_col not in df.columns:
            logger.warning(f"Missing column {col} or {avalanche_col}, skipping.")
            continue
        
        # Drop NaNs for correlation
        valid_data = df[[col, avalanche_col]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Not enough data points for correlation on {col}")
            continue

        corr, p_value = stats.spearmanr(valid_data[col], valid_data[avalanche_col])
        results[col] = {
            "correlation": corr,
            "p_value": p_value,
            "n": len(valid_data)
        }
        logger.info(f"Spearman r={corr:.3f}, p={p_value:.3f} for {col} vs {avalanche_col}")
    
    return results

def run_permutation_test(df: pd.DataFrame,
                         x_col: str,
                         y_col: str,
                         n_permutations: int = 1000,
                         seed: int = 42) -> Dict[str, float]:
    """
    Runs a non-parametric permutation test for the correlation between x and y.
    """
    np.random.seed(seed)
    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Align indices
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]
    
    if len(x) < 3:
        return {"observed_r": 0.0, "p_value": 1.0, "n": 0}

    observed_r, _ = stats.spearmanr(x, y)
    
    permuted_r = []
    for _ in range(n_permutations):
        y_shuffled = np.random.permutation(y.values)
        r, _ = stats.spearmanr(x.values, y_shuffled)
        permuted_r.append(r)
    
    p_value = (np.sum(np.abs(permuted_r) >= np.abs(observed_r)) + 1) / (n_permutations + 1)
    
    return {
        "observed_r": observed_r,
        "p_value": p_value,
        "n": len(x),
        "n_permutations": n_permutations
    }

def apply_holm_bonferroni_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, bool]:
    """
    Applies Holm-Bonferroni correction to a set of p-values.
    Returns a dictionary mapping feature names to significance (True/False).
    """
    sorted_features = sorted(p_values.keys(), key=lambda k: p_values[k])
    m = len(sorted_features)
    corrected_significance = {}
    
    for i, feature in enumerate(sorted_features):
        p = p_values[feature]
        threshold = alpha / (m - i)
        corrected_significance[feature] = p < threshold
        logger.debug(f"Holm-Bonferroni for {feature}: p={p:.4f}, threshold={threshold:.4f}, significant={corrected_significance[feature]}")
    
    return corrected_significance

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for a set of features.
    Flags features with VIF >= 5.
    """
    vif_data = {}
    X = df[features].dropna()
    
    if X.empty or len(X) < 3:
        logger.warning("Insufficient data to calculate VIF.")
        return {f: np.inf for f in features}
    
    # Add intercept is handled by VIF formula internally or by adding a column of ones if using manual calc
    # statsmodels VIF requires a constant column if not using formula API, but here we use the dataframe directly
    # The standard VIF calculation: VIF_j = 1 / (1 - R_j^2)
    # R_j^2 is from regressing feature j against all other features.
    
    # Using statsmodels VIF which expects a dataframe with constant if needed, 
    # but variance_inflation_factor usually works on the design matrix.
    # We assume the features are already centered or we just compute on raw.
    
    try:
        # Ensure we have a constant column if the model expects it, though VIF calculation 
        # on the features themselves usually implies regressing against others.
        # The standard implementation in statsmodels expects the design matrix.
        # We will compute VIF for each column against all others.
        
        # Note: variance_inflation_factor in statsmodels does not automatically add intercept.
        # We add a constant column for the regression if we were doing OLS, but for VIF 
        # of feature j against others, we just need the matrix of predictors.
        
        # Actually, the function `variance_inflation_factor` takes the exog matrix (X) and the index.
        # It calculates VIF for the column at `index` using all columns in `X`.
        
        for i, col in enumerate(features):
            if col not in X.columns:
                continue
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
    except Exception as e:
        log_exception(logger, e)
        # Fallback or error handling
        return {f: np.nan for f in features}
    
    return vif_data

def run_collinearity_diagnostics(df: pd.DataFrame, 
                                 structural_cols: List[str], 
                                 output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Runs collinearity diagnostics (VIF) on structural metrics.
    Flags features with VIF >= 5.
    """
    if not structural_cols:
        logger.warning("No structural columns provided for VIF calculation.")
        return {"vif": {}, "high_collinearity": [], "passed": True}
    
    vif_results = calculate_vif(df, structural_cols)
    high_collinearity = [col for col, val in vif_results.items() if val >= 5]
    
    result = {
        "vif": vif_results,
        "high_collinearity": high_collinearity,
        "threshold": 5.0,
        "passed": len(high_collinearity) == 0
    }
    
    logger.info(f"VIF Analysis complete. High collinearity found in: {high_collinearity}")
    
    if output_path:
        # Save VIF results to a CSV for reporting
        vif_df = pd.DataFrame(list(vif_results.items()), columns=["feature", "vif"])
        vif_df.to_csv(output_path, index=False)
        logger.info(f"VIF results saved to {output_path}")
    
    return result

def run_robustness_analysis(df: pd.DataFrame,
                            structural_cols: List[str],
                            avalanche_col: str,
                            vif_threshold: float = 5.0) -> Dict[str, Any]:
    """
    Runs the full robustness analysis including correlations, permutation tests,
    Holm-Bonferroni correction, and collinearity diagnostics.
    """
    logger.info("Starting robustness analysis pipeline.")
    
    # 1. Collinearity Diagnostics
    collinearity_result = run_collinearity_diagnostics(df, structural_cols)
    
    # Filter out features with high collinearity if necessary, or just report
    # For this task, we report them. The analysis might proceed with all, 
    # but the report should flag the issue.
    usable_cols = structural_cols # In a stricter pipeline, we might drop high VIF cols
    
    # 2. Correlations
    correlations = compute_spearman_correlations(df, usable_cols, avalanche_col)
    
    # 3. Permutation Tests
    perm_results = {}
    for col in usable_cols:
        if col in correlations:
            perm_results[col] = run_permutation_test(df, col, avalanche_col)
    
    # 4. Holm-Bonferroni
    p_values = {col: res["p_value"] for col, res in correlations.items()}
    corrected = apply_holm_bonferroni_correction(p_values)
    
    return {
        "collinearity": collinearity_result,
        "correlations": correlations,
        "permutation_tests": perm_results,
        "holm_bonferroni": corrected,
        "summary": {
            "total_features": len(structural_cols),
            "high_collinearity_count": len(collinearity_result["high_collinearity"]),
            "significant_correlations": sum(1 for v in corrected.values() if v)
        }
    }

def run_correlation_analysis(data_path: Optional[Path] = None,
                             output_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Main entry point to run the correlation analysis pipeline.
    Loads data, runs stats, and exports a summary report.
    """
    data_root = get_data_root()
    if data_path is None:
        data_path = data_root / "results" / "participant_metrics.csv"
    if output_dir is None:
        output_dir = data_root / "results"
    
    ensure_directories([output_dir])
    
    df = load_metrics_data(data_path)
    
    # Define columns based on expected schema from US2
    # Assuming structural metrics: degree, clustering, rich_club
    # Assuming avalanche metric: power_law_exponent
    structural_cols = ["degree_centrality", "clustering_coefficient", "rich_club_coefficient"]
    avalanche_col = "power_law_exponent"
    
    # Filter for columns that exist
    available_structural = [c for c in structural_cols if c in df.columns]
    if avalanche_col not in df.columns:
        raise ValueError(f"Avalanche column '{avalanche_col}' not found in data.")
    
    analysis_result = run_robustness_analysis(df, available_structural, avalanche_col)
    
    # Export results
    output_file = output_dir / "correlation_report.csv"
    
    # Flatten results for CSV export
    rows = []
    for col in available_structural:
        corr_data = analysis_result["correlations"].get(col, {})
        perm_data = analysis_result["permutation_tests"].get(col, {})
        sig = analysis_result["holm_bonferroni"].get(col, False)
        
        rows.append({
            "feature": col,
            "spearman_r": corr_data.get("correlation", np.nan),
            "spearman_p": corr_data.get("p_value", np.nan),
            "perm_p": perm_data.get("p_value", np.nan),
            "significant_holm": sig,
            "vif": analysis_result["collinearity"]["vif"].get(col, np.nan),
            "n": corr_data.get("n", np.nan)
        })
    
    report_df = pd.DataFrame(rows)
    report_df.to_csv(output_file, index=False)
    logger.info(f"Correlation report saved to {output_file}")
    
    return report_df

def main():
    """
    Command-line entry point for the stats module.
    """
    logger.info("Running stats analysis via main()")
    try:
        df = run_correlation_analysis()
        print(df)
    except Exception as e:
        log_exception(logger, e)
        sys.exit(1)

if __name__ == "__main__":
    main()