import json
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from scipy import stats
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import TIMEOUT_SECONDS

logger = get_logger(__name__)

def load_results_csv(input_path: str) -> pd.DataFrame:
    """Load the merged results CSV containing paired baseline and rule-engine metrics."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['task_id', 'method_rule', 'time_rule', 'success_rule', 
                     'method_baseline', 'time_baseline', 'success_baseline', 
                     'failure_type']
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def verify_paired_data_integrity(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Verify that every task_id has both rule and baseline entries."""
    issues = []
    task_ids = df['task_id'].unique()
    
    for tid in task_ids:
        subset = df[df['task_id'] == tid]
        has_rule = (subset['method_rule'].notna()).any()
        has_baseline = (subset['method_baseline'].notna()).any()
        
        if not has_rule or not has_baseline:
            issues.append(f"task_id {tid} missing paired data (rule: {has_rule}, baseline: {has_baseline})")
    
    if issues:
        logger.error(f"Data integrity check failed: {len(issues)} issues found")
        return False, issues
    
    logger.info("Paired data integrity check passed")
    return True, []

def prepare_data_for_regression(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the dataframe for mixed-effects regression analysis."""
    # Create long format for regression
    # We need: task_id, method (rule/baseline), time, success, failure_type
    
    rule_df = df[['task_id', 'method_rule', 'time_rule', 'success_rule', 'failure_type']].copy()
    rule_df.columns = ['task_id', 'method', 'time', 'success', 'failure_type']
    rule_df['method'] = 'rule'
    
    baseline_df = df[['task_id', 'method_baseline', 'time_baseline', 'success_baseline', 'failure_type']].copy()
    baseline_df.columns = ['task_id', 'method', 'time', 'success', 'failure_type']
    baseline_df['method'] = 'baseline'
    
    long_df = pd.concat([rule_df, baseline_df], ignore_index=True)
    
    # Handle censored time values
    # If time equals TIMEOUT_SECONDS, mark as censored
    long_df['is_censored'] = (long_df['time'] >= TIMEOUT_SECONDS).astype(int)
    
    # Encode method as numeric for interaction
    long_df['method_num'] = (long_df['method'] == 'baseline').astype(int)
    
    # Encode failure_type as numeric (one-hot or ordinal)
    # For simplicity in formula, we'll use categorical
    long_df['failure_type'] = long_df['failure_type'].astype('category')
    
    logger.info(f"Prepared {len(long_df)} rows for regression")
    return long_df

def fit_mixed_effects_model(long_df: pd.DataFrame) -> Any:
    """Fit mixed-effects logistic regression for success outcome."""
    # Formula: success ~ failure_type * method + (1|task_id)
    # Using GEE for binary outcome with exchangeable correlation
    
    # Remove rows with missing values
    clean_df = long_df.dropna(subset=['success', 'time', 'failure_type', 'method'])
    
    if len(clean_df) == 0:
        raise ValueError("No valid data points for regression after cleaning")
    
    # Fit logistic regression with GEE (since mixedlm doesn't support binary directly)
    # Using Exchangeable correlation structure for paired data
    formula = "success ~ C(failure_type) * C(method)"
    
    try:
        model = GEE.from_formula(
            formula,
            groups="task_id",
            data=clean_df,
            family=stats.families.Binomial(),
            cov_struct=Exchangeable()
        )
        result = model.fit()
        logger.info("Mixed-effects model fitted successfully")
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {str(e)}")
        # Fallback to simpler logistic regression if GEE fails
        try:
            import statsmodels.api as sm
            y = clean_df['success'].values
            # Create design matrix manually
            X = pd.get_dummies(clean_df[['failure_type', 'method']], drop_first=True)
            X = sm.add_constant(X)
            model = sm.Logit(y, X)
            result = model.fit(disp=False)
            logger.warning("Fell back to standard logistic regression")
            return result
        except Exception as e2:
            raise RuntimeError(f"Both model fitting attempts failed: {str(e2)}")

def extract_interaction_p_value(result: Any) -> Dict[str, Any]:
    """Extract the p-value for the interaction term between failure_type and method."""
    summary = result.summary2()
    
    # Extract coefficients and p-values
    coefs = {}
    if hasattr(summary, 'tables') and len(summary.tables) > 1:
        coef_table = summary.tables[1]
        for idx, row in coef_table.iterrows():
            coef_name = str(idx)
            if 'p' in row.index:
                p_val = row['p']
            elif 'P>|t|' in row.index:
                p_val = row['P>|t|']
            elif 'P>|z|' in row.index:
                p_val = row['P>|z|']
            else:
                p_val = None
            coefs[coef_name] = {'coef': row.get('Coef.', 0), 'p_value': p_val}
    
    # Look for interaction terms (contain both failure_type and method)
    interaction_terms = {}
    for name, stats in coefs.items():
        if 'C(failure_type)' in name and 'C(method)' in name:
            interaction_terms[name] = stats
    
    # Find the minimum p-value among interaction terms
    min_p = None
    min_term = None
    for term, stats in interaction_terms.items():
        if stats['p_value'] is not None:
            if min_p is None or stats['p_value'] < min_p:
                min_p = stats['p_value']
                min_term = term
    
    return {
        'interaction_terms': interaction_terms,
        'min_interaction_p_value': min_p,
        'significant_at_005': min_p < 0.05 if min_p is not None else False,
        'significant_at_001': min_p < 0.01 if min_p is not None else False
    }

def save_regression_results(result: Any, output_path: str, interaction_info: Dict[str, Any]) -> None:
    """Save regression results to JSON file."""
    results_dict = {
        'model_type': 'Mixed-Effects Logistic Regression (GEE)',
        'formula': "success ~ C(failure_type) * C(method) + (1|task_id)",
        'interaction_significance': interaction_info,
        'coefficients': {},
        'sample_size': result.nobs if hasattr(result, 'nobs') else 0
    }
    
    # Extract coefficients
    if hasattr(result, 'params'):
        for name, coef in result.params.items():
            results_dict['coefficients'][name] = {
                'estimate': float(coef),
                'p_value': interaction_info['interaction_terms'].get(name, {}).get('p_value')
            }
    
    # Add model fit statistics
    if hasattr(result, 'converged'):
        results_dict['converged'] = result.converged
    if hasattr(result, 'cov_re'):
        results_dict['n_params'] = len(result.params)
    
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)
    
    logger.info(f"Saved regression results to {output_path}")

def generate_interaction_significance_report(interaction_info: Dict[str, Any], output_path: str) -> None:
    """Generate a human-readable report on interaction term significance."""
    report = {
        'timestamp': str(pd.Timestamp.now()),
        'analysis_type': 'Interaction Term Significance (Failure Type x Method)',
        'hypothesis': 'The interaction between failure structure and method determines success rates',
        'results': interaction_info,
        'conclusion': (
            "SIGNIFICANT" if interaction_info['significant_at_005'] 
            else "NOT SIGNIFICANT"
        ),
        'interpretation': (
            "The data supports the hypothesis that failure structure dictates method viability."
            if interaction_info['significant_at_005']
            else "The data does not provide sufficient evidence to support the hypothesis."
        )
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved interaction significance report to {output_path}")

def run_pilot_analysis(input_path: str, regression_output: str, interaction_output: str) -> None:
    """Run the full pilot statistical analysis pipeline."""
    log_stage_start("pilot_statistical_analysis", input_path)
    
    try:
        # Load data
        df = load_results_csv(input_path)
        
        # Verify paired data
        is_valid, issues = verify_paired_data_integrity(df)
        if not is_valid:
            raise ValueError(f"Data integrity check failed: {issues}")
        
        # Prepare data
        long_df = prepare_data_for_regression(df)
        
        # Fit model
        model_result = fit_mixed_effects_model(long_df)
        
        # Extract interaction significance
        interaction_info = extract_interaction_p_value(model_result)
        
        # Save results
        save_regression_results(model_result, regression_output, interaction_info)
        generate_interaction_significance_report(interaction_info, interaction_output)
        
        log_stage_end("pilot_statistical_analysis", "SUCCESS")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        log_stage_end("pilot_statistical_analysis", "FAILED", str(e))
        raise

def main():
    parser = argparse.ArgumentParser(description="Run pilot statistical analysis")
    parser.add_argument("--input", required=True, help="Path to input results CSV")
    parser.add_argument("--regression-output", 
                        default="data/derived/pilot_regression_results.json",
                        help="Path for regression results JSON")
    parser.add_argument("--interaction-output",
                        default="data/derived/pilot_interaction_significance_report.json",
                        help="Path for interaction significance report JSON")
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    for path in [args.regression_output, args.interaction_output]:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    run_pilot_analysis(args.input, args.regression_output, args.interaction_output)

if __name__ == "__main__":
    main()
