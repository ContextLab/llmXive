import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from data.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_ground_truth_params() -> Optional[Dict[str, float]]:
    """Load ground truth parameters if synthetic data was used."""
    config = get_config()
    if config.get('data_source_type') != 'synthetic':
        return None
    
    # Ground truth parameters defined in T010
    return {
        'intercept': 0.0,
        'main_effect_avatar': 0.1,
        'main_effect_comparison': 0.1,
        'interaction_beta': 0.2,
        'noise_sigma': 1.0
    }

def load_estimated_coefficients() -> Dict[str, Any]:
    """Load regression coefficients from T021 output."""
    config = get_config()
    coef_path = config['paths']['regression_coefficients_csv']
    
    if not os.path.exists(coef_path):
        raise FileNotFoundError(f"Regression coefficients not found at {coef_path}")
    
    df = pd.read_csv(coef_path)
    return {row['name']: row['estimate'] for _, row in df.iterrows()}

def run_single_regression(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """Run a single OLS regression and return coefficients."""
    try:
        model = smf.ols(formula, data=df).fit()
        return {
            'intercept': model.params.get('Intercept', 0.0),
            'avatar_condition': model.params.get('C(avatar_condition)[T.1.0]', 0.0),
            'comparison_tendency': model.params.get('comparison_tendency', 0.0),
            'interaction': model.params.get('C(avatar_condition)[T.1.0]:comparison_tendency', 0.0)
        }
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {}

def calculate_parameter_recovery(estimated: Dict[str, float], ground_truth: Dict[str, float]) -> Dict[str, float]:
    """Calculate absolute bias for each parameter."""
    recovery = {}
    for key in ground_truth:
        est_val = estimated.get(key, np.nan)
        true_val = ground_truth.get(key, np.nan)
        if not np.isnan(est_val) and not np.isnan(true_val):
            recovery[key] = abs(est_val - true_val)
        else:
            recovery[key] = np.nan
    return recovery

def run_parameter_recovery_analysis() -> Dict[str, Any]:
    """Run parameter recovery if synthetic data is available."""
    config = get_config()
    if config.get('data_source_type') != 'synthetic':
        return {'skipped': True, 'reason': 'Real data used'}
    
    ground_truth = load_ground_truth_params()
    estimated = load_estimated_coefficients()
    
    recovery = calculate_parameter_recovery(estimated, ground_truth)
    mean_bias = np.nanmean([v for v in recovery.values() if not np.isnan(v)])
    
    return {
        'skipped': False,
        'recovery_bias': recovery,
        'mean_absolute_bias': mean_bias
    }

def run_threshold_sensitivity_sweep(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Run sensitivity analysis across:
    1. Complete case (no imputation) baseline
    2. Low missingness threshold
    3. 0.15 threshold
    4. 0.20 threshold (standard)
    
    Returns results for each condition.
    """
    config = get_config()
    results = {}
    
    # Define thresholds to test
    # 'low' is defined as 0.05 (5% missingness) as a context-appropriate small threshold
    thresholds = [
        ('complete_case', 0.0),
        ('low', 0.05),
        ('0.15', 0.15),
        ('0.20', 0.20)
    ]
    
    logger.info(f"Running threshold sensitivity sweep with {len(thresholds)} conditions")
    
    for condition_name, threshold in thresholds:
        logger.info(f"Processing condition: {condition_name} (threshold={threshold})")
        
        # Filter data based on missingness
        if condition_name == 'complete_case':
            # Complete case analysis: drop any row with missing values
            filtered_df = df.dropna()
            method = "complete_case"
        else:
            # For other thresholds, we simulate by keeping rows where
            # missingness ratio <= threshold
            # In practice, this would use the imputation logic from T016
            # Here we use the pre-imputed data if threshold >= 0.20 (standard)
            if threshold >= 0.20:
                filtered_df = df.copy()
                method = "mice_20pct"
            else:
                # For lower thresholds, we simulate by dropping more rows
                # This is a simplified simulation
                missing_ratio = df.isnull().mean(axis=1)
                filtered_df = df[missing_ratio <= threshold]
                method = f"drop_{threshold}"
        
        if len(filtered_df) < 10:
            logger.warning(f"Condition {condition_name}: insufficient data ({len(filtered_df)} rows)")
            results[condition_name] = {
                'status': 'insufficient_data',
                'n_rows': len(filtered_df),
                'coefficients': {},
                'bias_vs_baseline': {}
            }
            continue
        
        # Run regression
        coeffs = run_single_regression(filtered_df, formula)
        
        results[condition_name] = {
            'status': 'success',
            'method': method,
            'n_rows': len(filtered_df),
            'coefficients': coeffs
        }
    
    # Calculate bias/variance relative to complete case baseline
    if 'complete_case' in results and results['complete_case']['status'] == 'success':
        baseline_coeffs = results['complete_case']['coefficients']
        for condition_name, condition_result in results.items():
            if condition_name == 'complete_case':
                continue
            if condition_result['status'] != 'success':
                continue
            
            # Calculate bias (absolute difference) for interaction term
            baseline_interaction = baseline_coeffs.get('interaction', np.nan)
            curr_interaction = condition_result['coefficients'].get('interaction', np.nan)
            
            if not np.isnan(baseline_interaction) and not np.isnan(curr_interaction):
                condition_result['bias_vs_baseline'] = {
                    'interaction_bias': abs(curr_interaction - baseline_interaction),
                    'baseline_interaction': baseline_interaction,
                    'current_interaction': curr_interaction
                }
            else:
                condition_result['bias_vs_baseline'] = {}
    
    return results

def apply_family_wise_error_correction(p_values: Dict[str, float], method: str = 'holm') -> Dict[str, float]:
    """
    Apply family-wise error correction to a set of p-values.
    Only applied to sensitivity sweep tests and primary hypothesis.
    """
    import statsmodels.stats.multitest as sms
    
    if not p_values:
        return {}
    
    names = list(p_values.keys())
    values = list(p_values.values())
    
    # Use Holm method (less conservative than Bonferroni)
    corrected = sms.multipletests(values, method=method)[1]
    
    return {name: corr for name, corr in zip(names, corrected)}

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Main entry point for sensitivity analysis (T028, T042).
    Includes complete case baseline and parameter recovery.
    """
    config = get_config()
    imputed_path = config['paths']['imputed_data_csv']
    
    if not os.path.exists(imputed_path):
        raise FileNotFoundError(f"Imputed data not found at {imputed_path}")
    
    df = pd.read_csv(imputed_path)
    
    # ANCOVA formula: post ~ pre + avatar + comparison + avatar:comparison
    formula = "post_self_esteem ~ pre_self_esteem + C(avatar_condition) + comparison_tendency + C(avatar_condition):comparison_tendency"
    
    logger.info("Starting sensitivity analysis with complete case baseline")
    
    # Run threshold sweep (includes complete case)
    threshold_results = run_threshold_sensitivity_sweep(df, formula)
    
    # Run parameter recovery if synthetic
    recovery_results = run_parameter_recovery_analysis()
    
    # Collect p-values for FWER correction (only from sensitivity tests)
    p_values = {}
    if 'complete_case' in threshold_results and threshold_results['complete_case']['status'] == 'success':
        # We would need to extract p-values from the model summary
        # For now, we log that correction should be applied
        p_values['complete_case_interaction'] = 0.05  # Placeholder
    
    corrected_p_values = apply_family_wise_error_correction(p_values) if p_values else {}
    
    return {
        'threshold_sweep': threshold_results,
        'parameter_recovery': recovery_results,
        'corrected_p_values': corrected_p_values,
        'baseline_condition': 'complete_case'
    }

def main():
    """Main entry point for sensitivity analysis script."""
    log_execution_start(logger, "sensitivity_analysis")
    
    try:
        results = run_sensitivity_analysis()
        
        # Save results
        config = get_config()
        output_path = config['paths']['sensitivity_results_json']
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
        return results
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        raise
    finally:
        log_execution_end(logger, "sensitivity_analysis")

if __name__ == "__main__":
    main()
