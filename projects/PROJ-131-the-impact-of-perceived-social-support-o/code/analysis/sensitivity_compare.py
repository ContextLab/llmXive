import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_baseline_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the baseline regression results (from T024).
    Expected columns include: outcome, predictor, coef, se, pval, ci_low, ci_high
    """
    if filepath is None:
        filepath = "data/results/regression_results.csv"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Baseline results file not found at {filepath}. "
                                "Ensure T024 has run successfully.")
    
    logger.info(f"Loading baseline results from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure numeric types
    numeric_cols = ['coef', 'se', 'pval', 'ci_low', 'ci_high']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def load_sensitivity_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the sensitivity analysis results (from T029).
    Expected columns include: scenario, outcome, predictor, coef, se, pval
    """
    if filepath is None:
        filepath = "data/results/sensitivity_analysis.csv"
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found at {filepath}. "
                                "Ensure T029 has run successfully.")
    
    logger.info(f"Loading sensitivity results from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure numeric types
    numeric_cols = ['coef', 'se', 'pval']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def extract_interaction_coefficients(results_df: pd.DataFrame, 
                                     predictor_col: str = 'predictor',
                                     coef_col: str = 'coef',
                                     outcome_col: str = 'outcome',
                                     scenario_col: Optional[str] = None) -> pd.DataFrame:
    """
    Filter for the interaction term (SocialSupport:HarassmentExposure) and extract coefficients.
    
    Args:
        results_df: DataFrame containing regression results.
        predictor_col: Name of the column containing predictor names.
        coef_col: Name of the column containing coefficients.
        outcome_col: Name of the column containing outcome variable names.
        scenario_col: Name of the column identifying the scenario (e.g., 'baseline' vs 'sensitivity').
    
    Returns:
        DataFrame with columns: outcome, predictor, coef, scenario (if applicable)
    """
    # Identify interaction term patterns
    interaction_keywords = ['SocialSupport', 'Harassment', 'interaction', ':']
    interaction_mask = results_df[predictor_col].apply(
        lambda x: any(kw.lower() in str(x).lower() for kw in interaction_keywords)
    )
    
    interaction_df = results_df[interaction_mask].copy()
    
    # If scenario column doesn't exist, add it based on source
    if scenario_col and scenario_col not in interaction_df.columns:
        # Infer scenario from context if needed, but usually passed explicitly
        pass 
    
    return interaction_df[['outcome', 'predictor', 'coef']]

def compare_coefficients(baseline_df: pd.DataFrame, 
                         sensitivity_df: pd.DataFrame,
                         baseline_scenario: str = 'baseline',
                         sensitivity_scenario_col: str = 'scenario') -> pd.DataFrame:
    """
    Compare interaction coefficients from sensitivity runs against the baseline.
    Calculates the absolute and relative shift.
    
    Args:
        baseline_df: Baseline results DataFrame.
        sensitivity_df: Sensitivity results DataFrame.
        baseline_scenario: Label for the baseline scenario.
        sensitivity_scenario_col: Column name in sensitivity_df identifying the run type.
    
    Returns:
        DataFrame comparing coefficients with shift metrics.
    """
    # Extract interaction terms
    baseline_interactions = extract_interaction_coefficients(baseline_df)
    baseline_interactions['scenario'] = baseline_scenario
    
    sensitivity_interactions = extract_interaction_coefficients(sensitivity_df)
    
    if sensitivity_scenario_col not in sensitivity_interactions.columns:
        # If the column is missing, assume all rows are from the sensitivity run
        # unless the file itself distinguishes them. 
        # Based on T029 spec, it should have a 'scenario' column.
        logger.warning("Sensitivity results missing 'scenario' column. Assuming single sensitivity run.")
        sensitivity_interactions['scenario'] = 'sensitivity_continuous'
    
    # Rename columns to align for merging
    baseline_interactions = baseline_interactions.rename(columns={'coef': 'coef_baseline'})
    sensitivity_interactions = sensitivity_interactions.rename(columns={'coef': 'coef_sensitivity'})
    
    # Merge on outcome
    comparison = pd.merge(
        baseline_interactions[['outcome', 'scenario', 'coef_baseline']],
        sensitivity_interactions[['outcome', 'scenario', 'coef_sensitivity']],
        on='outcome',
        how='inner'
    )
    
    # Calculate shifts
    comparison['coef_shift'] = comparison['coef_sensitivity'] - comparison['coef_baseline']
    comparison['relative_shift_pct'] = (
        (comparison['coef_shift'] / comparison['coef_baseline']) * 100 
        if not comparison['coef_baseline'].isna().all() else np.nan
    )
    
    # Add scenario labels for clarity
    comparison['baseline_scenario'] = baseline_scenario
    comparison['sensitivity_scenario'] = comparison['scenario'].iloc[0] if len(comparison) > 0 else 'unknown'
    
    # Select final columns
    final_cols = [
        'outcome', 'baseline_scenario', 'coef_baseline', 
        'sensitivity_scenario', 'coef_sensitivity', 
        'coef_shift', 'relative_shift_pct'
    ]
    return comparison[final_cols]

def save_comparison_table(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """
    Save the comparison table to a CSV file.
    """
    if filepath is None:
        filepath = "data/results/sensitivity_coefficient_comparison.csv"
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving comparison table to {filepath}")
    df.to_csv(filepath, index=False)
    
    # Also log a summary
    logger.info(f"Comparison table generated with {len(df)} rows.")
    logger.info(f"Mean absolute shift: {df['coef_shift'].abs().mean():.4f}")

def run_sensitivity_comparison(baseline_path: Optional[str] = None,
                               sensitivity_path: Optional[str] = None,
                               output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Orchestrates the loading, comparison, and saving of sensitivity coefficient shifts.
    """
    logger.info("Starting sensitivity coefficient comparison (Task T028)")
    
    try:
        baseline_df = load_baseline_results(baseline_path)
        sensitivity_df = load_sensitivity_results(sensitivity_path)
        
        comparison_df = compare_coefficients(baseline_df, sensitivity_df)
        
        save_comparison_table(comparison_df, output_path)
        
        logger.info("Sensitivity coefficient comparison completed successfully.")
        return comparison_df
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during comparison: {e}")
        raise

def main():
    """
    Entry point for T028 execution.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default paths based on project structure
    baseline_path = "data/results/regression_results.csv"
    sensitivity_path = "data/results/sensitivity_analysis.csv"
    output_path = "data/results/sensitivity_coefficient_comparison.csv"
    
    try:
        run_sensitivity_comparison(baseline_path, sensitivity_path, output_path)
        print(f"Comparison table saved to {output_path}")
    except Exception as e:
        print(f"Failed to run sensitivity comparison: {e}")
        raise

if __name__ == "__main__":
    main()