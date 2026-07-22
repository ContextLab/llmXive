import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import FTestPower
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    X = df[features].dropna()
    if X.empty:
        logger.warning("No data available for VIF calculation.")
        return {feat: np.inf for feat in features}
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    vif_data = {}
    
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.inf
            
    return vif_data

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values.
    
    Args:
        p_values: List of uncorrected p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (corrected p-values, boolean mask of significant results).
    """
    if not p_values:
        return [], []
    
    try:
        corrected, rejected = multipletests(p_values, alpha=alpha, method='fdr_bh')
        return corrected, rejected
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        return p_values, [False] * len(p_values)

def run_power_analysis(effect_size: float = 0.15, alpha: float = 0.05, power: float = 0.8) -> Dict:
    """
    Run power analysis to determine minimum sample size required.
    
    Args:
        effect_size: Cohen's f2 effect size.
        alpha: Significance level.
        power: Desired statistical power.
        
    Returns:
        Dictionary with power analysis results.
    """
    f2 = effect_size
    f2_u = f2 / (1 - f2)
    numerator_dof = 1  # Assuming one predictor of interest
    
    f_test = FTestPower()
    n_required = f_test.solve_power(effect_size=f2_u, nobs1=None, alpha=alpha, power=power, 
                                    k_num=numerator_dof, k_denom=1)
    
    result = {
        "min_N_required": int(np.ceil(n_required)) if n_required else 0,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "method": "FTestPower"
    }
    
    logger.info(f"Power analysis complete: Minimum N required = {result['min_N_required']}")
    return result

def run_ancova_analysis(df: pd.DataFrame, pre_col: str, post_col: str, metric_col: str, 
                        confounds: List[str] = None, fd_col: str = None) -> Dict:
    """
    Perform ANCOVA analysis: Post ~ Pre + Metric + Confounds + FD_Covariate.
    
    Args:
        df: DataFrame with all variables.
        pre_col: Column name for pre-treatment score.
        post_col: Column name for post-treatment score.
        metric_col: Column name for network metric.
        confounds: List of confound variable names.
        fd_col: Column name for framewise displacement.
        
    Returns:
        Dictionary with regression results.
    """
    # Prepare data
    features = [pre_col, metric_col]
    if confounds:
        features.extend([c for c in confounds if c in df.columns])
    if fd_col and fd_col in df.columns:
        features.append(fd_col)
        
    # Drop rows with missing values
    cols_to_use = [post_col] + features
    clean_df = df[cols_to_use].dropna()
    
    if len(clean_df) < 5:
        logger.warning("Insufficient data for ANCOVA (N < 5).")
        return {"error": "Insufficient data", "N": len(clean_df)}
    
    y = clean_df[post_col]
    X = clean_df[features]
    X = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X).fit()
        results = {
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "r_squared": model.rsquared,
            "adj_r_squared": model.rsquared_adj,
            "N": len(clean_df),
            "model_type": "OLS",
            "formula": model.formula
        }
        logger.info(f"ANCOVA completed: R² = {results['r_squared']:.4f}, N = {results['N']}")
        return results
    except Exception as e:
        logger.error(f"ANCOVA failed: {e}")
        return {"error": str(e), "model_type": "Failed"}

def run_sensitivity_analysis(metrics_df: pd.DataFrame, 
                             motion_thresholds: List[float] = [2.0, 3.0],
                             p_values: List[float] = [0.01, 0.05, 0.1],
                             pre_col: str = 'pre_treatment_score',
                             post_col: str = 'post_treatment_score',
                             metric_col: str = 'modularity',
                             fd_col: str = 'mean_fd') -> Dict:
    """
    Perform sensitivity analysis by sweeping motion thresholds and p-value thresholds.
    
    Args:
        metrics_df: DataFrame containing metrics and motion data.
        motion_thresholds: List of motion thresholds (mm) to test.
        p_values: List of p-value thresholds to test.
        pre_col: Pre-treatment score column.
        post_col: Post-treatment score column.
        metric_col: Network metric column.
        fd_col: Framewise displacement column.
        
    Returns:
        Dictionary with sensitivity analysis results.
    """
    logger.info("Starting sensitivity analysis...")
    results = []
    
    for motion_thresh in motion_thresholds:
        # Filter data based on motion threshold
        if fd_col in metrics_df.columns:
            filtered_df = metrics_df[metrics_df[fd_col] <= motion_thresh].copy()
        else:
            filtered_df = metrics_df.copy()
        
        if len(filtered_df) < 5:
            logger.warning(f"Motion threshold {motion_thresh}mm leaves N={len(filtered_df)} < 5. Skipping.")
            continue
            
        for p_thresh in p_values:
            # Run ANCOVA
            ancova_results = run_ancova_analysis(
                filtered_df, 
                pre_col, post_col, metric_col,
                confounds=['age'] if 'age' in filtered_df.columns else None,
                fd_col=fd_col
            )
            
            if "error" in ancova_results:
                significant_count = 0
            else:
                # Check if the metric coefficient is significant
                p_val = ancova_results['p_values'].get(metric_col, 1.0)
                significant_count = 1 if p_val <= p_thresh else 0
            
            results.append({
                "motion_threshold_mm": motion_thresh,
                "p_value_threshold": p_thresh,
                "N": len(filtered_df),
                "significant_findings": significant_count,
                "metric_coefficient": ancova_results.get('coefficients', {}).get(metric_col, None),
                "metric_p_value": ancova_results.get('p_values', {}).get(metric_col, None),
                "r_squared": ancova_results.get('r_squared', None)
            })
            
    return results

def save_sensitivity_report(results: Dict, output_path: Path) -> None:
    """
    Save sensitivity analysis results to a markdown report.
    
    Args:
        results: Dictionary with sensitivity analysis results.
        output_path: Path to save the markdown report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "This report summarizes the robustness of findings across different motion thresholds and p-value significance levels.",
        "",
        "## Methodology",
        "- Motion thresholds tested: 2.0mm, 3.0mm",
        "- P-value thresholds tested: 0.01, 0.05, 0.1",
        "- Analysis: ANCOVA (Post ~ Pre + Metric + Confounds + FD)",
        "",
        "## Summary Table",
        "",
        "| Motion Threshold (mm) | P-value Threshold | N | Significant Findings | Metric Coefficient | Metric P-value | R² |",
        "|----------------------|-------------------|---|----------------------|--------------------|----------------|-----|"
    ]
    
    for res in results:
        coeff_str = f"{res['metric_coefficient']:.4f}" if res['metric_coefficient'] is not None else "N/A"
        p_str = f"{res['metric_p_value']:.4f}" if res['metric_p_value'] is not None else "N/A"
        r2_str = f"{res['r_squared']:.4f}" if res['r_squared'] is not None else "N/A"
        
        report_lines.append(
            f"| {res['motion_threshold_mm']} | {res['p_value_threshold']} | {res['N']} | "
            f"{res['significant_findings']} | {coeff_str} | {p_str} | {r2_str} |"
        )
    
    report_lines.extend([
        "",
        "## Interpretation",
        "",
        "A finding is considered significant if the p-value of the network metric coefficient is less than the specified p-value threshold.",
        "Motion thresholds filter subjects with excessive head movement (> threshold mm).",
        "",
        "## Conclusion",
        ""
    ])
    
    # Add a brief conclusion based on the data
    if results:
        stable_count = sum(1 for r in results if r['significant_findings'] == 1)
        total_tests = len(results)
        stability_rate = stable_count / total_tests if total_tests > 0 else 0
        
        report_lines.append(f"- Out of {total_tests} sensitivity tests, {stable_count} ({stability_rate:.1%}) showed significant findings.")
        if stability_rate > 0.8:
            report_lines.append("- Findings appear **robust** across tested thresholds.")
        elif stability_rate > 0.5:
            report_lines.append("- Findings show **moderate robustness** but are sensitive to threshold choices.")
        else:
            report_lines.append("- Findings are **sensitive** to threshold choices; interpret with caution.")
    else:
        report_lines.append("- No valid results were generated due to insufficient data or errors.")
        
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
        
    logger.info(f"Sensitivity analysis report saved to {output_path}")

def run_analysis(config: Dict) -> None:
    """
    Main entry point for analysis tasks.
    
    Args:
        config: Configuration dictionary with paths and parameters.
    """
    logger.info("Running analysis pipeline...")
    
    # Load data
    metrics_path = Path(config.get('metrics_path', 'data/metrics/network_metrics.csv'))
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return
        
    metrics_df = pd.read_csv(metrics_path)
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(
        metrics_df,
        motion_thresholds=[2.0, 3.0],
        p_values=[0.01, 0.05, 0.1],
        pre_col='pre_treatment_score',
        post_col='post_treatment_score',
        metric_col='modularity',
        fd_col='mean_fd'
    )
    
    # Save report
    report_path = Path(config.get('report_path', 'reports/sensitivity_analysis.md'))
    save_sensitivity_report(sensitivity_results, report_path)
    
    logger.info("Analysis pipeline completed successfully.")

def main():
    """Command-line entry point."""
    config = {
        'metrics_path': 'data/metrics/network_metrics.csv',
        'report_path': 'reports/sensitivity_analysis.md'
    }
    run_analysis(config)

if __name__ == '__main__':
    main()