import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Attempt to import statsmodels; fail loudly if missing (required dependency)
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    raise ImportError(
        "statsmodels is required for LME modeling. "
        "Please install it via `pip install statsmodels`."
    )

from config import load_config

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    Returns a dictionary mapping feature name to VIF value.
    """
    vif_data = {}
    # Prepare data: drop rows with NaN in any selected feature
    clean_df = df[features].dropna()
    if len(clean_df) == 0:
        logger.warning("No valid data for VIF calculation (all NaN).")
        return {f: float('inf') for f in features}

    X = clean_df[features]
    # Add intercept for VIF calculation context (though VIF is usually on centered data)
    # Standard approach: regress each X_j against all other X_k
    for i, feature in enumerate(features):
        y = X[feature]
        X_other = X[[f for f in features if f != feature]]
        if X_other.shape[1] == 0:
            vif_data[feature] = 1.0
            continue

        # Fit OLS
        model = sm.OLS(y, sm.add_constant(X_other)).fit()
        r_squared = model.rsquared
        vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
        vif_data[feature] = vif

    return vif_data

def mitigate_collinearity(
    df: pd.DataFrame,
    predictors: List[str],
    vif_threshold: float = 5.0
) -> List[str]:
    """
    Iteratively drop the predictor with the highest VIF if VIF > threshold.
    Returns the list of remaining predictors.
    """
    remaining = list(predictors)
    while len(remaining) > 1:
        vif_scores = calculate_vif(df, remaining)
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_feature]

        if max_vif <= vif_threshold:
            break

        logger.warning(
            f"Collinearity detected: {max_vif_feature} has VIF={max_vif:.2f} > {vif_threshold}. Dropping."
        )
        remaining.remove(max_vif_feature)

    return remaining

def handle_unfulfillable_predictors(
    df: pd.DataFrame,
    predictors: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Identify predictors that are entirely UNFULFILLABLE (all NaN or marked).
    Returns (remaining_predictors, dropped_predictors).
    """
    remaining = []
    dropped = []
    for p in predictors:
        if p not in df.columns:
            dropped.append(p)
            continue
        # Check if column is all NaN or marked as 'UNFULFILLABLE'
        if df[p].isna().all():
            dropped.append(p)
            logger.warning(f"Predictor {p} is entirely missing/UNFULFILLABLE. Dropping.")
        else:
            remaining.append(p)
    return remaining, dropped

def validate_sufficient_trials(
    df: pd.DataFrame,
    subject_col: str = 'subject_id',
    min_trials: int = 20,
    allow_aggregation: bool = False
) -> None:
    """
    Validate that each subject has at least `min_trials` trials.
    If a subject has fewer, raises RuntimeError unless allow_aggregation is True.
    
    Args:
        df: The dataframe containing trial-level data.
        subject_col: Name of the column identifying subjects.
        min_trials: Minimum number of trials required per subject.
        allow_aggregation: If True, log a warning but do not raise.
    """
    if subject_col not in df.columns:
        raise ValueError(f"Subject column '{subject_col}' not found in dataframe.")

    trial_counts = df[subject_col].value_counts()
    insufficient_subjects = trial_counts[trial_counts < min_trials].index.tolist()

    if insufficient_subjects:
        msg = (
            f"Subjects with insufficient trials (< {min_trials}): {insufficient_subjects}. "
            f"Counts: {trial_counts[trial_counts < min_trials].to_dict()}"
        )
        
        if not allow_aggregation:
            raise RuntimeError(f"Subject validation failed: {msg}")
        else:
            logger.warning(f"Aggregation allowed. Warning: {msg}")

def fit_lme_model(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
    subject_col: str = 'subject_id'
) -> sm.lme.LinearMixedEffects:
    """
    Fit a Linear Mixed Effects model.
    Formula: outcome ~ predictor1 + predictor2 + ... | (1 | subject_col)
    """
    if not predictors:
        raise ValueError("Cannot fit model with no predictors.")
    
    formula = f"{outcome} ~ {' + '.join(predictors)}"
    # Random intercept by subject
    formula += f" + (1 | {subject_col})"
    
    # Handle potential NaNs in the specific columns used for the model
    # statsmodels LME handles NaNs poorly, so we drop them first
    cols_to_check = [outcome] + predictors + [subject_col]
    valid_df = df[cols_to_check].dropna()
    
    if len(valid_df) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for LME fit.")
    
    model = smf.lme(formula, data=valid_df, re_formula=f"1 | {subject_col}")
    try:
        fitted = model.fit()
    except Exception as e:
        logger.error(f"LME fitting failed: {e}")
        raise
    
    return fitted

def likelihood_ratio_test(
    model_full: sm.lme.LinearMixedEffects,
    model_reduced: sm.lme.LinearMixedEffects
) -> Tuple[float, float]:
    """
    Perform Likelihood Ratio Test comparing two nested models.
    Returns (chi2_statistic, p_value).
    """
    # Note: statsmodels LME fit objects have llf (log likelihood)
    ll_full = model_full.llf
    ll_reduced = model_reduced.llf
    
    # Degrees of freedom difference (number of fixed effects parameters difference)
    # This is a simplification; exact df diff depends on specific parameter counts
    # For a simple drop of one predictor, df_diff = 1.
    # Here we approximate by comparing parameter counts if available, or assume 1 if not.
    # A robust implementation would compare the number of fixed effects coefficients.
    k_full = model_full.fe_params.shape[0]
    k_reduced = model_reduced.fe_params.shape[0]
    df_diff = k_full - k_reduced
    
    if df_diff <= 0:
        raise ValueError("Models are not nested or reduced model has more params.")
    
    chi2 = 2 * (ll_full - ll_reduced)
    # P-value from Chi-square distribution
    from scipy.stats import chi2 as chi2_dist
    p_value = 1 - chi2_dist.cdf(chi2, df_diff)
    
    return chi2, p_value

def save_model_summary(
    model: sm.lme.LinearMixedEffects,
    output_path: Path,
    predictors: List[str]
) -> None:
    """
    Extract fixed effects estimates, SEs, p-values and save to CSV.
    """
    summary_df = model.summary().tables[1].as_frame() # type: ignore
    # Filter for fixed effects only (usually all in this context)
    # Ensure we only output the requested predictors
    
    rows = []
    for param_name, row in summary_df.iterrows():
        if any(p in param_name for p in predictors) or param_name == "Intercept":
            rows.append({
                "parameter": param_name,
                "estimate": row["coef"],
                "std_error": row["std err"],
                "p_value": row["P>|t|"]
            })
    
    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_path, index=False)
    logger.info(f"Model summary saved to {output_path}")

def run_lme_pipeline(
    input_path: Path,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Main pipeline for User Story 2:
    1. Load data
    2. Validate trials per subject
    3. Handle unfulfillable predictors
    4. Mitigate collinearity (VIF)
    5. Fit model
    6. Save summary
    """
    if config is None:
        config = load_config()
    
    # Load data
    if not input_path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    df = pd.read_csv(input_path)
    
    # Configuration values
    min_trials = config.get('thresholds', {}).get('min_trials_per_subject', 20)
    allow_agg = config.get('flags', {}).get('allow_aggregation', False)
    vif_thresh = config.get('thresholds', {}).get('vif_threshold', 5.0)
    
    # 1. Validate sufficient trials
    validate_sufficient_trials(df, min_trials=min_trials, allow_aggregation=allow_agg)
    
    # Define outcome and potential predictors (standard for this project)
    outcome = "pupil_diameter" # Or mean/peak depending on preprocessing
    # Predictors typically: search_time, fixation_count, target_salience
    potential_predictors = ["search_time", "fixation_count", "target_salience"]
    
    # 2. Handle unfulfillable predictors
    available_predictors, dropped = handle_unfulfillable_predictors(df, potential_predictors)
    
    if len(available_predictors) == 0:
        raise ValueError("No valid predictors available for modeling.")
    
    # 3. Mitigate collinearity
    final_predictors = mitigate_collinearity(df, available_predictors, vif_threshold=vif_thresh)
    
    logger.info(f"Fitting LME with predictors: {final_predictors}")
    
    # 4. Fit Model
    model = fit_lme_model(df, outcome=outcome, predictors=final_predictors)
    
    # 5. Save Summary
    save_model_summary(model, output_path, final_predictors)
    
    # Optional: Run LRT if a reduced model is specified (e.
    # g., without salience)
    # For now, we just save the full summary as per T025/T024 requirements

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run LME Analysis Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to processed CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to save model summary")
    args = parser.parse_args()
    
    setup_logging()
    run_lme_pipeline(Path(args.input), Path(args.output))

if __name__ == "__main__":
    main()
