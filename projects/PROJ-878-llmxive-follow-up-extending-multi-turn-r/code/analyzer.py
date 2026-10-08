import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# External dependencies required by FR-004
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_execution_results(filepath: str) -> pd.DataFrame:
    """
    Load execution results from CSV.
    
    Args:
        filepath: Path to the execution log CSV file.
        
    Returns:
        DataFrame containing execution results.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Execution results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    required_cols = ['instance_id', 'turns_to_converge', 'nesting_depth', 'convergence_status']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in execution results: {missing}")
    
    logger.info(f"Loaded {len(df)} execution records from {filepath}")
    return df

def perform_cox_ph_analysis(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Perform Cox Proportional Hazards survival analysis.
    
    Models 'turns_to_converge' as the survival time, with 'nesting_depth'
    as the covariate. 'convergence_status' determines if the event (convergence)
    occurred or if it was censored (timeout).
    
    Args:
        df: DataFrame with execution results.
        
    Returns:
        Tuple of (CoxPHFitter model object, summary statistics dict).
    """
    # Prepare data for lifelines
    # Event occurred if status is 'success'
    df_analysis = df.copy()
    df_analysis['event'] = df_analysis['convergence_status'].apply(
        lambda x: 1 if x == 'success' else 0
    )
    
    # Filter out infinite or negative turns if any (should not happen but safety)
    df_analysis = df_analysis[df_analysis['turns_to_converge'] > 0]
    
    if len(df_analysis) == 0:
        raise ValueError("No valid data points for survival analysis after filtering.")
    
    # Fit Cox PH model
    cph = CoxPHFitter()
    try:
        cph.fit(df_analysis[['turns_to_converge', 'nesting_depth', 'event']], 
                duration_col='turns_to_converge', 
                event_col='event')
    except Exception as e:
        logger.error(f"Cox PH fitting failed: {e}")
        raise
    
    # Extract summary statistics
    summary = {
        'concordance_index': cph.concordance_index_,
        'coefficients': cph.params_.to_dict(),
        'hazard_ratios': cph.hazard_ratios_.to_dict(),
        'p_values': cph.summary['p'].to_dict(),
        'n_samples': len(df_analysis),
        'n_events': int(df_analysis['event'].sum())
    }
    
    logger.info(f"Cox PH Analysis complete. Concordance Index: {summary['concordance_index']:.4f}")
    return cph, summary

def perform_spearman_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Perform Spearman rank correlation analysis between nesting_depth and turns_to_converge.
    
    This is a descriptive statistic (FR-004, SC-001) to assess monotonic relationship.
    
    Args:
        df: DataFrame with execution results.
        
    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    # Filter to successful convergences for correlation, or all data?
    # Typically correlation is done on the continuous variable of interest.
    # We include all data points that have a numeric turn count.
    valid_df = df[df['turns_to_converge'].notna() & (df['turns_to_converge'] > 0)]
    
    if len(valid_df) < 2:
        logger.warning("Insufficient data for Spearman correlation.")
        return 0.0, 1.0
    
    corr, p_val = spearmanr(
        valid_df['nesting_depth'].values,
        valid_df['turns_to_converge'].values
    )
    
    logger.info(f"Spearman Correlation: rho={corr:.4f}, p-value={p_val:.4f}")
    return float(corr), float(p_val)

def generate_statistical_report(
    cox_summary: Dict[str, Any], 
    spearman_corr: float, 
    spearman_p: float,
    thresholds: List[int]
) -> Dict[str, Any]:
    """
    Compile all statistical results into a report dictionary.
    
    Args:
        cox_summary: Summary statistics from Cox PH analysis.
        spearman_corr: Spearman correlation coefficient.
        spearman_p: Spearman p-value.
        thresholds: List of turn thresholds used for sensitivity analysis.
        
    Returns:
        Dictionary containing the full statistical report.
    """
    report = {
        'analysis_type': 'Survival and Correlation Analysis',
        'fr_004_compliance': {
            'cox_ph_analysis': {
                'concordance_index': cox_summary['concordance_index'],
                'coefficients': cox_summary['coefficients'],
                'hazard_ratios': cox_summary['hazard_ratios'],
                'p_values': cox_summary['p_values'],
                'n_samples': cox_summary['n_samples'],
                'n_events': cox_summary['n_events']
            },
            'spearman_correlation': {
                'coefficient': spearman_corr,
                'p_value': spearman_p,
                'description': 'Descriptive statistic for monotonic relationship between nesting_depth and turns_to_converge'
            }
        },
        'sensitivity_analysis_thresholds': thresholds,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Statistical Analysis for llmXive')
    parser.add_argument('--puzzles', type=str, required=True, 
                        help='Path to puzzles JSONL file (for metadata if needed)')
    parser.add_argument('--results', type=str, required=True, 
                        help='Path to execution results CSV')
    parser.add_argument('--output', type=str, required=True, 
                        help='Path to output JSON report')
    parser.add_argument('--thresholds', type=int, nargs='+', default=[40, 50, 60],
                        help='Turn thresholds for sensitivity analysis')
    
    args = parser.parse_args()
    
    try:
        # 1. Load data
        df = load_execution_results(args.results)
        
        # 2. Perform Cox PH Analysis
        cox_model, cox_summary = perform_cox_ph_analysis(df)
        
        # 3. Perform Spearman Correlation
        spearman_corr, spearman_p = perform_spearman_correlation(df)
        
        # 4. Generate Report
        report = generate_statistical_report(
            cox_summary, spearman_corr, spearman_p, args.thresholds
        )
        
        # 5. Write Output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Statistical report written to {output_path}")
        print(f"Report saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
