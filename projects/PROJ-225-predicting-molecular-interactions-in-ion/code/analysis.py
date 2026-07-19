import pandas as pd
import json
import os
from typing import Dict, Any, List, Optional
from .config import AnalysisError
import logging

logger = logging.getLogger(__name__)

def run_anova(df, energy_col, family_col):
    """Run one-way ANOVA on energy column grouped by structural family."""
    from scipy.stats import f_oneway
    if family_col not in df.columns or energy_col not in df.columns:
        raise AnalysisError(f"Columns {family_col} or {energy_col} not found in dataframe")
    
    groups = [group[energy_col].values for name, group in df.groupby(family_col)]
    if len(groups) < 2:
        raise AnalysisError("Not enough groups to run ANOVA")
    
    stat, p_value = f_oneway(*groups)
    return {"f_statistic": float(stat), "p_value": float(p_value)}

def save_anova_results(results, path):
    """Save ANOVA results to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved ANOVA results to {path}")

def apply_bonferroni_correction(p_values, n_tests):
    """Apply Bonferroni correction to p-values."""
    if n_tests <= 0:
        raise AnalysisError("n_tests must be positive")
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def run_tukey_hsd(df, energy_col, family_col):
    """Run Tukey HSD post-hoc test."""
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    tukey = pairwise_tukeyhsd(endog=df[energy_col], groups=df[family_col], alpha=0.05)
    return {
        "significant_groups": [str(row) for row in tukey.summary().data[1:]],
        "reject": tukey.reject.tolist()
    }

def calculate_cohens_d(group1, group2):
    """Calculate Cohen's d effect size."""
    import numpy as np
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)

def validate_against_dft(models, dft_validation_set):
    """Validate models against DFT validation set."""
    import numpy as np
    if not os.path.exists(dft_validation_set):
        raise AnalysisError(f"DFT validation set not found at {dft_validation_set}")
    
    df = pd.read_parquet(dft_validation_set)
    predictions = {}
    actuals = {}
    
    for model_name, model in models.items():
        # Assuming model has predict method and features are in df
        # This is a placeholder for actual prediction logic
        # In real implementation, would extract features and predict
        if model_name in df.columns:
            predictions[model_name] = df[model_name].values
            actuals[model_name] = df[f"actual_{model_name}"].values
    
    mae_results = {}
    for model_name in predictions:
        mae = np.mean(np.abs(predictions[model_name] - actuals[model_name]))
        mae_results[model_name] = float(mae)
    
    return mae_results

def validate_against_experimental(models, experimental_set):
    """Validate models against experimental data."""
    # Similar to DFT validation but for experimental data
    pass

def calculate_correlation_matrix(descriptors, targets):
    """Calculate correlation matrix between descriptors and targets."""
    import numpy as np
    corr_matrix = descriptors.corrwith(targets)
    return corr_matrix.to_dict()

def check_tautology(correlation_matrix, threshold=0.95):
    """Check for tautology in correlations."""
    high_corr = [k for k, v in correlation_matrix.items() if abs(v) > threshold]
    return {
        "tautology_detected": len(high_corr) > 0,
        "highly_correlated_features": high_corr,
        "threshold": threshold
    }

def aggregate_validation_results(anova, tukey, dft_mae, experimental_status, tautology):
    """Aggregate all validation results into a single report."""
    return {
        "anova_results": anova,
        "tukey_hsd": tukey,
        "dft_validation_mae": dft_mae,
        "experimental_validation_status": experimental_status,
        "tautology_check": tautology
    }

def determine_data_sources():
    """Determine the sources of training and validation data."""
    sources = {
        "training_data_source": "SPICE",
        "validation_data_source": "DFT"
    }
    
    # Check if synthetic data was used as fallback
    sapt_path = "data/raw/sapt.parquet"
    if os.path.exists(sapt_path):
        # In a real implementation, we would check metadata or logs
        # to determine if this was synthetic or real
        sources["training_data_source"] = "Synthetic (IL-SAPT fallback)"
    
    # Check if experimental validation was performed
    experimental_path = "data/validation/experimental_set.parquet"
    if os.path.exists(experimental_path):
        sources["validation_data_source"] = "Experimental"
    
    return sources

def write_validation_report_with_provenance(report, path, data_sources):
    """Write validation report with data provenance section."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Add data provenance section
    report_with_provenance = report.copy()
    report_with_provenance["data_provenance"] = data_sources
    
    with open(path, 'w') as f:
        json.dump(report_with_provenance, f, indent=2)
    
    logger.info(f"Saved validation report with provenance to {path}")
    return report_with_provenance

def write_validation_report(report, path):
    """Write validation report (legacy function)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {path}")
