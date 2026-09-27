"""
Collinearity diagnostics (VIF) implementation.

Calculates Variance Inflation Factor (VIF) for all available predictors
to detect multicollinearity before ANCOVA.

SC-004: Study is invalid if any predictor has VIF >= 5.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import config loader from the project's config module
from config import load_config as load_project_config


def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Set up a logger that writes to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger


def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    return load_project_config()


def load_analysis_results() -> pd.DataFrame:
    """
    Load the combined analysis data required for VIF calculation.
    
    This function loads:
    1. Complexity metrics from data/analysis/complexity_metrics.csv
    2. Delta scores from data/analysis/delta_scores.csv
    
    And merges them by participant_id to create the predictor matrix.
    
    Returns:
        pd.DataFrame: Merged dataframe with all available predictors.
        
    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If required columns are missing.
    """
    base_path = Path("data/analysis")
    
    # Load complexity metrics
    complexity_path = base_path / "complexity_metrics.csv"
    if not complexity_path.exists():
        raise FileNotFoundError(f"Complexity metrics file not found: {complexity_path}")
    
    complexity_df = pd.read_csv(complexity_path)
    
    # Load delta scores
    delta_path = base_path / "delta_scores.csv"
    if not delta_path.exists():
        raise FileNotFoundError(f"Delta scores file not found: {delta_path}")
    
    delta_df = pd.read_csv(delta_path)
    
    # Merge on participant_id
    # We need Pre_Complexity and Post_Complexity, plus Fatigue_Delta
    merged = pd.merge(
        delta_df,
        complexity_df,
        on='participant_id',
        how='inner'
    )
    
    # Identify available predictors
    required_core = ['Fatigue_Delta']
    optional_covariates = ['age', 'time_of_day', 'medication_status']
    
    available_predictors = []
    
    # Core predictors
    if 'Fatigue_Delta' in merged.columns:
        available_predictors.append('Fatigue_Delta')
    else:
        raise ValueError("Required predictor 'Fatigue_Delta' not found in delta_scores.csv")
    
    # Check for Pre_Complexity - we need to aggregate by channel or use median
    if 'Pre_Complexity' in merged.columns:
        available_predictors.append('Pre_Complexity')
    elif 'lzc_value' in merged.columns and 'segment_id' in merged.columns:
        # Aggregate complexity metrics if not pre-aggregated
        # Use median Lempel-Ziv complexity across channels/segments as Pre_Complexity
        pre_complexity = merged[merged['segment_id'].str.contains('pre', case=False, na=False)].groupby('participant_id')['lzc_value'].median()
        merged = merged.drop(columns=['lzc_value', 'segment_id', 'channel'], errors='ignore')
        merged = merged.merge(pre_complexity.rename('Pre_Complexity'), left_on='participant_id', right_index=True, how='left')
        available_predictors.append('Pre_Complexity')
    
    # Check for optional covariates
    for cov in optional_covariates:
        if cov in merged.columns:
            available_predictors.append(cov)
    
    if len(available_predictors) < 2:
        raise ValueError(f"Insufficient predictors for VIF calculation. Need at least 2, found: {available_predictors}")
    
    return merged, available_predictors


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for each predictor in the dataframe.
    
    Args:
        df: DataFrame containing all predictors.
        predictors: List of column names to calculate VIF for.
        
    Returns:
        Dict mapping predictor name to VIF value.
        
    Note:
        VIF for a predictor is calculated as 1 / (1 - R^2) where R^2
        is from regressing that predictor against all other predictors.
    """
    # Prepare the design matrix (drop NaNs for VIF calculation)
    X = df[predictors].dropna()
    
    if len(X) < len(predictors) + 1:
        raise ValueError(f"Insufficient samples for VIF calculation. Need at least {len(predictors) + 1}, got {len(X)}")
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_results = {}
    for i, col in enumerate(predictors):
        # VIF formula: 1 / (1 - R^2) for regression of col on all other predictors
        # statsmodels vif function handles this
        try:
            vif_val = variance_inflation_factor(X_with_const.values, i + 1)  # +1 because of constant
            vif_results[col] = float(vif_val)
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_results[col] = float('inf')
    
    return vif_results


def run_collinearity_diagnostics(logger: logging.Logger) -> Dict[str, Any]:
    """
    Run full collinearity diagnostic pipeline.
    
    1. Load analysis data
    2. Calculate VIF for all available predictors
    3. Log all VIF values
    4. Check threshold (VIF < 5)
    5. Either halt with error or save valid predictors
    
    Returns:
        Dict with 'valid' (bool) and 'predictors' (list) keys.
    """
    logger.info("Loading analysis results for VIF calculation")
    try:
        merged_df, available_predictors = load_analysis_results()
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return {'valid': False, 'error': str(e), 'predictors': []}
    
    logger.info(f"Available predictors for VIF: {available_predictors}")
    
    # Calculate VIF
    logger.info("Calculating VIF for all predictors")
    vif_results = calculate_vif(merged_df, available_predictors)
    
    # Log all VIF values BEFORE checking threshold
    logger.info("VIF Diagnostic Results:")
    for predictor, vif_val in vif_results.items():
        status = "PASS" if vif_val < 5.0 else "FAIL"
        logger.info(f"  {predictor}: VIF = {vif_val:.4f} [{status}]")
    
    # Check for violations
    collinear_predictors = [p for p, v in vif_results.items() if v >= 5.0]
    
    if collinear_predictors:
        logger.warning(f"Collinearity violation: VIF >= 5 for {collinear_predictors}")
        logger.error(f"Study invalid per SC-004: Collinearity detected in {collinear_predictors}")
        return {
            'valid': False, 
            'error': f"Collinearity violation: VIF >= 5 for {collinear_predictors}. Study invalid per SC-004.",
            'predictors': list(vif_results.keys()),
            'vif_values': vif_results
        }
    
    # All predictors pass
    logger.info("All predictors passed VIF < 5 threshold")
    return {
        'valid': True,
        'predictors': available_predictors,
        'vif_values': vif_results
    }


def save_collinearity_report(result: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Save VIF diagnostic results to log and JSON file.
    
    Args:
        result: Output from run_collinearity_diagnostics
        logger: Logger instance
    """
    log_path = Path("data/analysis/vif_diagnostics.log")
    os.makedirs(log_path.parent, exist_ok=True)
    
    # Append to log file
    with open(log_path, 'a') as f:
        f.write(f"\n--- VIF Diagnostic Run: {pd.Timestamp.now().isoformat()} ---\n")
        if 'error' in result and not result['valid']:
            f.write(f"RESULT: FAILED - {result['error']}\n")
        else:
            f.write(f"RESULT: PASSED\n")
            f.write(f"Valid predictors: {result['predictors']}\n")
            if 'vif_values' in result:
                for p, v in result['vif_values'].items():
                    f.write(f"  {p}: {v:.4f}\n")
    
    # Save JSON if all pass
    if result['valid']:
        json_path = Path("data/analysis/vif_valid_predictors.json")
        with open(json_path, 'w') as f:
            json.dump({
                'valid': True,
                'predictors': result['predictors'],
                'vif_values': result['vif_values']
            }, f, indent=2)
        logger.info(f"Saved valid predictors to {json_path}")
    else:
        logger.info("VIF check failed - no valid_predictors.json created")


def main():
    """Main entry point for collinearity diagnostics."""
    parser = argparse.ArgumentParser(description="Run VIF collinearity diagnostics")
    parser.add_argument("--log-file", type=str, default=None, help="Optional log file path")
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("collinearity", args.log_file)
    logger.info("Starting collinearity diagnostics (VIF check)")
    
    # Load config
    config = load_config()
    logger.info(f"Loaded config: notch_frequency={config.get('notch_frequency', 'N/A')}")
    
    # Run diagnostics
    result = run_collinearity_diagnostics(logger)
    
    # Save report
    save_collinearity_report(result, logger)
    
    # Exit with appropriate code
    if not result['valid']:
        logger.error(result.get('error', 'Unknown error'))
        sys.exit(1)
    else:
        logger.info("Collinearity diagnostics passed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
