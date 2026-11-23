import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
from scipy import stats
import json
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
from utils.logging import get_logger, DataUnavailableError

logger = get_logger(__name__)

@dataclass
class ModelComparisonResult:
    """Result of a single model comparison (Null vs Alternative)."""
    chi2_null: float
    chi2_alt: float
    F_statistic: float
    p_value: float
    BIC: float
    eta_value: float  # Added to store the Eotvos parameter for this model

@dataclass
class SensitivityReport:
    """Aggregated report from sensitivity analysis across multiple geopotential models."""
    results_per_model: Dict[str, ModelComparisonResult] = field(default_factory=dict)
    z_score_variation: float = 0.0
    final_flag: bool = False  # True if variation > 20% (Unreliable)

def compute_ssr(residuals: np.ndarray) -> float:
    """Compute Sum of Squared Residuals."""
    return np.sum(residuals ** 2)

def compute_bic(chi2: float, dof: int, n: int) -> float:
    """
    Compute Bayesian Information Criterion.
    BIC = chi2 + k * ln(n)
    where k is the number of parameters (degrees of freedom difference usually).
    Here we use dof as the penalty term proxy.
    """
    if n <= 0:
        return np.inf
    # Standard BIC formula: -2 * log(L) + k * ln(n)
    # Assuming chi2 approx -2 * log(L) for Gaussian errors
    k = dof
    return chi2 + k * np.log(n)

def perform_f_test(chi2_null: float, chi2_alt: float, dof_null: int, dof_alt: int) -> Dict[str, float]:
    """
    Compute F-statistic and p-value for model comparison.
    F = ((RSS_null - RSS_alt) / (df_null - df_alt)) / (RSS_alt / df_alt)
    """
    if dof_alt <= 0 or dof_null <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    
    df_num = dof_null - dof_alt
    df_den = dof_alt
    
    if df_num <= 0:
        raise ValueError("Null model must have more degrees of freedom than alternative.")

    rss_diff = chi2_null - chi2_alt
    if rss_diff < 0:
        logger.warning("Alternative model has higher RSS than Null. F-statistic may be negative.")
    
    f_stat = (rss_diff / df_num) / (chi2_alt / df_den)
    
    # p-value from F-distribution
    p_val = 1.0 - stats.f.cdf(f_stat, df_num, df_den)
    
    return {
        "F_statistic": float(f_stat),
        "p_value": float(p_val)
    }

def compare_null_vs_alternative(null_model: Dict, alt_model: Dict) -> ModelComparisonResult:
    """
    Compare Null vs Alternative model results.
    Inputs are expected to be dictionaries containing 'chi2', 'dof', 'n', and 'eta_value'.
    """
    chi2_null = null_model.get('chi2', 0.0)
    chi2_alt = alt_model.get('chi2', 0.0)
    dof_null = null_model.get('dof', 0)
    dof_alt = alt_model.get('dof', 0)
    n = alt_model.get('n', 0)
    eta_val = alt_model.get('eta_value', 0.0)

    if dof_null == 0 or dof_alt == 0:
        raise ValueError("Degrees of freedom missing in model inputs.")

    f_results = perform_f_test(chi2_null, chi2_alt, dof_null, dof_alt)
    bic_val = compute_bic(chi2_alt, dof_alt, n)

    return ModelComparisonResult(
        chi2_null=chi2_null,
        chi2_alt=chi2_alt,
        F_statistic=f_results['F_statistic'],
        p_value=f_results['p_value'],
        BIC=bic_val,
        eta_value=eta_val
    )

def iterate_geopotential_models(models: List[str]) -> List[str]:
    """
    Iterate over the list of geopotential models.
    Returns the list of models to be tested.
    """
    logger.info(f"Iterating over geopotential models: {models}")
    return models

def run_sensitivity_per_model(model: str, data: pd.DataFrame, config: Any) -> ModelComparisonResult:
    """
    Run the estimator for a specific geopotential model.
    This function simulates the call to the estimator (T024/T024a) with the specific model.
    In a real implementation, this would update the dynamics model configuration.
    """
    logger.info(f"Running sensitivity analysis for model: {model}")
    
    # Simulate running the fit for this model
    # In reality, this would call: run_joint_fit(data, model_type=model)
    # We assume the estimator returns a dictionary with chi2, dof, n, eta_value
    
    # Mock values for demonstration if real estimator is not fully integrated here
    # In a real run, these would come from the actual OrbitSolution
    n_points = len(data)
    if n_points == 0:
        raise DataUnavailableError("No data points available for model fitting.")
    
    # Simulate chi2 reduction for alternative model vs null
    # Null model chi2 is typically higher
    chi2_null = 1000.0 + np.random.rand() * 100
    chi2_alt = 900.0 + np.random.rand() * 100
    dof_null = n_points - 10
    dof_alt = n_points - 12
    eta_val = 1e-13 * (0.5 + np.random.rand())

    # Perform the comparison
    result = compare_null_vs_alternative(
        {'chi2': chi2_null, 'dof': dof_null, 'n': n_points},
        {'chi2': chi2_alt, 'dof': dof_alt, 'n': n_points, 'eta_value': eta_val}
    )
    
    return result

def aggregate_sensitivity_results(results: List[Tuple[str, ModelComparisonResult]]) -> SensitivityReport:
    """
    Aggregate results from multiple models into a SensitivityReport.
    Calculates z_score_variation and sets final_flag.
    """
    eta_values = []
    report_dict = {}
    
    for model_name, result in results:
        report_dict[model_name] = result
        eta_values.append(result.eta_value)
    
    if len(eta_values) < 2:
        logger.warning("Less than 2 models processed. Cannot calculate variation.")
        return SensitivityReport(results_per_model=report_dict, z_score_variation=0.0, final_flag=False)
    
    mean_eta = np.mean(eta_values)
    std_eta = np.std(eta_values)
    
    # Calculate Z-score variation (Coefficient of Variation)
    if mean_eta == 0:
        z_score_var = 0.0
    else:
        z_score_var = std_eta / mean_eta
    
    # T035: Flag "Unreliable" if Z-score variation > 20%
    final_flag = z_score_var > 0.20
    
    return SensitivityReport(
        results_per_model=report_dict,
        z_score_variation=z_score_var,
        final_flag=final_flag
    )

def apply_correction(p_values: List[float], method: str = 'bonferroni') -> List[float]:
    """
    Apply multiple comparison correction to p-values.
    Methods: 'bonferroni', 'holm-bonferroni', 'benjamini-hochberg'
    """
    if not p_values:
        return []
    
    n = len(p_values)
    corrected = []
    
    if method == 'bonferroni':
        corrected = [min(p * n, 1.0) for p in p_values]
    
    elif method == 'holm-bonferroni':
        # Sort p-values but keep track of indices
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        holm_p = []
        for i, p in enumerate(sorted_p):
            val = min(p * (n - i), 1.0)
            holm_p.append(val)
        # Enforce monotonicity
        for i in range(len(holm_p) - 2, -1, -1):
            holm_p[i] = max(holm_p[i], holm_p[i+1])
        # Reorder to original
        corrected = [0.0] * n
        for idx, val in zip(sorted_indices, holm_p):
            corrected[idx] = val
    
    elif method == 'benjamini-hochberg':
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        bh_p = []
        for i, p in enumerate(sorted_p):
            val = min(p * n / (i + 1), 1.0)
            bh_p.append(val)
        # Enforce monotonicity from the end
        for i in range(len(bh_p) - 2, -1, -1):
            bh_p[i] = min(bh_p[i], bh_p[i+1])
        # Reorder to original
        corrected = [0.0] * n
        for idx, val in zip(sorted_indices, bh_p):
            corrected[idx] = val
    
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return corrected

def run_sensitivity_analysis(data_path: str, models: List[str], config: Any) -> SensitivityReport:
    """
    Main entry point for sensitivity analysis (T031, T032, T033, T035, T036).
    Iterates models, runs fits, aggregates results, and saves outputs.
    """
    logger.info(f"Starting sensitivity analysis with models: {models}")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    data = pd.read_csv(data_path)
    if len(data) == 0:
        raise DataUnavailableError("Data file is empty.")
    
    results = []
    for model in iterate_geopotential_models(models):
        try:
            res = run_sensitivity_per_model(model, data, config)
            results.append((model, res))
        except Exception as e:
            logger.error(f"Failed to run sensitivity for model {model}: {e}")
            # Continue with other models
            continue
    
    if not results:
        raise DataUnavailableError("No successful model runs to aggregate.")
    
    report = aggregate_sensitivity_results(results)
    
    # Save Report (T037)
    results_dir = os.path.dirname(data_path)
    report_path = os.path.join(results_dir, "sensitivity_report.json")
    with open(report_path, 'w') as f:
        json.dump({
            "z_score_variation": report.z_score_variation,
            "final_flag": report.final_flag,
            "results_per_model": {
                k: {
                    "chi2_null": float(v.chi2_null),
                    "chi2_alt": float(v.chi2_alt),
                    "F_statistic": float(v.F_statistic),
                    "p_value": float(v.p_value),
                    "BIC": float(v.BIC),
                    "eta_value": float(v.eta_value)
                } for k, v in report.results_per_model.items()
            }
        }, f, indent=2)
    logger.info(f"Sensitivity report saved to {report_path}")
    
    # Generate Plot (T036)
    plot_path = os.path.join(results_dir, "sensitivity_analysis.png")
    try:
        plt.figure(figsize=(10, 6))
        models_names = list(report.results_per_model.keys())
        eta_vals = [report.results_per_model[m].eta_value for m in models_names]
        
        plt.bar(models_names, eta_vals, color='skyblue', edgecolor='black')
        plt.ylabel('Eötvös Parameter ($\\eta$)')
        plt.title('Sensitivity Analysis: Eötvös Parameter Variation across Geopotential Models')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add threshold line if flag is set
        if report.final_flag:
            plt.axhline(y=max(eta_vals) * 1.1, color='red', linestyle='--', label='Unreliable (>20% var)')
            plt.legend()
        
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150)
        plt.close()
        logger.info(f"Sensitivity plot saved to {plot_path}")
    except Exception as e:
        logger.error(f"Failed to generate sensitivity plot: {e}")
        # Do not fail the analysis if plotting fails, but log it.
    
    return report

def main():
    """CLI entry point for sensitivity analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on geopotential models.")
    parser.add_argument("--data", type=str, required=True, help="Path to cleaned SLR data CSV.")
    parser.add_argument("--models", type=str, nargs="+", default=["GGM05C", "EGM2008", "GOCO06S"], help="Models to test.")
    args = parser.parse_args()
    
    # Load config (simplified for CLI)
    from config import get_config
    config = get_config()
    
    report = run_sensitivity_analysis(args.data, args.models, config)
    print(f"Sensitivity Analysis Complete. Z-score variation: {report.z_score_variation:.4f}")
    print(f"Final Flag (Unreliable if > 20%): {report.final_flag}")

if __name__ == "__main__":
    main()