import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multitest import multipletests
from scipy.stats import shapiro

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_subject_count(df: pd.DataFrame, min_count: int = 30) -> bool:
    """
    Check if the number of unique subjects meets the minimum requirement.
    
    Args:
        df: DataFrame containing subject data.
        min_count: Minimum required number of subjects.
        
    Returns:
        True if count >= min_count, False otherwise.
    """
    if 'subject_id' not in df.columns:
        logger.warning("DataFrame missing 'subject_id' column.")
        return False
    
    unique_subjects = df['subject_id'].nunique()
    if unique_subjects < min_count:
        logger.warning(f"Subject count ({unique_subjects}) is below minimum ({min_count}).")
        return False
    return True

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    if n1 + n2 == 0:
        return 0.0
        
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_effect_sizes(df: pd.DataFrame, metric_col: str, group_col: str) -> Dict[str, float]:
    """
    Calculate effect sizes (Cohen's d) for each group combination.
    
    Args:
        df: DataFrame with metric and group columns.
        metric_col: Name of the metric column.
        group_col: Name of the group column.
        
    Returns:
        Dictionary mapping group pairs to Cohen's d values.
    """
    effect_sizes = {}
    groups = df[group_col].unique()
    
    for i, g1 in enumerate(groups):
        for g2 in groups[i+1:]:
            vals1 = df[df[group_col] == g1][metric_col].values
            vals2 = df[df[group_col] == g2][metric_col].values
            if len(vals1) > 0 and len(vals2) > 0:
                d = calculate_cohens_d(vals1, vals2)
                effect_sizes[f"{g1}_vs_{g2}"] = d
                
    return effect_sizes

def run_lme_analysis(df: pd.DataFrame, formula: str, dependent_var: str) -> Tuple[Any, Dict[str, float]]:
    """
    Run Linear Mixed Effects (LME) analysis.
    
    Args:
        df: Input DataFrame.
        formula: Statsmodels formula string (e.g., "centrality ~ pli + global_coherence + (1|subject)").
        dependent_var: Name of the dependent variable for result extraction.
        
    Returns:
        Tuple of (fitted model object, dictionary of raw p-values).
    """
    logger.info(f"Running LME analysis with formula: {formula}")
    
    # Ensure numeric columns are numeric
    for col in df.columns:
        if col not in ['subject_id']:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass
    
    # Drop rows with NaN in relevant columns for regression
    df_clean = df.dropna(subset=[dependent_var] + [col.split('+')[0].split('~')[0].strip().split()[0] for col in formula.split('+') if '1|' not in col])
    
    if len(df_clean) < 3:
        logger.error("Not enough data points for LME analysis after cleaning.")
        raise ValueError("Insufficient data for LME analysis.")

    try:
        model = mixedlm(formula, df_clean, groups=df_clean["subject_id"])
        result = model.fit()
        
        # Extract p-values for fixed effects
        p_values = {}
        for param, p_val in result.pvalues.items():
            p_values[param] = float(p_val)
            
        logger.info(f"LME analysis completed. P-values: {p_values}")
        return result, p_values
        
    except Exception as e:
        logger.error(f"LME analysis failed: {e}")
        raise

def run_shapiro_wilk(df: pd.DataFrame, residuals_col: str = 'residuals') -> Dict[str, float]:
    """
    Perform Shapiro-Wilk test on residuals for diagnostic purposes.
    
    Args:
        df: DataFrame containing residuals.
        residuals_col: Name of the column containing residuals.
        
    Returns:
        Dictionary with 'statistic' and 'pvalue'.
    """
    logger.info("Running Shapiro-Wilk test on residuals.")
    
    if residuals_col not in df.columns:
        logger.warning(f"Column '{residuals_col}' not found. Skipping Shapiro-Wilk.")
        return {"statistic": 0.0, "pvalue": 1.0}
        
    residuals = df[residuals_col].dropna()
    if len(residuals) < 3:
        logger.warning("Not enough residuals for Shapiro-Wilk test.")
        return {"statistic": 0.0, "pvalue": 1.0}
        
    stat, pval = shapiro(residuals)
    logger.info(f"Shapiro-Wilk: stat={stat:.4f}, p={pval:.4f}")
    return {"statistic": float(stat), "pvalue": float(pval)}

def apply_benjamini_hochberg(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to a dictionary of p-values.
    
    Args:
        p_values: Dictionary mapping hypothesis names to raw p-values.
        alpha: Significance level.
        
    Returns:
        Dictionary mapping hypothesis names to FDR-corrected p-values.
    """
    if not p_values:
        return {}
        
    names = list(p_values.keys())
    raw_p = list(p_values.values())
    
    # multipletests returns (reject, p_corrected, p_adjusted, alphacSidak, alphacBonf)
    # We use method='fdr_bh' for Benjamini-Hochberg
    _, p_corrected, _, _ = multipletests(raw_p, alpha=alpha, method='fdr_bh')
    
    corrected_p = {name: float(p) for name, p in zip(names, p_corrected)}
    logger.info(f"FDR Correction applied. Corrected p-values: {corrected_p}")
    return corrected_p

def generate_analysis_report(
    lme_result: Any,
    raw_p_values: Dict[str, float],
    fdr_p_values: Dict[str, float],
    shapiro_result: Dict[str, float],
    effect_sizes: Optional[Dict[str, float]] = None,
    n_subjects: int = 0
) -> Dict[str, Any]:
    """
    Generate the final analysis report dictionary.
    
    Args:
        lme_result: Fitted LME model object.
        raw_p_values: Dictionary of raw p-values.
        fdr_p_values: Dictionary of FDR-corrected p-values.
        shapiro_result: Shapiro-Wilk diagnostic results.
        effect_sizes: Optional dictionary of effect sizes.
        n_subjects: Total number of subjects.
        
    Returns:
        Dictionary containing the full analysis report.
    """
    report = {
        "metadata": {
            "n_subjects": n_subjects,
            "shapiro_wilk": shapiro_result
        },
        "lme_results": {
            "coefficients": {k: float(v) for k, v in lme_result.fe_params.items()},
            "raw_p_values": raw_p_values,
            "fdr_corrected_p_values": fdr_p_values,
            "summary": str(lme_result.summary())
        }
    }
    
    if effect_sizes:
        report["effect_sizes"] = effect_sizes
        
    return report

def main():
    """
    Main entry point for Task T037.
    Reads metrics, runs LME, applies FDR, and writes analysis_results.json.
    """
    logger.info("Starting T037: LME Analysis and FDR Correction.")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    metrics_path = base_dir / "data" / "metrics" / "SubjectMetrics.csv"
    output_dir = base_dir / "data" / "results"
    output_path = output_dir / "analysis_results.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        # Create a dummy report to avoid crash if data is missing, 
        # though in a real run this should fail or be handled upstream.
        report = {
            "error": "SubjectMetrics.csv not found",
            "metadata": {"n_subjects": 0}
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    # Load Data
    logger.info(f"Loading metrics from {metrics_path}")
    df = pd.read_csv(metrics_path)
    
    # Check subject count (T034 logic)
    n_subjects = df['subject_id'].nunique()
    check_subject_count(df, min_count=30)
    
    # Define variables for LME
    # Assuming the metrics file has columns: subject_id, centrality, pli, global_coherence
    # If columns differ, we map them or raise error.
    required_cols = ['subject_id', 'centrality', 'pli', 'global_coherence']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in metrics: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
        
    # Run LME
    formula = "centrality ~ pli + global_coherence + (1|subject_id)"
    try:
        lme_model, raw_p = run_lme_analysis(df, formula, "centrality")
    except ValueError as e:
        logger.error(f"LME failed: {e}")
        return
        
    # Apply FDR
    fdr_p = apply_benjamini_hochberg(raw_p)
    
    # Shapiro-Wilk on residuals
    # Extract residuals from the fitted model if possible, or calculate manually
    # statsmodels mixedlm result has residuals property
    residuals = lme_model.resid
    df_resid = pd.DataFrame({'residuals': residuals})
    shapiro_res = run_shapiro_wilk(df_resid)
    
    # Effect sizes (if N < 30, though we calculate regardless for completeness)
    # We compare high vs low centrality groups or similar, but task T011 handles specific logic.
    # Here we just include if available or empty.
    effect_sizes = {}
    if n_subjects < 30:
        # Simple split median for demonstration if not handled by T011 explicitly
        median_c = df['centrality'].median()
        low_group = df[df['centrality'] < median_c]
        high_group = df[df['centrality'] >= median_c]
        effect_sizes["centrality_low_vs_high_pli"] = calculate_cohens_d(
            low_group['pli'].values, high_group['pli'].values
        )
    
    # Generate Report
    report = generate_analysis_report(
        lme_model,
        raw_p,
        fdr_p,
        shapiro_res,
        effect_sizes=effect_sizes if effect_sizes else None,
        n_subjects=n_subjects
    )
    
    # Write Output
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Analysis results written to {output_path}")

if __name__ == "__main__":
    main()
