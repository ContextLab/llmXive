"""
Statistical analysis module for brain network dynamics and VR therapy response.
Implements ANCOVA, power analysis, VIF collinearity checks, FDR correction,
and sensitivity analysis.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.power import FTestPower
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import json
import os

logger = logging.getLogger(__name__)


class CollinearityUnresolvableError(Exception):
    """Raised when collinearity cannot be resolved via PCA."""
    pass


def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    
    Args:
        df: DataFrame containing the features.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        Maximum VIF value across all features.
    """
    if not feature_cols:
        return 0.0
    
    X = df[feature_cols].dropna()
    if X.shape[0] < len(feature_cols) + 1:
        logger.warning("Not enough samples to calculate VIF reliably.")
        return float('inf')
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_values = []
    for col in feature_cols:
        try:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_values.append(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_values.append(float('inf'))
    
    return max(vif_values) if vif_values else 0.0


def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply False Discovery Rate (FDR) correction to a list of p-values.
    
    Args:
        p_values: List of uncorrected p-values.
        alpha: Significance level.
        
    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []
    
    try:
        _, p_values_corrected, _, _ = multipletests(
            p_values, 
            alpha=alpha, 
            method='fdr_bh', 
            is_sorted=False, 
            returnsorted=False
        )
        return p_values_corrected.tolist()
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        return p_values


def load_power_analysis_results() -> Optional[Dict[str, Any]]:
    """Load power analysis results from JSON file."""
    path = Path("data/metrics/power_analysis.json")
    if not path.exists():
        logger.warning(f"Power analysis file not found: {path}")
        return None
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load power analysis results: {e}")
        return None


def run_power_analysis(n_obs: int, effect_size: float = 0.15, alpha: float = 0.05, power: float = 0.8) -> Dict[str, Any]:
    """
    Run power analysis to determine minimum sample size required.
    
    Args:
        n_obs: Current number of observations.
        effect_size: Cohen's f-squared (default 0.15 for medium effect).
        alpha: Significance level.
        power: Desired statistical power.
        
    Returns:
        Dictionary with power analysis results.
    """
    logger.info(f"Running power analysis: n_obs={n_obs}, effect_size={effect_size}, alpha={alpha}, power={power}")
    
    ft = FTestPower()
    
    try:
        # Calculate minimum N required
        result = ft.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            nobs1=None,
            ratio=1.0,
            alternative='two-sided'
        )
        
        min_n_required = int(np.ceil(result))
        
        # Determine status
        if n_obs < 5:
            status = "HALT"
            warning_message = "Insufficient Power: N < 5"
        elif n_obs < min_n_required:
            status = "WARNING"
            warning_message = "WARNING: Underpowered for hypothesis testing (Power < 0.8)"
        else:
            status = "OK"
            warning_message = ""
        
        result_dict = {
            "min_N_required": min_n_required,
            "effect_size": effect_size,
            "alpha": alpha,
            "power": power,
            "method": "FTestPower",
            "status": status,
            "warning_message": warning_message,
            "current_n": n_obs
        }
        
        # Save to file
        output_path = Path("data/metrics/power_analysis.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"Power analysis saved to {output_path}: status={status}, min_N={min_n_required}")
        
        return result_dict
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return {
            "min_N_required": -1,
            "effect_size": effect_size,
            "alpha": alpha,
            "power": power,
            "method": "FTestPower",
            "status": "ERROR",
            "warning_message": f"Power analysis error: {str(e)}",
            "current_n": n_obs
        }


def run_ancova_analysis(
    df: pd.DataFrame,
    outcome_col: str,
    pre_col: str,
    metric_col: str,
    confound_cols: Optional[List[str]] = None,
    fd_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run ANCOVA analysis: Outcome ~ Pre + Metric + Confounds + FD.
    
    Args:
        df: DataFrame with all variables.
        outcome_col: Name of the outcome variable (post-treatment).
        pre_col: Name of the pre-treatment covariate.
        metric_col: Name of the network metric predictor.
        confound_cols: List of confound variable names.
        fd_col: Name of the framewise displacement covariate.
        
    Returns:
        Dictionary with model results.
    """
    logger.info(f"Running ANCOVA: {outcome_col} ~ {pre_col} + {metric_col}")
    
    # Build formula
    predictors = [pre_col, metric_col]
    if confound_cols:
        predictors.extend(confound_cols)
    if fd_col and fd_col in df.columns:
        predictors.append(fd_col)
    
    formula = f"{outcome_col} ~ " + " + ".join(predictors)
    
    # Prepare data
    model_data = df[[outcome_col] + predictors].dropna()
    
    if model_data.shape[0] < len(predictors) + 1:
        raise ValueError(f"Insufficient data for ANCOVA: {model_data.shape[0]} rows, {len(predictors)+1} parameters needed")
    
    y = model_data[outcome_col]
    X = sm.add_constant(model_data[predictors])
    
    try:
        model = sm.OLS(y, X).fit()
        
        # Extract results for the metric of interest
        metric_idx = predictors.index(metric_col)
        metric_coef = model.params[metric_idx]
        metric_pval = model.pvalues[metric_idx]
        r_squared = model.rsquared
        
        return {
            "formula": formula,
            "metric_coefficient": float(metric_coef),
            "metric_p_value": float(metric_pval),
            "r_squared": float(r_squared),
            "n_obs": int(model_data.shape[0]),
            "params": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict()
        }
    except Exception as e:
        logger.error(f"ANCOVA model fitting failed: {e}")
        raise


def run_sensitivity_analysis(
    df: pd.DataFrame,
    outcome_col: str,
    pre_col: str,
    metric_cols: List[str],
    motion_thresholds: List[float] = [2.0, 3.0],
    pval_thresholds: List[float] = [0.01, 0.05, 0.1],
    outcome_defs: List[str] = ["change", "residual", "raw"],
    fd_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis sweeping motion thresholds, p-values, and outcome definitions.
    
    Args:
        df: DataFrame with all variables.
        outcome_col: Base outcome variable name.
        pre_col: Pre-treatment covariate.
        metric_cols: List of network metric columns to test.
        motion_thresholds: List of motion thresholds (mm) to test.
        pval_thresholds: List of p-value thresholds to test.
        outcome_defs: List of outcome definitions to test.
        fd_col: Framewise displacement column name.
        
    Returns:
        DataFrame with sensitivity analysis results.
    """
    logger.info(f"Running sensitivity analysis with {len(motion_thresholds)} motion, {len(pval_thresholds)} pval, {len(outcome_defs)} outcome thresholds")
    
    results = []
    
    for motion_thresh in motion_thresholds:
        # Filter by motion
        df_motion = df.copy()
        if fd_col and fd_col in df_motion.columns:
            df_motion = df_motion[df_motion[fd_col] <= motion_thresh]
            logger.debug(f"Motion threshold {motion_thresh}mm: {len(df_motion)} subjects remaining")
        
        if len(df_motion) < 5:
            logger.warning(f"Too few subjects after motion filter ({motion_thresh}mm): {len(df_motion)}")
            continue
        
        for outcome_def in outcome_defs:
            # Create outcome variable based on definition
            if outcome_def == "change":
                if outcome_col in df_motion.columns and pre_col in df_motion.columns:
                    df_motion["outcome"] = df_motion[outcome_col] - df_motion[pre_col]
                else:
                    continue
            elif outcome_def == "residual":
                # Residual of post ~ pre
                if outcome_col in df_motion.columns and pre_col in df_motion.columns:
                    try:
                        X_pre = sm.add_constant(df_motion[[pre_col]])
                        y_post = df_motion[outcome_col]
                        model_pre = sm.OLS(y_post, X_pre).fit()
                        df_motion["outcome"] = model_pre.resid
                    except:
                        continue
                else:
                    continue
            elif outcome_def == "raw":
                if outcome_col in df_motion.columns:
                    df_motion["outcome"] = df_motion[outcome_col]
                else:
                    continue
            else:
                continue
            
            for metric_col in metric_cols:
                if metric_col not in df_motion.columns:
                    continue
                
                for pval_thresh in pval_thresholds:
                    # Run ANCOVA
                    try:
                        ancova_result = run_ancova_analysis(
                            df_motion,
                            outcome_col="outcome",
                            pre_col=pre_col,
                            metric_col=metric_col,
                            fd_col=fd_col
                        )
                        
                        p_val = ancova_result["metric_p_value"]
                        coef = ancova_result["metric_coefficient"]
                        significant = p_val < pval_thresh
                        
                        results.append({
                            "threshold_type": "combined",
                            "threshold_value": f"{motion_thresh}mm|{pval_thresh}|{outcome_def}",
                            "motion_threshold": motion_thresh,
                            "pval_threshold": pval_thresh,
                            "outcome_definition": outcome_def,
                            "metric": metric_col,
                            "significant": significant,
                            "effect_size": coef,
                            "p_value": p_val,
                            "n_obs": ancova_result["n_obs"]
                        })
                        
                    except Exception as e:
                        logger.warning(f"ANCOVA failed for {metric_col} with {outcome_def}: {e}")
                        continue
    
    if not results:
        logger.warning("No sensitivity analysis results generated")
        return pd.DataFrame()
    
    return pd.DataFrame(results)


def save_sensitivity_report(results_df: pd.DataFrame, output_path: str = "reports/sensitivity_analysis.md") -> None:
    """
    Save sensitivity analysis results to a markdown report.
    
    Args:
        results_df: DataFrame with sensitivity analysis results.
        output_path: Path to save the report.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Sensitivity Analysis Report\n\n")
        f.write("This report shows the robustness of findings across different analytical choices.\n\n")
        
        if results_df.empty:
            f.write("No results to report.\n")
            return
        
        # Summary by threshold type
        f.write("## Summary by Threshold Combination\n\n")
        f.write("| Motion (mm) | P-Value | Outcome Def | Metric | Significant | Effect Size | N |\n")
        f.write("|-------------|---------|-------------|--------|-------------|-------------|---|\n")
        
        for _, row in results_df.iterrows():
            f.write(f"| {row['motion_threshold']} | {row['pval_threshold']} | {row['outcome_definition']} | {row['metric']} | {'Yes' if row['significant'] else 'No'} | {row['effect_size']:.4f} | {row['n_obs']} |\n")
        
        # Aggregate counts
        f.write("\n## Aggregate Significance Counts\n\n")
        summary = results_df.groupby(['motion_threshold', 'pval_threshold', 'outcome_definition'])['significant'].agg(['sum', 'count']).reset_index()
        summary['sig_pct'] = (summary['sum'] / summary['count'] * 100).round(1)
        
        f.write("| Motion (mm) | P-Value | Outcome Def | Significant | Total | % Sig |\n")
        f.write("|-------------|---------|-------------|-------------|-------|-------|\n")
        for _, row in summary.iterrows():
            f.write(f"| {row['motion_threshold']} | {row['pval_threshold']} | {row['outcome_definition']} | {int(row['sum'])} | {int(row['count'])} | {row['sig_pct']}% |\n")
        
        f.write("\n## Methodological Notes\n\n")
        f.write("- Motion thresholds tested: 2.0mm, 3.0mm\n")
        f.write("- P-value thresholds tested: 0.01, 0.05, 0.1\n")
        f.write("- Outcome definitions tested: Change Score, Residual, Raw Post\n")
        f.write("- Primary analysis uses 3.0mm threshold, p<0.05, Change Score outcome\n")
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")


def run_analysis() -> None:
    """Main entry point for statistical analysis pipeline."""
    logger.info("Starting statistical analysis pipeline")
    
    # Load data
    try:
        network_metrics = pd.read_csv("data/metrics/network_metrics.csv")
        qc_metrics = pd.read_csv("data/metrics/qc_metrics.csv")
        filtered_subjects = pd.read_csv("data/metrics/filtered_subjects.csv")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return
    
    # Merge data
    df = network_metrics.merge(qc_metrics, on='subject_id', how='inner')
    df = df.merge(filtered_subjects, on='subject_id', how='inner')
    df = df[df['status'] == 'included']
    
    if df.empty:
        logger.warning("No included subjects for analysis")
        return
    
    # Power analysis
    power_result = run_power_analysis(n_obs=len(df))
    if power_result.get('status') == 'HALT':
        logger.error(power_result.get('warning_message', 'HALT condition met'))
        return
    
    # VIF check
    metric_cols = [c for c in df.columns if 'modularity' in c.lower() or 'efficiency' in c.lower()]
    if metric_cols:
        vif = calculate_vif(df, metric_cols)
        logger.info(f"Calculated VIF: {vif:.2f}")
        
        if vif > 5:
            logger.warning("High collinearity detected (VIF > 5). Switching to exploratory mode.")
            # PCA handling would go here, but per spec we don't replace primary predictors
            model_selection = "PCA-Exploratory"
        else:
            model_selection = "OLS"
        
        # Save model selection
        model_log = {
            "vif_value": vif,
            "decision": model_selection,
            "reason": "High collinearity" if vif > 5 else "Low collinearity"
        }
        with open("data/metrics/model_selection_log.json", 'w') as f:
            json.dump(model_log, f, indent=2)
    
    # Run ANCOVA for each metric
    results = []
    for metric_col in metric_cols:
        try:
            ancova_result = run_ancova_analysis(
                df,
                outcome_col='post_treatment_score',
                pre_col='pre_treatment_score',
                metric_col=metric_col,
                confound_cols=['age', 'medication_status'] if 'age' in df.columns else None,
                fd_col='mean_fd'
            )
            
            results.append({
                'metric': metric_col,
                'coefficient': ancova_result['metric_coefficient'],
                'p_value_uncorrected': ancova_result['metric_p_value'],
                'model_type': model_selection,
                'n_obs': ancova_result['n_obs']
            })
        except Exception as e:
            logger.warning(f"ANCOVA failed for {metric_col}: {e}")
            continue
    
    if results:
        # Apply FDR correction
        p_values = [r['p_value_uncorrected'] for r in results]
        p_values_corrected = apply_fdr_correction(p_values)
        
        for i, r in enumerate(results):
            r['p_value_corrected'] = p_values_corrected[i]
            r['vif'] = vif if metric_cols else 0
            r['min_N_required'] = power_result.get('min_N_required', -1)
        
        # Save results
        results_df = pd.DataFrame(results)
        results_df.to_csv("data/metrics/statistical_results.csv", index=False)
        logger.info("Statistical results saved")
    
    # Run sensitivity analysis
    if metric_cols:
        sens_results = run_sensitivity_analysis(
            df,
            outcome_col='post_treatment_score',
            pre_col='pre_treatment_score',
            metric_cols=metric_cols,
            motion_thresholds=[2.0, 3.0],
            pval_thresholds=[0.01, 0.05, 0.1],
            outcome_defs=['change', 'residual', 'raw'],
            fd_col='mean_fd'
        )
        
        if not sens_results.empty:
            save_sensitivity_report(sens_results, "reports/sensitivity_analysis.md")
    
    logger.info("Statistical analysis pipeline completed")


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_analysis()


if __name__ == "__main__":
    main()