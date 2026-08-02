import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    """
    if len(predictors) == 0:
        return pd.Series([], dtype=float)

    X = df[predictors].dropna()
    if X.empty:
        return pd.Series(index=predictors, dtype=float)

    # Add constant for intercept if needed for VIF calculation
    X_const = sm.add_constant(X)
    vif_data = []
    for col in predictors:
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col))
            vif_data.append(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append(np.inf)

    return pd.Series(vif_data, index=predictors)

def mitigate_collinearity(df: pd.DataFrame, predictors: List[str], vif_threshold: float = 5.0) -> Tuple[List[str], Dict[str, float]]:
    """
    Iteratively remove predictors with VIF > threshold until all are below threshold.
    Returns the list of kept predictors and a log of removed ones.
    """
    kept = list(predictors)
    removal_log = {}

    while True:
        if len(kept) == 0:
            logger.warning("All predictors removed due to collinearity.")
            break

        vifs = calculate_vif(df, kept)
        max_vif_idx = vifs.idxmax()
        max_vif = vifs[max_vif_idx]

        if max_vif <= vif_threshold:
            break

        logger.info(f"Removing {max_vif_idx} (VIF={max_vif:.2f} > {vif_threshold})")
        removal_log[max_vif_idx] = max_vif
        kept.remove(max_vif_idx)

    return kept, removal_log

def handle_unfulfillable_predictors(df: pd.DataFrame, predictors: List[str]) -> Tuple[List[str], bool]:
    """
    Check if target_salience is present and not marked UNFULFILLABLE.
    If missing/unfulfillable, remove from predictors and log.
    """
    final_predictors = []
    salience_missing = False

    for p in predictors:
        if p == 'target_salience':
            if 'target_salience' not in df.columns:
                logger.warning("target_salience column missing. Excluding from model.")
                salience_missing = True
                continue
            # Check if all values are UNFULFILLABLE or NaN
            if df['target_salience'].isna().all() or (df['target_salience'] == 'UNFULFILLABLE').all():
                logger.warning("target_salience is UNFULFILLABLE for all trials. Excluding from model.")
                salience_missing = True
                continue
        final_predictors.append(p)

    return final_predictors, salience_missing

def validate_sufficient_trials(df: pd.DataFrame, subject_col: str = 'subject_id', min_trials: int = 20, allow_aggregation: bool = False) -> None:
    """
    Validate that each subject has at least min_trials.
    Raises RuntimeError if not met and aggregation is not allowed.
    """
    if allow_aggregation:
        logger.info("Aggregation flag is true. Skipping strict trial count validation.")
        return

    counts = df.groupby(subject_col).size()
    insufficient = counts[counts < min_trials]
    if not insufficient.empty:
        msg = f"Subjects with insufficient trials (< {min_trials}): {insufficient.to_dict()}"
        logger.error(msg)
        raise RuntimeError(msg)

def fit_lme_model(df: pd.DataFrame, formula: str, random_effect: str = '(1|subject_id)') -> smf.mixedlm.MixedLMResults:
    """
    Fit a Linear Mixed-Effects model.
    """
    try:
        model = smf.mixedlm(formula, df, groups=df['subject_id'])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        raise

def likelihood_ratio_test(full_result, reduced_result) -> Dict[str, float]:
    """
    Perform likelihood-ratio test between two nested models.
    """
    lr_stat = 2 * (full_result.llf - reduced_result.llf)
    # Degrees of freedom difference (approximate)
    df_diff = len(full_result.fe_params) - len(reduced_result.fe_params)
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(lr_stat, df_diff)
    return {'lr_statistic': lr_stat, 'df_diff': df_diff, 'p_value': p_value}

def save_model_summary(result: smf.mixedlm.MixedLMResults, output_path: Path, predictors: List[str]) -> None:
    """
    Extract fixed-effect estimates, SEs, p-values and save to CSV.
    """
    # Extract fixed effects table
    # result.summary2() gives a nice table, but we need to parse programmatically
    # Using result.params, result.bse, and result.pvalues if available
    # Note: statsmodels mixedlm pvalues might need manual calculation or summary parsing
    # For now, we assume standard attributes exist or derive from t-values

    params = result.params
    bse = result.bse
    
    # Handle case where p-values are not directly available in some versions
    # Calculate from t-values if necessary: t = param / bse
    # p-value = 2 * (1 - cdf(|t|))
    try:
        p_vals = result.pvalues
    except AttributeError:
        t_vals = params / bse
        from scipy.stats import norm
        p_vals = 2 * (1 - norm.cdf(np.abs(t_vals)))

    # Filter for fixed effects only (exclude intercept if needed, but usually kept)
    # The params index usually contains 'Intercept', 'predictor1', 'predictor2'
    # We need to map these to our original predictor names if possible
    
    data = []
    for name, param in params.items():
        if name.startswith('Group var'): # Skip random effect variances
            continue
        
        # Clean name if it has random effect suffix or similar
        clean_name = name
        if 'group' in clean_name.lower():
            continue
            
        # Check if this is one of our predictors or intercept
        if clean_name == 'Intercept':
            term_name = 'Intercept'
        else:
            # Assume direct mapping for fixed effects
            term_name = clean_name

        data.append({
            'term': term_name,
            'estimate': param,
            'std_error': bse[name],
            'p_value': p_vals[name]
        })

    df_summary = pd.DataFrame(data)
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Model summary saved to {output_path}")

def run_lme_pipeline(data_path: Path, output_path: Path, config: Dict[str, Any]) -> None:
    """
    Main pipeline for User Story 2: LME modeling.
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Validate trials
    validate_sufficient_trials(df, min_trials=config.get('min_trials', 20))

    # Define predictors based on config or defaults
    base_predictors = config.get('predictors', ['search_time', 'fixation_count', 'target_salience'])
    
    # Handle unfulfillable
    final_predictors, salience_missing = handle_unfulfillable_predictors(df, base_predictors)
    
    if salience_missing:
        logger.info("Fitting reduced model without target_salience.")

    # Check collinearity
    final_predictors, removal_log = mitigate_collinearity(df, final_predictors, vif_threshold=config.get('vif_threshold', 5.0))

    if len(final_predictors) == 0:
        raise RuntimeError("No predictors left after collinearity mitigation.")

    # Construct formula
    # Assuming dependent variable is 'pupil_diameter' or similar, check config or default
    dep_var = config.get('dependent_variable', 'pupil_diameter')
    formula = f"{dep_var} ~ {' + '.join(final_predictors)}"

    logger.info(f"Fitting model: {formula}")
    result = fit_lme_model(df, formula)

    # Save summary
    save_model_summary(result, output_path, final_predictors)

    # Optional: Log likelihood ratio test if a reduced model was conceptually fitted
    # (Not implemented here as per strict task scope, but structure is in place)

def main():
    """
    Entry point for script execution.
    """
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Run LME Analysis Pipeline")
    parser.add_argument("--data", type=str, required=True, help="Path to processed CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = {}
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f) or {}

    run_lme_pipeline(Path(args.data), Path(args.output), config)

if __name__ == "__main__":
    main()