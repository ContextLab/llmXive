import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from config_utils import load_config

logger = logging.getLogger(__name__)

def check_subject_count(metrics_df: pd.DataFrame, min_count: int = 30) -> bool:
    """Verify if the subject count meets the minimum threshold."""
    count = metrics_df['subject_id'].nunique()
    logger.info(f"Subject count: {count} (min required: {min_count})")
    return count >= min_count

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size between two groups."""
    mean_diff = np.mean(group1) - np.mean(group2)
    std_pooled = np.sqrt((np.std(group1, ddof=1)**2 + np.std(group2, ddof=1)**2) / 2)
    if std_pooled == 0:
        return 0.0
    return float(mean_diff / std_pooled)

def calculate_effect_sizes(
    metrics_df: pd.DataFrame,
    centralities: List[str],
    synchrony_cols: List[str]
) -> Dict[str, float]:
    """Calculate effect sizes for centrality-synchrony pairs when N < 30."""
    effect_sizes = {}
    for centrality in centralities:
        for synchrony in synchrony_cols:
            if centrality in metrics_df.columns and synchrony in metrics_df.columns:
                group1 = metrics_df[metrics_df['pli_mean'] > metrics_df['pli_mean'].median()][centrality].values
                group2 = metrics_df[metrics_df['pli_mean'] <= metrics_df['pli_mean'].median()][centrality].values
                if len(group1) > 0 and len(group2) > 0:
                    effect_sizes[f"{centrality}_{synchrony}"] = calculate_cohens_d(group1, group2)
    return effect_sizes

def run_lme_analysis(
    metrics_df: pd.DataFrame,
    formula: str = "centrality ~ pli + global_coherence + (1|subject)"
) -> Dict[str, Any]:
    """Run Linear Mixed Effects analysis on the metrics dataframe."""
    results = {}
    try:
        # Ensure required columns exist, otherwise skip or handle gracefully
        required_cols = ['subject_id', 'pli_mean', 'global_coherence']
        if not all(col in metrics_df.columns for col in required_cols):
            logger.warning("Required columns missing for LME analysis.")
            return results

        # Placeholder for actual centrality column selection logic
        # In a real scenario, this would iterate over centrality metrics
        centrality_col = 'degree_centrality' 
        if centrality_col not in metrics_df.columns:
            centrality_col = metrics_df.columns[0] # Fallback for demo structure

        model = smf.mixedlm(
            f"{centrality_col} ~ pli_mean + global_coherence",
            metrics_df,
            groups=metrics_df['subject_id']
        )
        lme_result = model.fit()
        
        results['coefficients'] = lme_result.params.to_dict()
        results['p_values'] = lme_result.pvalues.to_dict()
        results['summary'] = lme_result.summary().as_text()
    except Exception as e:
        logger.error(f"LME analysis failed: {e}")
    return results

def run_shapiro_wilk(
    metrics_df: pd.DataFrame,
    target_col: str = "residuals"
) -> Dict[str, float]:
    """Perform Shapiro-Wilk test on residuals for normality diagnostics."""
    from scipy.stats import shapiro
    if target_col not in metrics_df.columns:
        logger.warning(f"Target column {target_col} not found for Shapiro-Wilk.")
        return {}
    
    data = metrics_df[target_col].dropna()
    if len(data) < 3:
        logger.warning("Insufficient data for Shapiro-Wilk test.")
        return {}
        
    stat, p_val = shapiro(data)
    return {"statistic": float(stat), "p_value": float(p_val)}

def apply_benjamini_hochberg(
    p_values: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, float]:
    """Apply Benjamini-Hochberg FDR correction to a dictionary of p-values."""
    if not p_values:
        return {}
    
    names = list(p_values.keys())
    p_vals = list(p_values.values())
    
    # Filter out NaNs if any
    valid_indices = [i for i, p in enumerate(p_vals) if not np.isnan(p)]
    if not valid_indices:
        return {}
        
    p_vals_clean = [p_vals[i] for i in valid_indices]
    names_clean = [names[i] for i in valid_indices]
    
    reject, p_vals_corrected, _, _ = multipletests(
        p_vals_clean, alpha=alpha, method='fdr_bh'
    )
    
    result = {}
    for i, name in enumerate(names_clean):
        result[name] = float(p_vals_corrected[i])
    return result

def generate_analysis_report(
    lme_results: Dict[str, Any],
    fdr_results: Dict[str, float],
    effect_sizes: Optional[Dict[str, float]] = None,
    shapiro_results: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Compile all analysis results into a single report dictionary."""
    report = {
        "lme_results": lme_results,
        "fdr_corrected_p_values": fdr_results,
        "significance_flags": {k: "Significant" if v < 0.05 else "Non-Significant" 
                               for k, v in fdr_results.items()}
    }
    
    if effect_sizes:
        report["effect_sizes"] = effect_sizes
    if shapiro_results:
        report["shapiro_wilk_diagnostics"] = shapiro_results
        
    return report

def main() -> None:
    """Main entry point for the analysis pipeline."""
    config = load_config()
    metrics_path = Path(config.get("paths", {}).get("metrics_csv", "data/metrics/SubjectMetrics.csv"))
    output_dir = Path(config.get("paths", {}).get("results_dir", "data/results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return

    metrics_df = pd.read_csv(metrics_path)
    
    # Check subject count
    sufficient_data = check_subject_count(metrics_df)
    
    # Run LME
    lme_res = run_lme_analysis(metrics_df)
    
    # Extract p-values for FDR
    p_vals = lme_res.get("p_values", {})
    fdr_res = apply_benjamini_hochberg(p_vals)
    
    # Effect sizes if needed
    effect_sizes = None
    if not sufficient_data:
        effect_sizes = calculate_effect_sizes(metrics_df, ['degree_centrality'], ['pli_mean'])
    
    # Diagnostics
    shapiro_res = run_shapiro_wilk(metrics_df, 'residuals')
    
    # Generate Report
    report_data = generate_analysis_report(lme_res, fdr_res, effect_sizes, shapiro_res)
    
    # Save Results
    results_path = output_dir / "analysis_results.json"
    with open(results_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Analysis results saved to {results_path}")

if __name__ == "__main__":
    main()