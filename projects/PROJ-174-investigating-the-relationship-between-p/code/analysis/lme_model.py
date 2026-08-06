import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Ensure parent directory is in path for relative imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config
from data_model import ModelResult

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    """
    vif_data = {}
    # Add intercept for VIF calculation context (though statsmodels handles it)
    X = df[predictors].copy()
    
    # Handle potential constant column if present in predictors
    if 'intercept' in X.columns:
        X = X.drop(columns=['intercept'])
        
    if X.shape[1] == 0:
        return {}

    for feature in X.columns:
        try:
            # Fit linear model of this feature against others
            y = X[feature]
            X_others = X.drop(columns=[feature])
            # Add constant for regression
            X_others_with_const = sm.add_constant(X_others)
            
            # Check for singular matrix or perfect collinearity
            if X_others_with_const.shape[1] > 1:
                model = sm.OLS(y, X_others_with_const).fit()
                vif_data[feature] = 1 / (1 - model.rsquared)
            else:
                # Only one other variable (or none), VIF is not meaningful or 1
                vif_data[feature] = 1.0
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
            
    return vif_data

def mitigate_collinearity(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> Tuple[List[str], List[str]]:
    """
    If any VIF > threshold, drop the predictor with the highest VIF and refit.
    Returns (remaining_predictors, dropped_predictors).
    """
    remaining = list(predictors)
    dropped = []
    current_df = df.copy()
    
    # Filter out any predictors that might have been marked as UNFULFILLABLE or NaN
    # We assume the dataframe passed here is already cleaned or we handle NaNs in fit
    
    iteration = 0
    max_iterations = len(remaining)
    
    while iteration < max_iterations:
        iteration += 1
        if len(remaining) <= 1:
            break
            
        vif_scores = calculate_vif(current_df, remaining)
        if not vif_scores:
            break
            
        max_vif_var = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_var]
        
        logger.info(f"Iteration {iteration}: Max VIF = {max_vif:.2f} for {max_vif_var}")
        
        if max_vif <= threshold:
            break
            
        logger.warning(f"VIF {max_vif:.2f} > {threshold} for {max_vif_var}. Dropping predictor.")
        dropped.append(max_vif_var)
        remaining.remove(max_vif_var)
        
    return remaining, dropped

def handle_unfulfillable_predictors(df: pd.DataFrame, predictors: List[str]) -> Tuple[List[str], List[str]]:
    """
    If target salience is missing (UNFULFILLABLE), fit a reduced model excluding that predictor.
    Returns (used_predictors, excluded_predictors).
    """
    used = []
    excluded = []
    
    for p in predictors:
        # Check if column exists and has valid data
        if p not in df.columns:
            logger.warning(f"Predictor {p} not found in dataframe. Excluding.")
            excluded.append(p)
            continue
        
        # Check for 'UNFULFILLABLE' marker in the data if it's a categorical status, 
        # or simply check if the column is all NaN/missing for the relevant rows
        # Assuming the column exists but might be all NaN or marked specifically
        if df[p].isna().all() or (df[p] == 'UNFULFILLABLE').any():
            logger.warning(f"Predictor {p} is UNFULFILLABLE or missing. Excluding from model.")
            excluded.append(p)
        else:
            used.append(p)
            
    return used, excluded

def validate_sufficient_trials(df: pd.DataFrame, subject_col: str = 'subject_id', min_trials: int = 20) -> bool:
    """
    Validate sufficient trials per subject.
    Raises RuntimeError if any subject has < min_trials unless aggregation is allowed.
    """
    # Check config for aggregation flag
    try:
        config = load_config()
        allow_aggregation = config.get('thresholds', {}).get('allow_aggregation', False)
    except Exception:
        allow_aggregation = False

    trial_counts = df.groupby(subject_col).size()
    min_count = trial_counts.min()
    
    if min_count < min_trials:
        if allow_aggregation:
            logger.warning(f"Minimum trials per subject is {min_count} (< {min_trials}). Aggregation flag is True, proceeding with caution.")
            return True
        else:
            subject_with_low = trial_counts[trial_counts < min_trials].index[0]
            raise RuntimeError(f"Subject {subject_with_low} has < {min_trials} trials. Pipeline halted.")
            
    return True

def fit_lme_model(df: pd.DataFrame, formula: str, random_effect: str = '(1|subject_id)') -> sm.regression.mixed_linear_model.MixedLMResults:
    """
    Fit the Linear Mixed Effects model.
    """
    try:
        # Handle categorical variables if needed, statsmodels formula API handles this usually
        # Ensure numeric columns are numeric
        numeric_df = df.apply(pd.to_numeric, errors='ignore')
        
        model = smf.mixedlm(formula, numeric_df, groups=numeric_df['subject_id'])
        result = model.fit(reml=False) # Using ML for likelihood ratio test compatibility
        return result
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        raise

def likelihood_ratio_test(model_full, model_reduced) -> Dict[str, float]:
    """
    Perform likelihood-ratio test comparing nested models.
    Returns dict with chi2 statistic and p-value.
    """
    ll_full = model_full.llf
    ll_reduced = model_reduced.llf
    df_diff = model_full.df_model - model_reduced.df_model # Approximate df diff for fixed effects
    
    # Calculate Chi-squared statistic
    chi2_stat = 2 * (ll_full - ll_reduced)
    p_value = 1 - stats.chi2.cdf(chi2_stat, df_diff)
    
    return {
        'chi2_statistic': chi2_stat,
        'df_diff': df_diff,
        'p_value': p_value
    }

def save_model_summary(result: sm.regression.mixed_linear_model.MixedLMResults, 
                       predictors: List[str], 
                       output_path: Path,
                       lrt_result: Optional[Dict[str, float]] = None,
                       dropped_predictors: Optional[List[str]] = None):
    """
    Output fixed-effect estimates, SEs, p-values to results/model_summary.csv.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    # Extract fixed effects parameters
    # The result object has 'params' and 'bse'
    # 'params' index includes intercept and predictors
    summary_data = []
    
    # Get parameter names
    param_names = result.params.index.tolist()
    
    for name in param_names:
        # Skip random effects parameters if they appear in params (usually they don't in the main params index for fixed)
        # But 'group' variance might be there. We focus on fixed effects.
        if name.startswith('group') or name.startswith('Scale'):
            continue
            
        coef = result.params[name]
        std_err = result.bse[name] if name in result.bse.index else 0.0
        p_val = result.pvalues[name] if name in result.pvalues.index else 1.0
        
        summary_data.append({
            'term': name,
            'estimate': coef,
            'std_error': std_err,
            'p_value': p_val
        })
        
    df_summary = pd.DataFrame(summary_data)
    
    # Add metadata columns
    df_summary['model_type'] = 'LME'
    df_summary['dropped_predictors'] = ';'.join(dropped_predictors) if dropped_predictors else 'None'
    if lrt_result:
        df_summary['lrt_chi2'] = lrt_result.get('chi2_statistic', np.nan)
        df_summary['lrt_p_value'] = lrt_result.get('p_value', np.nan)
    else:
        df_summary['lrt_chi2'] = np.nan
        df_summary['lrt_p_value'] = np.nan
        
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Model summary saved to {output_path}")

def run_lme_pipeline(input_path: Path, output_path: Path, config: Dict[str, Any]) -> None:
    """
    Main pipeline for US2: LME model fitting.
    """
    logger.info("Starting LME Pipeline")
    
    # Load data
    if not input_path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Validate trials
    validate_sufficient_trials(df, min_trials=config.get('thresholds', {}).get('min_trials_per_subject', 20))
    
    # Define predictors and outcome
    # Assuming standard columns from US1 processing
    outcome = 'pupil_diameter' # Or mean/peak as determined by config
    base_predictors = ['search_time', 'fixation_count', 'target_salience']
    
    # Handle unfulfillable
    used_predictors, excluded_predictors = handle_unfulfillable_predictors(df, base_predictors)
    
    if not used_predictors:
        logger.error("No valid predictors remaining after filtering unfulfillable ones.")
        # Create empty summary or minimal
        pd.DataFrame({'term': [], 'estimate': [], 'std_error': [], 'p_value': []}).to_csv(output_path, index=False)
        return

    # Mitigate collinearity
    final_predictors, dropped_predictors = mitigate_collinearity(df, used_predictors, threshold=config.get('thresholds', {}).get('vif_threshold', 5.0))
    
    if not final_predictors:
        logger.error("No predictors remaining after collinearity mitigation.")
        pd.DataFrame({'term': [], 'estimate': [], 'std_error': [], 'p_value': []}).to_csv(output_path, index=False)
        return

    # Construct formula
    # Fixed effects: outcome ~ predictor1 + predictor2 ...
    # Random effects: (1|subject_id)
    formula = f"{outcome} ~ {' + '.join(final_predictors)}"
    logger.info(f"Fitting formula: {formula}")
    
    # Fit model
    model_result = fit_lme_model(df, formula)
    
    # Likelihood Ratio Test (if we had a reduced model, but task says compare nested)
    # For this task, we compare the full model against a null model (intercept only)
    null_formula = f"{outcome} ~ 1"
    try:
        null_model = fit_lme_model(df, null_formula)
        lrt_res = likelihood_ratio_test(model_result, null_model)
    except Exception as e:
        logger.warning(f"Could not perform LRT: {e}")
        lrt_res = None
        
    # Save results
    save_model_summary(model_result, final_predictors, output_path, lrt_res, dropped_predictors)
    
    logger.info("LME Pipeline completed successfully.")

def main():
    """
    Entry point for LME model fitting.
    """
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    
    # Default paths based on project structure
    input_file = Path("data/processed/processed_features.csv") # Assumes US1 output
    output_file = Path("results/model_summary.csv")
    
    # Allow CLI override
    import argparse
    parser = argparse.ArgumentParser(description="Run LME Model Analysis")
    parser.add_argument("--input", type=str, help="Path to processed features CSV")
    parser.add_argument("--output", type=str, help="Path to output summary CSV")
    args = parser.parse_args()
    
    if args.input:
        input_file = Path(args.input)
    if args.output:
        output_file = Path(args.output)
        
    run_lme_pipeline(input_file, output_file, config)

if __name__ == "__main__":
    main()
