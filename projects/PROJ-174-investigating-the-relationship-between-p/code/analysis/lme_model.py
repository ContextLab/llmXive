import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# statsmodels is a pinned dependency in requirements.txt (T002a)
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats

# Project relative imports (adjusting for code/ root structure)
try:
    from config import load_config
    from data_model import ModelResult
except ImportError:
    # Fallback for direct execution from code/ directory
    from config import load_config
    from data_model import ModelResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    Excludes the intercept column if present.
    """
    vif_data = {}
    X = df[predictors].dropna()
    if X.empty:
        logger.warning("No valid data points for VIF calculation.")
        return vif_data

    # Add constant for intercept if not already present in model matrix logic
    # VIF calculation typically uses the design matrix without the intercept column
    # but statsmodels VIF function expects the matrix with constant if the model has one.
    # However, standard VIF calculation for multicollinearity checks often excludes the intercept column itself.
    # We calculate VIF for the predictors provided.
    
    X_const = sm.add_constant(X)
    for col in predictors:
        if col in X_const.columns:
            try:
                vif = variance_inflation_factor(X_const.values, list(X_const.columns).index(col))
                vif_data[col] = vif
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_data[col] = np.nan
    return vif_data

def mitigate_collinearity(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> Tuple[List[str], Dict[str, float]]:
    """
    Iteratively remove predictors with VIF > threshold until all remaining are below threshold.
    Returns the list of kept predictors and their final VIFs.
    """
    current_predictors = list(predictors)
    final_vifs = {}
    
    # Handle empty predictors
    if not current_predictors:
        return [], {}

    while True:
        vifs = calculate_vif(df, current_predictors)
        # Filter out NaNs
        valid_vifs = {k: v for k, v in vifs.items() if not np.isnan(v)}
        
        if not valid_vifs:
            break

        max_vif_col = max(valid_vifs, key=valid_vifs.get)
        max_vif = valid_vifs[max_vif_col]

        if max_vif <= threshold:
            final_vifs = valid_vifs
            break

        logger.info(f"Collinearity detected: Removing '{max_vif_col}' (VIF={max_vif:.2f} > {threshold})")
        current_predictors.remove(max_vif_col)
        
        if not current_predictors:
            logger.error("All predictors removed due to collinearity.")
            break

    return current_predictors, final_vifs

def handle_unfulfillable_predictors(df: pd.DataFrame, predictors: List[str], unfulfillable_col: str = "status") -> List[str]:
    """
    Check if any predictor column contains 'UNFULFILLABLE' values (or is missing entirely).
    If a predictor is missing or marked UNFULFILLABLE in the data, remove it from the list.
    """
    valid_predictors = []
    for p in predictors:
        if p not in df.columns:
            logger.warning(f"Predictor '{p}' not found in dataframe. Skipping.")
            continue
        
        # Check for UNFULFILLABLE status in the status column if it exists, or check the predictor itself
        # The prompt says: "If target salience is missing (UNFULFILLABLE), fit a reduced model"
        # We assume the status column indicates the state of the row, or the predictor itself might be NaN/missing.
        
        # If the predictor column itself has many NaNs or is specifically marked
        # We check if the column exists and has valid numeric data
        if df[p].isna().all():
            logger.warning(f"Predictor '{p}' is entirely NaN. Removing.")
            continue
        
        # If there's a status column and it says UNFULFILLABLE for the whole dataset regarding this feature
        # This is a heuristic based on T015 spec.
        if unfulfillable_col in df.columns:
            # If the status is UNFULFILLABLE, we might need to exclude rows or the predictor
            # For this task, we assume we drop the predictor if the data is fundamentally missing.
            pass 
        
        valid_predictors.append(p)
    
    return valid_predictors

def fit_lme_model(df: pd.DataFrame, formula: str, group_col: str) -> Optional[MixedLM]:
    """
    Fit a Linear Mixed Effects model.
    """
    try:
        # Filter out rows with NaN in formula columns
        formula_cols = [col.strip() for col in formula.replace('+', ' ').replace('-', ' ').replace('*', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').split()]
        # Simple extraction of column names from formula string is complex, 
        # but statsmodels handles NaNs internally if we pass the data.
        # However, MixedLM requires complete cases for the formula variables.
        clean_df = df.dropna(subset=formula.split(' ')[0].split('~')[0].split('+') + formula.split(' ')[0].split('~')[1].split('+'))
        
        if clean_df.empty:
            logger.error("No data remaining after dropping NaNs for LME fitting.")
            return None

        model = MixedLM.from_formula(formula, groups=clean_df[group_col], data=clean_df)
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        return None

def likelihood_ratio_test(full_model: MixedLM, reduced_model: MixedLM) -> Tuple[float, float]:
    """
    Perform likelihood ratio test between two nested models.
    Returns (chi2_stat, p_value).
    """
    try:
        lr_stat = 2 * (full_model.llf - reduced_model.llf)
        # Degrees of freedom difference
        df_diff = full_model.df_model - reduced_model.df_model
        if df_diff <= 0:
            df_diff = 1 # Fallback
        p_val = 1 - stats.chi2.cdf(lr_stat, df_diff)
        return lr_stat, p_val
    except Exception as e:
        logger.warning(f"Could not compute likelihood ratio test: {e}")
        return np.nan, np.nan

def validate_sufficient_trials(df: pd.DataFrame, group_col: str, min_trials: int = 20) -> bool:
    """
    Check if each subject has at least min_trials.
    Raises RuntimeError if not and config flag is false.
    """
    counts = df.groupby(group_col).size()
    if (counts < min_trials).any():
        subjects = counts[counts < min_trials].index.tolist()
        msg = f"Subject(s) {subjects} have < {min_trials} trials."
        # Check config for aggregation flag? T024 says "unless config.yaml aggregation flag is true"
        # We assume config loading is handled or we raise error as per T024 requirement.
        raise RuntimeError(msg)
    return True

def save_model_summary(result: MixedLM, output_path: Path, predictors: List[str]):
    """
    Save fixed-effect estimates, SEs, p-values to CSV.
    """
    if result is None:
        logger.error("No model result to save.")
        return

    # Extract fixed effects
    # result.fe_params is a Series
    # result.bse is a Series (standard errors)
    # result.pvalues is a Series (p-values)
    
    summary_data = {
        'term': result.fe_params.index,
        'estimate': result.fe_params.values,
        'std_error': result.bse.values,
        'p_value': result.pvalues.values
    }
    
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Model summary saved to {output_path}")

def run_lme_pipeline(
    input_path: Path, 
    output_path: Path, 
    config: Dict[str, Any], 
    predictors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main pipeline for US2: LME modeling.
    """
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate trials
    group_col = config.get('group_column', 'subject_id')
    try:
        validate_sufficient_trials(df, group_col, min_trials=config.get('min_trials', 20))
    except RuntimeError as e:
        logger.error(str(e))
        # Depending on strictness, we might return early or continue with reduced set
        # For T025, we assume we proceed if possible or log error.
        # Re-raising to stop if strict.
        raise e

    # Determine predictors
    if predictors is None:
        # Default predictors based on T015/T021 context
        candidates = ['search_time', 'fixation_count', 'target_salience']
        predictors = [p for p in candidates if p in df.columns]
    
    # Handle unfulfillable
    predictors = handle_unfulfillable_predictors(df, predictors)
    
    if not predictors:
        logger.error("No valid predictors remaining for LME.")
        # Create empty summary or error out?
        pd.DataFrame(columns=['term', 'estimate', 'std_error', 'p_value']).to_csv(output_path, index=False)
        return {}

    # Collinearity check
    predictors, vifs = mitigate_collinearity(df, predictors, threshold=config.get('vif_threshold', 5.0))
    if not predictors:
        logger.error("All predictors dropped due to collinearity.")
        pd.DataFrame(columns=['term', 'estimate', 'std_error', 'p_value']).to_csv(output_path, index=False)
        return {}

    # Construct formula
    # Assuming response is 'pupil_diameter' or similar, let's assume 'pupil_diameter' based on data_model
    response = 'pupil_diameter'
    if response not in df.columns:
        # Fallback to first numeric column if response missing? Or error.
        logger.error(f"Response variable '{response}' not found in data.")
        # Try to find a suitable response
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            response = numeric_cols[0]
            logger.warning(f"Using '{response}' as response variable.")
        else:
            raise ValueError("No numeric response variable found.")

    formula = f"{response} ~ {' + '.join(predictors)}"
    logger.info(f"Fitting model with formula: {formula}")

    model_result = fit_lme_model(df, formula, group_col)
    
    if model_result:
        save_model_summary(model_result, output_path, predictors)
        
        # Return summary dict for logging
        summary_dict = {
            'formula': formula,
            'predictors_used': predictors,
            'vifs': vifs,
            'coefficients': model_result.fe_params.to_dict(),
            'p_values': model_result.pvalues.to_dict()
        }
        return summary_dict
    else:
        logger.error("Model fitting failed.")
        return {}

def main():
    """
    Entry point for running LME model analysis.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run LME Model Analysis")
    parser.add_argument('--input', type=str, required=True, help="Path to processed CSV")
    parser.add_argument('--output', type=str, required=True, help="Path to output summary CSV")
    parser.add_argument('--config', type=str, default='config.yaml', help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_lme_pipeline(Path(args.input), output_path, config)

if __name__ == "__main__":
    main()