import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
import scipy.stats as stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def load_grouping_validation(validation_path):
    """Load grouping validation JSON."""
    if not os.path.exists(validation_path):
        raise FileNotFoundError(f"Validation file not found: {validation_path}")
    with open(validation_path, 'r') as f:
        return json.load(f)

def load_and_filter_data(data_path, validation):
    """Load cleaned data and filter to valid grouping levels."""
    df = pd.read_csv(data_path)
    
    # Filter by field if valid
    if validation.get("field", {}).get("status") == "valid":
        valid_fields = validation["field"]["valid_levels"]
        df = df[df['field'].isin(valid_fields)]
    
    # Filter by original_study_id if valid
    if validation.get("original_study_id", {}).get("status") == "valid":
        valid_studies = validation["original_study_id"]["valid_levels"]
        df = df[df['original_study_id'].isin(valid_studies)]
    
    if len(df) == 0:
        raise ValueError("No data remaining after filtering invalid grouping levels.")
    
    return df

def build_exog_re(df, group_col):
    """
    Build the random effects design matrix (exog_re) for a specific grouping factor.
    Returns a numpy array where each column corresponds to a unique level of group_col.
    """
    unique_levels = df[group_col].unique()
    level_to_idx = {level: i for i, level in enumerate(unique_levels)}
    n_rows = len(df)
    n_cols = len(unique_levels)
    
    exog_re = np.zeros((n_rows, n_cols))
    for i, level in enumerate(df[group_col]):
        exog_re[i, level_to_idx[level]] = 1
    
    return exog_re

def fit_full_lmm(df):
    """
    Fit the Full Model: power_estimate ~ year + effect_size + sample_size
    with crossed random intercepts for 'field' and 'original_study_id'.
    
    Implementation Note:
    statsmodels MixedLM supports crossed random effects by specifying:
    - groups: The primary grouping factor (random intercepts per level).
    - exog_re: The design matrix for the second random effect.
    
    Here, we use 'field' as groups and 'original_study_id' as exog_re.
    """
    # Fixed effects
    fixed_cols = ['year', 'effect_size', 'sample_size']
    # Ensure columns exist
    for col in fixed_cols:
        if col not in df.columns:
            raise ValueError(f"Missing fixed effect column: {col}")
    
    exog = sm.add_constant(df[fixed_cols])
    
    # Random effects for 'original_study_id' (crossed)
    exog_re = build_exog_re(df, 'original_study_id')
    
    # Fit Model
    model = MixedLM(endog=df['power_estimate'], exog=exog, groups=df['field'], exog_re=exog_re)
    
    try:
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Full model fitting failed: {e}")
        raise

def fit_reduced_lmm(df):
    """
    Fit the Reduced Model: power_estimate ~ effect_size + sample_size
    (Same random effects as Full Model, but without 'year').
    """
    fixed_cols = ['effect_size', 'sample_size']
    exog = sm.add_constant(df[fixed_cols])
    
    exog_re = build_exog_re(df, 'original_study_id')
    
    model = MixedLM(endog=df['power_estimate'], exog=exog, groups=df['field'], exog_re=exog_re)
    
    try:
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Reduced model fitting failed: {e}")
        raise

def perform_lrt(full_result, reduced_result):
    """
    Perform Likelihood Ratio Test comparing Full vs Reduced model.
    """
    llf_full = full_result.llf
    llf_reduced = reduced_result.llf
    
    # LRT Statistic: 2 * (LL_full - LL_reduced)
    lrt_stat = 2 * (llf_full - llf_reduced)
    
    # Degrees of freedom difference (1 parameter: 'year')
    df_diff = 1
    
    # P-value
    p_value = 1 - stats.chi2.cdf(lrt_stat, df_diff)
    
    return {
        "chi2_statistic": float(lrt_stat),
        "df_diff": int(df_diff),
        "p_value_lrt": float(p_value)
    }

def extract_year_metrics(full_result):
    """Extract year slope, SE, and CI from full model."""
    params = full_result.params
    bse = full_result.bse
    
    slope = params['year']
    se = bse['year']
    ci_lower = slope - 1.96 * se
    ci_upper = slope + 1.96 * se
    
    return {
        "slope_year": float(slope),
        "se_year": float(se),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def calculate_residuals(df, full_result):
    """Calculate residuals: observed - predicted."""
    fitted = full_result.fittedvalues
    residuals = df['power_estimate'] - fitted
    return residuals

def save_results(metrics, lrt_results, output_path):
    """Save final model summary to JSON."""
    output = {
        **metrics,
        **lrt_results,
        "methodology_note": "MixedLM with crossed random effects (groups=field, exog_re=original_study_id)."
    }
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Saved results to {output_path}")

def save_residuals(df, residuals, output_path):
    """Save residuals to CSV."""
    df_res = df.copy()
    df_res['model_residual'] = residuals
    
    # Select required columns for downstream tasks (T013, T020, T020b)
    output_df = df_res[['study_id', 'year', 'field', 'original_study_id', 'model_residual']]
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved residuals to {output_path}")

# --- Main Pipeline ---

def main():
    # Paths
    data_path = Path("data/derived/cleaned_data.csv")
    validation_path = Path("data/derived/grouping_validation.json")
    summary_output_path = Path("results/lmm_final_summary.json")
    residuals_output_path = Path("data/derived/residuals.csv")
    
    # Ensure output directory exists
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    residuals_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data & Validation
    logger.info("Loading data and validation...")
    validation = load_grouping_validation(validation_path)
    df = load_and_filter_data(data_path, validation)
    
    logger.info(f"Data loaded: {len(df)} rows after filtering.")
    
    # 2. Fit Full Model
    logger.info("Fitting Full Model (with year)...")
    full_result = fit_full_lmm(df)
    
    # 3. Fit Reduced Model
    logger.info("Fitting Reduced Model (without year)...")
    reduced_result = fit_reduced_lmm(df)
    
    # 4. Perform LRT
    logger.info("Performing Likelihood Ratio Test...")
    lrt_results = perform_lrt(full_result, reduced_result)
    
    # 5. Extract Metrics
    logger.info("Extracting year metrics...")
    metrics = extract_year_metrics(full_result)
    
    # 6. Calculate Residuals
    logger.info("Calculating residuals...")
    residuals = calculate_residuals(df, full_result)
    
    # 7. Save Outputs
    logger.info("Saving outputs...")
    save_results(metrics, lrt_results, summary_output_path)
    save_residuals(df, residuals, residuals_output_path)
    
    logger.info("Pipeline completed successfully.")
    return metrics, lrt_results

if __name__ == "__main__":
    main()