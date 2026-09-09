"""
Statistical analysis module for User Story 2.
Implements multiple linear regression, VIF calculation, and associational report generation.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.constants import get_vif_threshold, get_significance_level
from utils.exceptions import CausalLanguageViolationError
from utils.cautions import scan_report_for_causal_language
from utils.logger import get_logger, log_model_fit_start, log_model_fit_success, log_model_fit_error

logger = get_logger(__name__)

# Define the standard column names expected by the pipeline
COL_TARGET = 'self_perception_score'
COL_PREDICTOR = 'perceived_social_validation'
COL_AGE = 'age'
COL_GENDER = 'gender_encoded'
COL_OFFLINE = 'offline_relationship_quality'
COL_TRAITS = 'intrinsic_traits_score'

def fit_multiple_linear_regression(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Fits a multiple linear regression model using statsmodels.
    
    Args:
        df: DataFrame containing the required columns.
        
    Returns:
        Tuple of (results object, summary dictionary)
    """
    log_model_fit_start(logger)
    
    # Define predictors
    predictors = [
        COL_PREDICTOR,
        COL_AGE,
        COL_GENDER,
        COL_OFFLINE,
        COL_TRAITS
    ]
    
    # Filter columns that actually exist in the dataframe
    available_predictors = [col for col in predictors if col in df.columns]
    
    if not available_predictors:
        raise ValueError("No predictor columns found in the dataframe.")
        
    if COL_TARGET not in df.columns:
        raise ValueError(f"Target column '{COL_TARGET}' not found in dataframe.")
    
    X = df[available_predictors]
    y = df[COL_TARGET]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X).fit()
        log_model_fit_success(logger)
        return model, {
            'predictors_used': available_predictors,
            'n_obs': len(y),
            'r_squared': model.rsquared,
            'adj_r_squared': model.rsquared_adj,
            'f_statistic': model.fvalue,
            'f_pvalue': model.f_pvalue
        }
    except Exception as e:
        log_model_fit_error(logger, str(e))
        raise

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for each predictor.
    
    Args:
        df: DataFrame containing the data.
        predictors: List of predictor column names.
        
    Returns:
        Dictionary mapping predictor names to VIF values.
    """
    vif_data = {}
    X = df[predictors]
    X = sm.add_constant(X)
    
    for col in X.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
            
    return vif_data

def check_vif_results(vif_results: Dict[str, float], threshold: float) -> Dict[str, Any]:
    """
    Checks VIF results against the threshold and returns status.
    
    Args:
        vif_results: Dictionary of VIF values.
        threshold: The VIF threshold value.
        
    Returns:
        Dictionary with vif_value, threshold_value, and status.
    """
    max_vif = max(vif_results.values()) if vif_results else 0.0
    status = "PASS" if max_vif < threshold else "FAIL"
    
    return {
        "vif_value": max_vif,
        "threshold_value": threshold,
        "status": status
    }

def generate_associational_report(model_results: Dict[str, Any], 
                                  vif_results: Dict[str, Any], 
                                  df_stats: Dict[str, Any]) -> str:
    """
    Generates a draft report string ensuring all findings are labeled "associational".
    
    This function constructs a text buffer that describes the results.
    It explicitly avoids causal language (e.g., "causes", "leads to").
    
    Args:
        model_results: Dictionary containing regression results.
        vif_results: Dictionary containing VIF analysis results.
        df_stats: Dictionary containing dataset statistics.
        
    Returns:
        A string buffer representing the draft report.
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("STATISTICAL ANALYSIS REPORT: ASSOCIATIONAL FINDINGS")
    report_lines.append("=" * 60)
    report_lines.append("")
    
    # Dataset Overview
    report_lines.append("1. DATASET OVERVIEW")
    report_lines.append(f"   - Sample Size (N): {df_stats.get('n_rows', 0)}")
    report_lines.append(f"   - Predictors Used: {', '.join(df_stats.get('predictors_used', []))}")
    report_lines.append("")
    
    # Model Fit
    report_lines.append("2. MODEL FIT STATISTICS")
    report_lines.append(f"   - R-squared: {model_results.get('r_squared', 0):.4f}")
    report_lines.append(f"   - Adjusted R-squared: {model_results.get('adj_r_squared', 0):.4f}")
    report_lines.append(f"   - F-statistic: {model_results.get('f_statistic', 0):.2f}")
    report_lines.append(f"   - F-statistic p-value: {model_results.get('f_pvalue', 0):.6f}")
    report_lines.append("")
    
    # Coefficients
    report_lines.append("3. COEFFICIENT ESTIMATES (ASSOCIATIONAL)")
    report_lines.append("   The following coefficients represent the *association* between")
    report_lines.append("   the predictors and the outcome variable, holding other variables constant.")
    report_lines.append("")
    
    params = model_results.get('params', {})
    pvalues = model_results.get('pvalues', {})
    conf_int = model_results.get('conf_int', [])
    
    for i, (param_name, coef) in enumerate(params.items()):
        if param_name == 'const':
            continue
        p_val = pvalues.get(param_name, 0)
        sig_level = get_significance_level()
        significance = " (significant)" if p_val < sig_level else ""
        
        # Ensure we use "associated with" or "linked to" instead of "causes"
        report_lines.append(f"   - {param_name}:")
        report_lines.append(f"       Coefficient: {coef:.4f}")
        report_lines.append(f"       p-value: {p_val:.6f}{significance}")
        if conf_int and len(conf_int) > i:
            ci_low = conf_int[i][0]
            ci_high = conf_int[i][1]
            report_lines.append(f"       95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
        report_lines.append("")
        
    # VIF Results
    report_lines.append("4. MULTICOLLINEARITY CHECK (VIF)")
    vif_val = vif_results.get('vif_value', 0)
    threshold = vif_results.get('threshold_value', 0)
    status = vif_results.get('status', 'UNKNOWN')
    
    report_lines.append(f"   - Maximum VIF observed: {vif_val:.4f}")
    report_lines.append(f"   - Threshold: {threshold}")
    report_lines.append(f"   - Status: {status}")
    report_lines.append("")
    
    # Conclusion
    report_lines.append("5. CONCLUSION")
    report_lines.append("   The analysis identifies statistical *associations* between the predictors")
    report_lines.append("   and self-perception scores. These results describe the strength and direction")
    report_lines.append("   of the relationships observed in the data but do not imply causality.")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def run_analysis(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the full regression analysis pipeline including VIF and report generation.
    
    Args:
        df: Input DataFrame.
        output_path: Optional path to save the model results JSON.
        
    Returns:
        Dictionary containing all analysis results.
    """
    logger.info("Starting regression analysis...")
    
    # 1. Fit Model
    model, model_summary = fit_multiple_linear_regression(df)
    
    # 2. Calculate VIF
    predictors = [col for col in model_summary['predictors_used'] if col != 'const']
    vif_scores = calculate_vif(df, predictors)
    threshold = get_vif_threshold()
    vif_check = check_vif_results(vif_scores, threshold)
    
    # 3. Prepare data for report
    df_stats = {
        'n_rows': len(df),
        'predictors_used': model_summary['predictors_used']
    }
    
    # Extract model details for report generation
    model_details = {
        'params': model.params.to_dict(),
        'pvalues': model.pvalues.to_dict(),
        'conf_int': model.conf_int().values.tolist(),
        'r_squared': model_summary['r_squared'],
        'adj_r_squared': model_summary['adj_r_squared'],
        'f_statistic': model_summary['f_statistic'],
        'f_pvalue': model_summary['f_pvalue']
    }
    
    # 4. Generate Draft Report Buffer
    draft_report = generate_associational_report(model_details, vif_check, df_stats)
    
    # 5. CAUSAL LANGUAGE CHECK (T020)
    # Scan the draft report for forbidden causal language
    trigger_words, found = scan_report_for_causal_language(draft_report)
    
    if found:
        logger.error(f"Causal language detected: {trigger_words}")
        raise CausalLanguageViolationError(
            f"Causal language violation detected in report. Found: {trigger_words}. "
            "The pipeline halts to prevent misinterpretation of associational data as causal."
        )
    
    # 6. Compile Final Results
    final_results = {
        'model_summary': model_summary,
        'coefficients': model_details['params'],
        'pvalues': model_details['pvalues'],
        'confidence_intervals': model_details['conf_int'],
        'vif_analysis': {
            'scores': vif_scores,
            'max_vif': vif_check['vif_value'],
            'threshold': vif_check['threshold_value'],
            'status': vif_check['status']
        },
        'report_draft': draft_report,
        'causal_check': {
            'passed': True,
            'trigger_words_found': []
        }
    }
    
    # 7. Save to JSON if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_path}")
        
    return final_results

def main():
    """
    Entry point for running the regression analysis standalone.
    Expects a CSV file in data/processed/ or similar.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Regression Analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--output", type=str, default="data/processed/model_results.json", help="Path to output JSON")
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    try:
        results = run_analysis(df, args.output)
        print("Analysis completed successfully.")
        print(f"Max VIF: {results['vif_analysis']['max_vif']:.2f} ({results['vif_analysis']['status']})")
    except CausalLanguageViolationError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()