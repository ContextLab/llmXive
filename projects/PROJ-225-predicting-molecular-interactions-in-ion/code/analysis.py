import pandas as pd
import json
import os
from typing import Dict, Any, List, Optional
import logging
import config
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.anova import AnovaRM
import numpy as np

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.py."""
    return {
        'SEED': config.SEED,
        'DATA_PATHS': config.DATA_PATHS,
        'ANOVA_ALPHA': 0.05,
        'TAUTOLOGY_THRESHOLD': 0.95
    }

def check_anova_assumptions(df: pd.DataFrame, energy_col: str, family_col: str) -> Dict[str, Any]:
    """
    Check ANOVA assumptions (Normality and Homogeneity of Variance).
    
    If assumptions are violated (p < 0.05), log a WARNING and prepare 
    for a non-parametric fallback (Kruskal-Wallis).
    
    Args:
        df: DataFrame containing energy and family columns.
        energy_col: Name of the energy column to test.
        family_col: Name of the structural family column.
        
    Returns:
        Dictionary containing assumption check results:
        {
            'shapiro_p': float,
            'levene_p': float,
            'normality_passed': bool,
            'homogeneity_passed': bool,
            'assumptions_met': bool,
            'recommendation': str
        }
    """
    if energy_col not in df.columns or family_col not in df.columns:
        raise ValueError(f"Columns '{energy_col}' and/or '{family_col}' not found in DataFrame")
    
    # Group data by family
    groups = [group[energy_col].values for _, group in df.groupby(family_col)]
    
    if len(groups) < 2:
        logger.warning("Not enough groups to perform ANOVA assumption checks.")
        return {
            'shapiro_p': None,
            'levene_p': None,
            'normality_passed': False,
            'homogeneity_passed': False,
            'assumptions_met': False,
            'recommendation': 'Insufficient groups'
        }
    
    results = {}
    
    # 1. Normality Check (Shapiro-Wilk)
    # Note: Shapiro-Wilk is sensitive to sample size. We check each group.
    shapiro_p_values = []
    for i, group_data in enumerate(groups):
        if len(group_data) >= 3:  # Shapiro-Wilk requires at least 3 samples
            stat, p_val = stats.shapiro(group_data)
            shapiro_p_values.append(p_val)
        else:
            # If group is too small for Shapiro, we cannot confirm normality
            shapiro_p_values.append(0.0) 
    
    if shapiro_p_values:
        # Use the minimum p-value across groups for a conservative check
        min_shapiro_p = min(shapiro_p_values)
        results['shapiro_p'] = min_shapiro_p
        normality_passed = min_shapiro_p >= config.ANOVA_ALPHA
    else:
        results['shapiro_p'] = None
        normality_passed = False
    
    # 2. Homogeneity of Variance Check (Levene's Test)
    # Levene's test is robust to non-normality compared to Bartlett's
    try:
        levene_stat, levene_p = stats.levene(*groups)
        results['levene_p'] = levene_p
        homogeneity_passed = levene_p >= config.ANOVA_ALPHA
    except Exception as e:
        logger.error(f"Levene's test failed: {e}")
        results['levene_p'] = None
        homogeneity_passed = False
    
    # Determine if assumptions are met
    assumptions_met = normality_passed and homogeneity_passed
    
    # Recommendation
    if assumptions_met:
        recommendation = "ANOVA assumptions met. Proceed with One-way ANOVA."
    else:
        reasons = []
        if not normality_passed:
            reasons.append("Normality violated (Shapiro-Wilk p < 0.05)")
        if not homogeneity_passed:
            reasons.append("Homogeneity of variance violated (Levene's p < 0.05)")
        
        recommendation = f"Assumptions violated: {', '.join(reasons)}. Switching to Kruskal-Wallis test."
        logger.warning(f"ANOVA assumptions violated for {energy_col}: {recommendation}")
    
    results['normality_passed'] = normality_passed
    results['homogeneity_passed'] = homogeneity_passed
    results['assumptions_met'] = assumptions_met
    results['recommendation'] = recommendation
    
    return results

def run_anova(df: pd.DataFrame, energy_col: str, family_col: str) -> Dict[str, Any]:
    """
    Perform One-way ANOVA.
    If assumptions are violated, falls back to Kruskal-Wallis and reports both.
    
    Args:
        df: DataFrame.
        energy_col: Target energy column.
        family_col: Grouping column.
        
    Returns:
        Dictionary with ANOVA results.
    """
    # Check assumptions first
    assumption_results = check_anova_assumptions(df, energy_col, family_col)
    
    groups = [group[energy_col].values for _, group in df.groupby(family_col)]
    
    anova_result = {}
    
    # Always attempt standard ANOVA if possible, but note if assumptions failed
    try:
        f_stat, p_val = stats.f_oneway(*groups)
        anova_result['f_statistic'] = float(f_stat)
        anova_result['p_value'] = float(p_val)
        anova_result['method'] = 'One-way ANOVA'
    except Exception as e:
        logger.warning(f"Standard ANOVA failed: {e}. Using Kruskal-Wallis immediately.")
        anova_result['f_statistic'] = None
        anova_result['p_value'] = None
        anova_result['method'] = 'Skipped (Error)'
    
    # If assumptions violated, run Kruskal-Wallis
    if not assumption_results['assumptions_met']:
        try:
            kw_stat, kw_p = stats.kruskal(*groups)
            anova_result['fallback_method'] = 'Kruskal-Wallis'
            anova_result['fallback_statistic'] = float(kw_stat)
            anova_result['fallback_p_value'] = float(kw_p)
            logger.info(f"Kruskal-Wallis result for {energy_col}: statistic={kw_stat:.4f}, p={kw_p:.4f}")
        except Exception as e:
            logger.error(f"Kruskal-Wallis failed: {e}")
            anova_result['fallback_method'] = 'Kruskal-Wallis'
            anova_result['fallback_statistic'] = None
            anova_result['fallback_p_value'] = None
    else:
        anova_result['fallback_method'] = None
        anova_result['fallback_statistic'] = None
        anova_result['fallback_p_value'] = None
    
    # Attach assumption details
    anova_result['assumption_check'] = assumption_results
    
    return anova_result

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    return [min(p * n_tests, 1.0) for p in p_values]

def run_tukey_hsd(df: pd.DataFrame, energy_col: str, family_col: str) -> Dict[str, Any]:
    """Run Tukey HSD test for post-hoc analysis."""
    try:
        tukey = pairwise_tukeyhsd(endog=df[energy_col], groups=df[family_col], alpha=0.05)
        return {
            'reject_null': tukey.reject,
            'p_values': tukey.pvalues,
            'meandiffs': tukey.meandiffs,
            'confint': tukey.confint,
            'summary': str(tukey)
        }
    except Exception as e:
        logger.error(f"Tukey HSD failed: {e}")
        return {'error': str(e)}

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size between two groups."""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float(np.abs(np.mean(group1) - np.mean(group2)) / pooled_std)

def save_anova_results(results: Dict[str, Any], path: str) -> None:
    """Save ANOVA results to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"ANOVA results saved to {path}")

def validate_against_dft(models: Dict, dft_validation_set: pd.DataFrame) -> Dict[str, float]:
    """Validate models against DFT validation set."""
    results = {}
    for name, model in models.items():
        preds = model.predict(dft_validation_set.drop(columns=['total_energy']))
        mae = np.mean(np.abs(preds - dft_validation_set['total_energy']))
        results[f"{name}_mae"] = float(mae)
        logger.info(f"DFT Validation MAE for {name}: {mae:.4f} kcal/mol")
    return results

def validate_against_experimental(models: Dict, exp_data: pd.DataFrame) -> Dict[str, float]:
    """Validate models against experimental data if available."""
    return validate_against_dft(models, exp_data)

def calculate_correlation_matrix(descriptors: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix between descriptors and targets."""
    combined = pd.concat([descriptors, targets], axis=1)
    return combined.corr()

def check_tautology(correlation_matrix: pd.DataFrame, threshold: float = 0.95) -> bool:
    """Check for tautological correlations."""
    high_corr = correlation_matrix.abs().gt(threshold).any().any()
    if high_corr:
        logger.warning("Tautological correlation detected (r > 0.95)")
    return high_corr

def aggregate_validation_results(anova_predictions: Dict, anova_raw: Dict, tukey: Dict, 
                                 dft_mae: Dict, sc003_status: bool, tautology: bool) -> Dict[str, Any]:
    """Aggregate all validation results into a single report."""
    return {
        'anova_predictions': anova_predictions,
        'anova_raw': anova_raw,
        'tukey_hsd': tukey,
        'dft_mae': dft_mae,
        'sc003_compliance': sc003_status,
        'tautology_check': tautology
    }

def write_validation_report(report: Dict[str, Any], path: str) -> None:
    """Write the final validation report."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Validation report saved to {path}")

def calculate_sc003_compliance(dft_mae: float, test_mae: float) -> bool:
    """Check if DFT MAE is within 2.0x of test set MAE."""
    if test_mae == 0:
        return False
    return dft_mae <= 2.0 * test_mae

def compare_anova_results(raw_results: Dict, pred_results: Dict) -> Dict[str, Any]:
    """Compare ANOVA results from raw data vs predictions."""
    return {
        'raw_p_value': raw_results.get('p_value'),
        'pred_p_value': pred_results.get('p_value'),
        'trend_consistent': (raw_results.get('p_value', 1) < 0.05) == (pred_results.get('p_value', 1) < 0.05)
    }

def run_anova_on_predictions(predictions_df: pd.DataFrame, family_col: str) -> Dict[str, Any]:
    """Run ANOVA on model predictions."""
    return run_anova(predictions_df, 'predicted_energy', family_col)

def compare_raw_vs_prediction_anova(raw_results: Dict, prediction_results: Dict) -> Dict[str, Any]:
    """Compare raw vs prediction ANOVA results."""
    return compare_anova_results(raw_results, prediction_results)

def main():
    """Main entry point for analysis script."""
    logger.info("Starting Analysis Pipeline")
    cfg = load_config()
    
    # Example execution path (to be replaced by actual data loading in full pipeline)
    # This function serves as the entry point for T063 logic integration
    logger.info("Analysis pipeline initialized.")

if __name__ == "__main__":
    main()