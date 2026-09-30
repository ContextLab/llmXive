import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure parent directory is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from statsmodels.formula.api import mixedlm
    from statsmodels.regression.linear_model import OLS
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    raise ImportError("statsmodels is required. Install via: pip install statsmodels")

from config import load_config
from logging_config import LoggingContext, get_logger

logger = get_logger(__name__)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    Args:
        df: DataFrame containing predictor columns.
        predictors: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping predictor name to VIF value.
    """
    vif_data = {}
    # Add intercept for VIF calculation if not present
    X = df[predictors].dropna()
    
    if X.empty:
        logger.warning("No valid data for VIF calculation.")
        return {p: float('inf') for p in predictors}

    # OLS requires a constant term for VIF calculation in statsmodels
    try:
        X_with_const = sm.add_constant(X)
        model = OLS(X_with_const.iloc[:, 1], X_with_const).fit()
        vif = [variance_inflation_factor(model.model.exog, i) 
               for i in range(model.model.exog.shape[1])]
        
        # Map back to original predictors (skipping const)
        for i, p in enumerate(predictors):
            vif_data[p] = vif[i+1]
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        # Fallback to simple correlation-based estimation if OLS fails
        for p in predictors:
            # Simple heuristic: max correlation with other predictors
            max_corr = 0
            for other in predictors:
                if other != p:
                    corr = df[p].corr(df[other])
                    if corr is not None and abs(corr) > max_corr:
                        max_corr = abs(corr)
            # VIF approx 1 / (1 - R^2)
            vif_data[p] = 1.0 / (1.0 - (max_corr ** 2)) if max_corr < 1.0 else float('inf')
    
    return vif_data

def mitigate_collinearity(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> Tuple[List[str], Optional[str]]:
    """
    Mitigate collinearity by dropping the predictor with highest VIF if > threshold.
    Performs a SINGLE step reduction as per requirements.
    
    Args:
        df: DataFrame with data.
        predictors: List of candidate predictors.
        threshold: VIF threshold for dropping.
        
    Returns:
        Tuple of (remaining_predictors, dropped_predictor_name or None)
    """
    vif_values = calculate_vif(df, predictors)
    dropped = None
    
    # Find max VIF
    max_vif_pred = None
    max_vif_val = -1
    
    for p, v in vif_values.items():
        if v > max_vif_val:
            max_vif_val = v
            max_vif_pred = p
    
    if max_vif_val > threshold and max_vif_pred:
        logger.warning(f"VIF for '{max_vif_pred}' is {max_vif_val:.2f} > {threshold}. Dropping predictor.")
        remaining = [p for p in predictors if p != max_vif_pred]
        return remaining, max_vif_pred
    
    return predictors, None

def handle_unfulfillable_predictors(df: pd.DataFrame, predictors: List[str], unfulfillable_marker: str = "UNFULFILLABLE") -> Tuple[List[str], List[str]]:
    """
    Identify and remove predictors marked as UNFULFULFILLABLE.
    
    Args:
        df: DataFrame.
        predictors: List of predictor names.
        unfulfillable_marker: String value indicating unfulfillable data.
        
    Returns:
        Tuple of (valid_predictors, dropped_predictors)
    """
    valid = []
    dropped = []
    
    for p in predictors:
        if p not in df.columns:
            dropped.append(p)
            logger.warning(f"Predictor '{p}' not found in data. Dropping.")
            continue
        
        # Check if column contains the unfulfillable marker
        if df[p].dtype == object or df[p].apply(lambda x: isinstance(x, str)).any():
            if (df[p] == unfulfillable_marker).any():
                dropped.append(p)
                logger.warning(f"Predictor '{p}' contains UNFULFILLABLE values. Dropping.")
                continue
        
        valid.append(p)
        
    return valid, dropped

def validate_sufficient_trials(df: pd.DataFrame, subject_col: str = 'subject_id', 
                               min_trials: int = 20, aggregate_flag: bool = False) -> pd.DataFrame:
    """
    Validate that each subject has sufficient trials.
    
    Logic:
    - Group by subject_id and count trials.
    - If any subject has < min_trials:
      - If aggregate_flag is True: Aggregate across subjects (drop subject_id, treat as single group).
      - If aggregate_flag is False: Raise RuntimeError with message "Subject {id} has < 20 trials".
    
    Args:
        df: Input DataFrame.
        subject_col: Name of the subject ID column.
        min_trials: Minimum required trials per subject.
        aggregate_flag: If True, aggregate data across subjects instead of failing.
        
    Returns:
        DataFrame (possibly aggregated if flag is set).
        
    Raises:
        RuntimeError: If a subject has insufficient trials and aggregation is disabled.
    """
    if subject_col not in df.columns:
        logger.warning(f"Subject column '{subject_col}' not found. Skipping trial validation.")
        return df

    trial_counts = df.groupby(subject_col).size()
    
    insufficient = trial_counts[trial_counts < min_trials]
    
    if len(insufficient) > 0:
        if aggregate_flag:
            logger.warning(f"Found {len(insufficient)} subjects with < {min_trials} trials. "
                           f"Aggregating across subjects as per config.")
            # Drop subject column to aggregate
            if subject_col in df.columns:
                df = df.drop(columns=[subject_col])
            return df
        else:
            # Raise error for the first insufficient subject found
            bad_subject = insufficient.index[0]
            count = insufficient.iloc[0]
            raise RuntimeError(f"Subject {bad_subject} has {count} trials (< {min_trials}). "
                               f"Set aggregation flag in config.yaml to True to aggregate across subjects.")
    
    return df

def fit_lme_model(df: pd.DataFrame, formula: str, random_effect: str = "1|subject_id") -> Any:
    """
    Fit a Linear Mixed Effects model.
    
    Args:
        df: Dataframe.
        formula: Statsmodels formula string (e.g., "pupil ~ search_time + fixation_count").
        random_effect: Random effect specification.
        
    Returns:
        Fitted model result.
    """
    try:
        model = mixedlm(formula, df, groups=df["subject_id"])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        raise

def likelihood_ratio_test(full_model: Any, reduced_model: Any) -> Dict[str, float]:
    """
    Perform likelihood ratio test between two models.
    
    Args:
        full_model: The full fitted model.
        reduced_model: The reduced (nested) fitted model.
        
    Returns:
        Dict with 'chi2_statistic' and 'p_value'.
    """
    try:
        lr_stat = 2 * (full_model.llf - reduced_model.llf)
        # Degrees of freedom difference (simplified, assumes 1 df diff for single param drop)
        # In practice, calculate df_diff based on parameters
        df_diff = len(full_model.params) - len(reduced_model.params)
        from scipy.stats import chi2
        p_val = 1 - chi2.cdf(lr_stat, df_diff)
        return {'chi2_statistic': lr_stat, 'p_value': p_val}
    except Exception as e:
        logger.error(f"Likelihood ratio test failed: {e}")
        return {'chi2_statistic': 0.0, 'p_value': 1.0}

def save_model_summary(result: Any, dropped_predictor: Optional[str], output_path: str):
    """
    Save model summary to CSV.
    
    Schema:
    - predictor, coef, std_err, p_value, dropped_predictor
    """
    summary_data = []
    
    if hasattr(result, 'summary2') or hasattr(result, 'summary'):
        # Extract fixed effects
        if hasattr(result, 'fe_params'):
            params = result.fe_params
            bse = result.bse
            pvals = result.pvalues
            
            for i, (pred, coef) in enumerate(params.items()):
                summary_data.append({
                    'predictor': pred,
                    'coef': float(coef),
                    'std_err': float(bse.iloc[i]) if i < len(bse) else 0.0,
                    'p_value': float(pvals.iloc[i]) if i < len(pvals) else 1.0,
                    'dropped_predictor': dropped_predictor
                })
    
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Model summary saved to {output_path}")

def run_lme_pipeline(input_path: str, output_path: str, config: Dict[str, Any]):
    """
    Main pipeline for US2: LME Model fitting.
    
    Steps:
    1. Load data.
    2. Validate sufficient trials (T024 logic).
    3. Handle unfulfillable predictors.
    4. Mitigate collinearity (VIF check).
    5. Fit model.
    6. Save summary.
    """
    logger.info("Starting LME Pipeline")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # T024: Validate trials
    min_trials = config.get('thresholds', {}).get('min_trials', 20)
    aggregate = config.get('aggregation', {}).get('enabled', False)
    
    try:
        df = validate_sufficient_trials(df, min_trials=min_trials, aggregate_flag=aggregate)
    except RuntimeError as e:
        logger.error(str(e))
        raise
    
    # Define predictors (example: from features.csv columns)
    # In a real scenario, these would be derived from the data schema
    potential_predictors = ['search_time', 'fixation_count', 'target_salience']
    valid_predictors = [p for p in potential_predictors if p in df.columns]
    
    # Handle unfulfillable
    valid_predictors, dropped_unfulfillable = handle_unfulfillable_predictors(df, valid_predictors)
    
    if len(valid_predictors) == 0:
        logger.error("No valid predictors remaining after filtering.")
        raise ValueError("No valid predictors for LME model.")
    
    # Mitigate collinearity
    vif_threshold = config.get('thresholds', {}).get('vif', 5.0)
    final_predictors, dropped_vif = mitigate_collinearity(df, valid_predictors, threshold=vif_threshold)
    
    dropped_predictor = dropped_vif or (dropped_unfulfillable[0] if dropped_unfulfillable else None)
    
    # Construct formula
    formula = "pupil_diameter ~ " + " + ".join(final_predictors)
    
    # Fit model
    logger.info(f"Fitting model: {formula}")
    model_result = fit_lme_model(df, formula)
    
    # Save summary
    save_model_summary(model_result, dropped_predictor, output_path)
    
    logger.info("LME Pipeline completed successfully.")

def main():
    """Entry point for script execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LME Model Pipeline")
    parser.add_argument('--input', type=str, required=True, help='Input CSV path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV path')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    run_lme_pipeline(args.input, args.output, config)

if __name__ == "__main__":
    main()