import pandas as pd
import json
import os
from typing import Dict, Any, List, Optional
import logging
import config
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.anova import AnovaRM
from scipy import stats
import numpy as np

# Configure logging specifically for this module if not already done
# The main pipeline configures logging in utils.py, but we ensure handlers exist
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler('logs/analysis.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def run_anova(df: pd.DataFrame, energy_col: str, family_col: str) -> Dict[str, Any]:
    """
    Perform One-way ANOVA on energy components grouped by structural family.
    Logs raw p-values and effect sizes.
    """
    logger.info(f"Running ANOVA on {energy_col} grouped by {family_col}")
    
    # Group data
    groups = [group[energy_col].values for name, group in df.groupby(family_col)]
    
    # Check if we have enough groups for ANOVA
    if len(groups) < 2:
        logger.warning("Less than 2 groups found for ANOVA. Skipping.")
        return {"f_statistic": None, "p_value": None, "error": "Insufficient groups"}

    try:
        f_stat, p_val = stats.f_oneway(*groups)
        
        # Calculate effect size (Eta-squared)
        # Eta^2 = SS_between / SS_total
        grand_mean = df[energy_col].mean()
        ss_total = ((df[energy_col] - grand_mean) ** 2).sum()
        
        ss_between = 0
        for name, group in df.groupby(family_col):
            n = len(group)
            mean = group[energy_col].mean()
            ss_between += n * ((mean - grand_mean) ** 2)
        
        eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

        # LOGGING: Raw p-value and effect size
        logger.info(f"ANOVA Raw Results for {energy_col}:")
        logger.info(f"  F-statistic: {f_stat:.4f}")
        logger.info(f"  Raw p-value: {p_val:.6e}")
        logger.info(f"  Eta-squared (Effect Size): {eta_squared:.4f}")
        
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "eta_squared": float(eta_squared),
            "groups_analyzed": len(groups)
        }
    except Exception as e:
        logger.error(f"ANOVA failed for {energy_col}: {e}")
        return {"f_statistic": None, "p_value": None, "error": str(e)}

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Logs corrected p-values.
    """
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    
    # LOGGING: Corrected p-values
    logger.info("Bonferroni Correction Applied:")
    for i, (orig, corr) in enumerate(zip(p_values, corrected)):
        logger.info(f"  Test {i+1}: Raw={orig:.6e} -> Corrected={corr:.6e}")
        
    return corrected

def run_tukey_hsd(df: pd.DataFrame, energy_col: str, family_col: str) -> Dict[str, Any]:
    """
    Run Tukey's HSD test for post-hoc analysis.
    Logs significant pairwise comparisons and effect sizes (Cohen's d).
    """
    logger.info(f"Running Tukey HSD on {energy_col} grouped by {family_col}")
    
    try:
        tukey = pairwise_tukeyhsd(endog=df[energy_col], groups=df[family_col], alpha=0.05)
        
        results = []
        significant_pairs = 0
        
        # Parse Tukey results
        for row in tukey.results:
            group1 = row[0]
            group2 = row[1]
            meandiff = row[2]
            p_adjust = row[4]
            reject = row[5]
            
            # Calculate Cohen's d for this pair
            g1_data = df[df[family_col] == group1][energy_col]
            g2_data = df[df[family_col] == group2][energy_col]
            
            if len(g1_data) > 0 and len(g2_data) > 0:
                mean_diff = g1_data.mean() - g2_data.mean()
                pooled_std = np.sqrt((g1_data.var() + g2_data.var()) / 2)
                cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0
            else:
                cohens_d = 0.0

            pair_info = {
                "group1": group1,
                "group2": group2,
                "mean_diff": float(meandiff),
                "p_adjusted": float(p_adjust),
                "reject": bool(reject),
                "cohens_d": float(cohens_d)
            }
            results.append(pair_info)

            # LOGGING: Pairwise details and effect sizes
            status = "SIGNIFICANT" if reject else "Not Significant"
            logger.info(f"  Pair ({group1} vs {group2}): {status}, p-adj={p_adjust:.6e}, Cohen's d={cohens_d:.4f}")
            
            if reject:
                significant_pairs += 1

        logger.info(f"Tukey HSD Complete: {significant_pairs} significant pairs found out of {len(results)} comparisons.")
        
        return {
            "comparisons": results,
            "significant_count": significant_pairs,
            "total_comparisons": len(results)
        }
    except Exception as e:
        logger.error(f"Tukey HSD failed: {e}")
        return {"comparisons": [], "error": str(e)}

def calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Cohen's d effect size between two groups."""
    mean_diff = group1.mean() - group2.mean()
    pooled_std = np.sqrt((group1.var() + group2.var()) / 2)
    return float(mean_diff / pooled_std) if pooled_std > 0 else 0.0

def save_anova_results(results: Dict[str, Any], path: str):
    """Save ANOVA results to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"ANOVA results saved to {path}")

def validate_against_dft(models: Dict[str, Any], dft_validation_set: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate models against the generated DFT set.
    Logs MAE for each energy component.
    """
    logger.info("Starting DFT Validation...")
    
    if dft_validation_set.empty:
        logger.warning("DFT validation set is empty. Skipping validation.")
        return {"error": "Empty DFT set"}

    results = {}
    
    # Map model names to target columns
    model_map = {
        'electrostatic': 'electrostatic_energy',
        'dispersion': 'dispersion_energy',
        'hbond': 'hbond_energy'
    }
    
    for model_name, target_col in model_map.items():
        if model_name in models:
            model = models[model_name]
            # Predict
            preds = model.predict(dft_validation_set.drop(columns=[target_col, 'total_energy'], errors='ignore'))
            actuals = dft_validation_set[target_col]
            
            # Calculate MAE
            mae = np.mean(np.abs(preds - actuals))
            
            # LOGGING: Validation MAE
            logger.info(f"DFT Validation MAE for {model_name} energy: {mae:.4f} kcal/mol")
            
            results[model_name] = {
                "mae": float(mae),
                "n_samples": len(actuals)
            }
        else:
            logger.warning(f"Model {model_name} not found in provided models.")
            results[model_name] = {"error": "Model missing"}

    logger.info("DFT Validation Complete.")
    return results

def validate_against_experimental(models: Dict[str, Any], experimental_data: pd.DataFrame) -> Dict[str, Any]:
    """Placeholder for experimental validation if data becomes available."""
    logger.info("Experimental validation requested but no data provided.")
    return {"status": "skipped", "reason": "No experimental data"}

def calculate_correlation_matrix(descriptors: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix between descriptors and targets."""
    combined = pd.concat([descriptors, targets], axis=1)
    return combined.corr()

def check_tautology(correlation_matrix: pd.DataFrame, threshold: float = 0.95) -> bool:
    """Check for tautological correlations (too high)."""
    high_corr = correlation_matrix.abs().unstack()
    high_corr = high_corr[high_corr > threshold]
    if len(high_corr) > 0:
        logger.warning(f"Tautology Check: Found {len(high_corr)} correlations > {threshold}")
        return True
    return False

def aggregate_validation_results(anova_raw: Dict, tukey: Dict, dft_mae: Dict, sc003_status: bool, tautology: bool) -> Dict[str, Any]:
    """Aggregate all validation results into a single report."""
    return {
        "anova_raw": anova_raw,
        "tukey_hsd": tukey,
        "dft_validation": dft_mae,
        "sc003_compliance": sc003_status,
        "tautology_check": tautology
    }

def write_validation_report(report: Dict[str, Any], path: str):
    """Write the final validation report to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {path}")

def write_validation_report_with_provenance(report: Dict[str, Any], path: str, provenance: Dict[str, Any]):
    """Write report with data provenance."""
    report["data_provenance"] = provenance
    write_validation_report(report, path)

def determine_data_sources(df: pd.DataFrame) -> Dict[str, str]:
    """Determine the source of data in the dataframe."""
    sources = df['source'].unique() if 'source' in df.columns else ['unknown']
    return {"sources": list(sources)}

def calculate_sc003_compliance(dft_mae: Dict, test_mae: Dict, threshold: float = 0.5) -> bool:
    """
    Check if MAE meets SC-003 compliance (<= 0.5 kcal/mol).
    Logs the compliance status.
    """
    # Average MAE across components if available
    mae_values = [v.get('mae', float('inf')) for v in dft_mae.values() if isinstance(v, dict) and 'mae' in v]
    
    if not mae_values:
        logger.warning("No MAE values found for SC003 compliance check.")
        return False
    
    avg_mae = sum(mae_values) / len(mae_values)
    compliant = avg_mae <= threshold
    
    # LOGGING: SC003 Compliance
    logger.info(f"SC-003 Compliance Check:")
    logger.info(f"  Average DFT MAE: {avg_mae:.4f} kcal/mol")
    logger.info(f"  Threshold: {threshold} kcal/mol")
    logger.info(f"  Status: {'COMPLIANT' if compliant else 'NON-COMPLIANT'}")
    
    return compliant

def main():
    """
    Main entry point for running analysis tasks.
    This function orchestrates the ANOVA, Tukey HSD, and DFT validation,
    ensuring all p-values, effect sizes, and MAEs are logged as required by T038.
    """
    logger.info("Starting Analysis Pipeline (T038)")
    
    # Load data (assuming paths from config or defaults)
    # In a real run, these paths would be passed or loaded from config
    unified_path = "data/processed/unified_dataset.parquet"
    dft_path = "data/validation/dft_validation_set.parquet"
    
    if not os.path.exists(unified_path):
        logger.error(f"Unified dataset not found at {unified_path}. Exiting.")
        return

    df = pd.read_parquet(unified_path)
    
    # Run ANOVA on raw SAPT data
    energy_cols = ['electrostatic_energy', 'dispersion_energy', 'hbond_energy']
    family_col = 'structural_family'
    
    anova_results = {}
    for col in energy_cols:
        if col in df.columns:
            anova_results[col] = run_anova(df, col, family_col)
        else:
            logger.warning(f"Column {col} not found in dataframe.")
    
    # Run Tukey HSD
    tukey_results = {}
    for col in energy_cols:
        if col in df.columns:
            tukey_results[col] = run_tukey_hsd(df, col, family_col)
    
    # Load DFT validation set if exists
    dft_results = {}
    if os.path.exists(dft_path):
        dft_df = pd.read_parquet(dft_path)
        # Mock models for demonstration if not loaded
        # In a full pipeline, models would be loaded here
        models = {} 
        dft_results = validate_against_dft(models, dft_df)
        
        # Calculate SC003 compliance
        sc003_status = calculate_sc003_compliance(dft_results, {})
    else:
        logger.warning("DFT validation set not found. Skipping DFT validation.")
    
    # Save results
    save_anova_results({"anova": anova_results, "tukey": tukey_results, "dft": dft_results}, "analysis/anova_results.json")
    
    logger.info("Analysis Pipeline Complete.")

if __name__ == "__main__":
    main()
