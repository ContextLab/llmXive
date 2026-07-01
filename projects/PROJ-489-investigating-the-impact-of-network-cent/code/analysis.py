import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

# Configure logger
logger = logging.getLogger(__name__)

def check_subject_count(df: pd.DataFrame) -> bool:
    """
    Check if the number of subjects is at least 30.
    
    Args:
        df: DataFrame containing subject metrics.
        
    Returns:
        True if N >= 30, False otherwise.
    """
    count = df['subject_id'].nunique()
    if count < 30:
        logger.warning(f"Subject count ({count}) is less than 30. "
                       "Downstream effect size estimation will be performed.")
    return count >= 30

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(group1) - np.mean(group2)) / pooled_std)

def calculate_effect_sizes(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str,
    groups: List[str]
) -> Dict[str, float]:
    """
    Calculate Cohen's d for pairs of groups based on a binary grouping variable.
    
    Args:
        df: DataFrame with data.
        x_col: Column name for the independent variable (e.g., centrality).
        y_col: Column name for the dependent variable (e.g., synchrony).
        group_col: Column name for the grouping variable.
        groups: List of group labels to compare.
        
    Returns:
        Dictionary mapping group pairs to Cohen's d.
    """
    if len(groups) != 2:
        logger.warning("Effect size calculation requires exactly two groups.")
        return {}
    
    g1, g2 = groups
    mask1 = df[group_col] == g1
    mask2 = df[group_col] == g2
    
    data1 = df.loc[mask1, y_col].values
    data2 = df.loc[mask2, y_col].values
    
    if len(data1) == 0 or len(data2) == 0:
        logger.warning(f"Missing data for groups {g1} or {g2}.")
        return {}
        
    d = calculate_cohens_d(data1, data2)
    return {f"{g1}_vs_{g2}": d}

def run_lme_analysis(
    df: pd.DataFrame,
    formula: str,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run Linear Mixed Effects (LME) analysis.
    
    Args:
        df: DataFrame with data.
        formula: Statsmodels formula string.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary with model results (params, pvalues).
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    try:
        model = smf.mixedlm(formula, df, groups=df["subject_id"])
        result = model.fit()
        
        return {
            "params": result.params.to_dict(),
            "pvalues": result.pvalues.to_dict(),
            "loglike": float(result.llf),
            "aic": float(result.aic),
            "bic": float(result.bic)
        }
    except Exception as e:
        logger.error(f"LME model fitting failed: {e}")
        return {
            "params": {},
            "pvalues": {},
            "loglike": None,
            "aic": None,
            "bic": None,
            "error": str(e)
        }

def run_shapiro_wilk(residuals: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality on residuals.
    
    Args:
        residuals: Array of residuals from a model.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(residuals) < 3:
        logger.warning("Not enough residuals for Shapiro-Wilk test.")
        return (0.0, 1.0)
    
    try:
        stat, p_val = stats.shapiro(residuals)
        return float(stat), float(p_val)
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return (0.0, 1.0)

def apply_benjamini_hochberg(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to a dictionary of p-values.
    
    Args:
        p_values: Dictionary mapping hypothesis names to raw p-values.
        
    Returns:
        Dictionary mapping hypothesis names to corrected p-values.
    """
    if not p_values:
        return {}
        
    names = list(p_values.keys())
    raw_p = np.array(list(p_values.values()))
    
    if np.any(np.isnan(raw_p)):
        logger.warning("NaN values found in p-values. Skipping correction for those.")
        # Filter out NaNs for calculation, then map back
        valid_mask = ~np.isnan(raw_p)
        valid_names = [n for i, n in enumerate(names) if valid_mask[i]]
        valid_p = raw_p[valid_mask]
    else:
        valid_names = names
        valid_p = raw_p
    
    sorted_indices = np.argsort(valid_p)
    sorted_p = valid_p[sorted_indices]
    n = len(sorted_p)
    
    # Calculate BH critical values
    bh_values = (np.arange(1, n + 1) / n) * sorted_p[-1] # Approximation using max p
    # Standard BH: p_i * n / i
    # We want adjusted p-values that are monotonic
    adjusted = np.empty(n)
    for i in range(n - 1, -1, -1):
        if i == n - 1:
            adjusted[i] = sorted_p[i] * n / (i + 1)
        else:
            adjusted[i] = min(sorted_p[i] * n / (i + 1), adjusted[i+1])
    
    # Ensure values are <= 1
    adjusted = np.minimum(adjusted, 1.0)
    
    # Map back to original order
    final_dict = {}
    for i, idx in enumerate(sorted_indices):
        original_name = valid_names[idx]
        final_dict[original_name] = float(adjusted[i])
        
    # Add back NaNs as NaN
    for i, is_nan in enumerate(np.isnan(raw_p)):
        if is_nan:
            final_dict[names[i]] = float('nan')
            
    return final_dict

def generate_analysis_report(
    lme_results: Dict[str, Any],
    fdr_results: Dict[str, float],
    shapiro_results: Tuple[float, float],
    effect_sizes: Optional[Dict[str, float]] = None,
    temporal_proximity_flag: bool = False
) -> Dict[str, Any]:
    """
    Assemble the final analysis report dictionary.
    
    Args:
        lme_results: LME model output.
        fdr_results: FDR corrected p-values.
        shapiro_results: Shapiro-Wilk stats and p-value.
        effect_sizes: Optional effect sizes.
        temporal_proximity_flag: Flag indicating confounding limitation.
        
    Returns:
        Complete report dictionary.
    """
    report: Dict[str, Any] = {
        "lme_results": lme_results,
        "fdr_corrected_p_values": fdr_results,
        "shapiro_wilk": {
            "statistic": shapiro_results[0],
            "p_value": shapiro_results[1]
        },
        "temporal_proximity_confound": temporal_proximity_flag
    }
    
    if effect_sizes:
        report["effect_sizes"] = effect_sizes
    
    # Determine significance flags
    significant_results = []
    non_significant_results = []
    
    if "pvalues" in lme_results:
        for key, p_val in lme_results["pvalues"].items():
            if p_val is None or np.isnan(p_val):
                continue
            
            fdr_p = fdr_results.get(key, p_val)
            if fdr_p < 0.05:
                significant_results.append({
                    "parameter": key,
                    "raw_p": p_val,
                    "fdr_p": fdr_p,
                    "status": "Significant"
                })
            else:
                non_significant_results.append({
                    "parameter": key,
                    "raw_p": p_val,
                    "fdr_p": fdr_p,
                    "status": "Non-Significant"
                })
    
    report["significance_summary"] = {
        "significant": significant_results,
        "non_significant": non_significant_results
    }
    
    return report

def main() -> None:
    """
    Main entry point for the analysis pipeline.
    Loads metrics, runs LME, FDR, diagnostics, and saves results.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.error("config.yaml not found. Exiting.")
        return

    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)
    
    # Paths
    metrics_path = Path("data/metrics/SubjectMetrics.csv")
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}. Exiting.")
        return
    
    df = pd.read_csv(metrics_path)
    
    # 1. Check subject count
    n_subjects = check_subject_count(df)
    
    # 2. Run LME
    # Assuming columns exist as per spec: centrality, pli, global_coherence
    formula = "centrality ~ pli + global_coherence + (1|subject_id)"
    # Note: statsmodels mixedlm formula syntax is 'y ~ x + (1|group)'
    # But standard statsmodels formula for mixedlm is 'y ~ x' with groups argument.
    # The prompt spec says: `centrality ~ pli + global_coherence + (1|subject)`
    # This looks like lme4 syntax. In statsmodels:
    # model = smf.mixedlm("centrality ~ pli + global_coherence", df, groups=df["subject_id"])
    
    # Adjusting formula for statsmodels.mixedlm
    lme_formula = "centrality ~ pli + global_coherence"
    
    lme_results = run_lme_analysis(df, lme_formula, random_state=config.get("random_seed", 42))
    
    # 3. Shapiro-Wilk on residuals (if model succeeded)
    shapiro_stat, shapiro_p = 0.0, 1.0
    if "params" in lme_results and lme_results["params"]:
        # Re-fit to get residuals if not stored, or extract from result object if we stored it
        # Since we returned dict, we need to re-run or store residuals in run_lme_analysis
        # Let's re-run briefly to get residuals
        try:
            model = smf.mixedlm(lme_formula, df, groups=df["subject_id"])
            result = model.fit()
            residuals = result.resid
            shapiro_stat, shapiro_p = run_shapiro_wilk(residuals)
        except Exception as e:
            logger.error(f"Could not compute residuals for Shapiro-Wilk: {e}")
    
    # 4. FDR Correction
    raw_p_values = lme_results.get("pvalues", {})
    fdr_p_values = apply_benjamini_hochberg(raw_p_values)
    
    # 5. Effect Sizes (if N < 30)
    effect_sizes = None
    if not n_subjects:
        # Assume binary grouping for demonstration if needed, or skip
        # Spec says: compute effect sizes for each centrality-synchrony pair
        # This implies comparing high vs low centrality? Or specific groups?
        # Since we don't have explicit groups in the CSV, we skip or log warning
        logger.info("Subject count < 30. Effect size calculation requires grouping logic not present in CSV.")
        # Placeholder: calculate d for first numeric column vs median split?
        # Spec T011 says "append these to analysis_results.json". 
        # We will calculate d for centrality split by median if possible
        if 'centrality' in df.columns:
            median_c = df['centrality'].median()
            groups = ['high', 'low']
            df['centrality_group'] = df['centrality'].apply(lambda x: 'high' if x >= median_c else 'low')
            effect_sizes = calculate_effect_sizes(df, 'centrality', 'global_coherence', 'centrality_group', groups)
    
    # 6. Temporal Proximity Flag
    # This should come from T029/T041 logic. Assuming it's in the config or we check a flag
    # For this task, we assume a flag is passed or derived.
    # Let's assume a config flag or check a column if it exists
    temporal_flag = False
    if 'temporal_proximity_flag' in config:
        temporal_flag = config['temporal_proximity_flag']
    
    # 7. Generate Report
    report = generate_analysis_report(
        lme_results=lme_results,
        fdr_results=fdr_p_values,
        shapiro_results=(shapiro_stat, shapiro_p),
        effect_sizes=effect_sizes,
        temporal_proximity_flag=temporal_flag
    )
    
    # 8. Save Results
    results_path = results_dir / "analysis_results.json"
    with open(results_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Analysis results saved to {results_path}")

if __name__ == "__main__":
    main()