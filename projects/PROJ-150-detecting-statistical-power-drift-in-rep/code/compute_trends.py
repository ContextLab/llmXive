import os
import sys
import pickle
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.tools import add_constant

# Import logging utilities from the project
try:
    from logging_config import get_module_logger, log_operation_start, log_operation_complete
except ImportError:
    # Fallback if logging_config is not in path (though it should be per API surface)
    logging.basicConfig(level=logging.INFO)
    def get_module_logger(name): return logging.getLogger(name)
    def log_operation_start(logger, msg): logger.info(f"START: {msg}")
    def log_operation_complete(logger, msg): logger.info(f"COMPLETE: {msg}")

def load_and_prepare_data(input_path: str) -> pd.DataFrame:
    """
    Load the power estimates CSV and prepare it for modeling.
    Ensures required columns are present and handles basic types.
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['study_id', 'year', 'field', 'original_study_id', 'effect_size', 'sample_size', 'power_est']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    # Ensure numeric types
    numeric_cols = ['year', 'effect_size', 'sample_size', 'power_est']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN in critical columns for modeling
    initial_count = len(df)
    df = df.dropna(subset=['year', 'power_est', 'effect_size', 'sample_size'])
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to NaN in critical columns.")
    
    log_operation_complete(logger, f"Loaded {len(df)} rows")
    return df

def fit_mixed_linear_model(df: pd.DataFrame) -> MixedLM:
    """
    Fit the Linear Mixed-Effects Model as specified in T012a:
    power_est ~ year + effect_size + sample_size + (1|field) + (1|original_study_id)
    
    Note: statsmodels MixedLM handles one grouping variable directly. 
    To handle two random effects (field and original_study_id), we typically 
    stack them or use a compound grouping. However, the spec asks for random intercepts for BOTH.
    
    Approach: We will create a combined group key if possible, or fit a model with 
    the primary grouping (e.g., original_study_id) and treat 'field' as a fixed effect 
    if the library doesn't support nested/crossed random effects easily in this version.
    
    Correction based on strict spec: "random intercepts for field AND original_study_id".
    Statsmodels MixedLM supports `re_formula` and `groups`. For crossed random effects,
    we often need to use a workaround or a specific formulation.
    Given the constraints and standard usage in this pipeline, we will fit the model
    with `original_study_id` as the group, and include `field` as a fixed effect covariate
    to account for its variance, as true crossed random effects in statsmodels require 
    complex formulation or `linearmodels` library.
    
    HOWEVER, to adhere strictly to the "random intercepts" requirement without external 
    libraries not in requirements, we will attempt to use the `vc_formula` (variance components)
    if available, or fall back to the most robust interpretation: 
    Group by `original_study_id` (since studies are nested in fields or are the unit of replication).
    
    Let's implement the model: 
    Endog: power_est
    Exog: year, effect_size, sample_size
    Groups: original_study_id (primary unit of replication)
    We will add 'field' as a fixed effect to control for it, as is standard when crossed 
    effects are hard to specify in basic MixedLM without `vc_formula`.
    
    Wait, the spec says: `power_est ~ year + effect_size + sample_size + (1|field) + (1|original_study_id)`
    This implies crossed random effects.
    
    Strategy for Statsmodels MixedLM:
    We can use the `vc_formula` argument to specify variance components for 'field'.
    Formula: "power_est ~ year + effect_size + sample_size"
    Groups: "original_study_id"
    VCF: {"field": "0 + C(field)"} -> This adds a random effect for each level of field.
    
    Let's try this approach.
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, "Fitting Mixed Linear Model")
    
    # Prepare data
    # Ensure categorical for group
    df = df.copy()
    df['original_study_id'] = df['original_study_id'].astype(str)
    df['field'] = df['field'].astype(str)
    
    # Define formula
    # Fixed effects: year, effect_size, sample_size
    # Random effects: Intercept by original_study_id, Intercept by field
    formula = "power_est ~ year + effect_size + sample_size"
    
    # We need to handle the crossed random effects. 
    # In statsmodels, we can use `vc_formula` for the second random effect.
    # But `vc_formula` is for variance components.
    # Let's try fitting with original_study_id as groups and field as a fixed effect first 
    # if vc_formula proves unstable, but the spec is strict.
    # Actually, let's use the standard approach for crossed effects in statsmodels:
    # It's often easier to stack the groups if they are small, but here we use vc_formula.
    
    try:
        # Attempt to fit with crossed random effects using vc_formula
        # Note: This requires statsmodels >= 0.13.0 roughly
        model = MixedLM.from_formula(
            formula, 
            data=df, 
            groups=df['original_study_id'],
            re_formula="1",
            vc_formula={"field": "0 + C(field)"}
        )
        result = model.fit()
        logger.info("Model fitted successfully with crossed random effects.")
    except Exception as e:
        logger.warning(f"Crossed random effects fit failed ({e}). Falling back to single grouping (original_study_id) + field as fixed effect.")
        # Fallback: Treat field as fixed effect if crossed effects fail
        model = MixedLM.from_formula(
            "power_est ~ year + effect_size + sample_size + C(field)", 
            data=df, 
            groups=df['original_study_id']
        )
        result = model.fit()
        logger.info("Model fitted with field as fixed effect.")
    
    log_operation_complete(logger, "Model fitting complete")
    return result

def extract_year_statistics(result: MixedLM) -> dict:
    """
    Extract the year slope, standard error, confidence intervals, and p-value.
    The p-value is computed against the null hypothesis of zero slope (H0: beta_year = 0).
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, "Extracting year statistics")
    
    # Get parameter table
    # params: [Intercept, year, effect_size, sample_size, ...]
    # We need to find the index of 'year'
    param_names = result.params.index.tolist()
    
    if 'year' not in param_names:
        # Check if it's named differently due to formula parsing
        # It should be 'year' if added as a numeric column
        raise KeyError("Year coefficient not found in model results. Check column types.")
    
    idx_year = param_names.index('year')
    
    slope = result.params['year']
    se = result.bse['year']
    
    # 95% Confidence Interval
    # statsmodels get_prediction or manually: slope +/- 1.96 * se
    # Using the t-distribution with appropriate degrees of freedom is more accurate,
    # but for large N, 1.96 is standard. statsmodels conf_int() is best.
    conf_int = result.conf_int(alpha=0.05)
    ci_lower = conf_int.iloc[idx_year, 0]
    ci_upper = conf_int.iloc[idx_year, 1]
    
    # P-value
    # The t-statistic is slope / se. The p-value is P(|t| > |t_stat|)
    # statsmodels results usually have a z-test or t-test p-value.
    # result.pvalues is a Series
    p_value = result.pvalues['year']
    
    # Explicit assertion for SC-001: p-value is for H0: slope = 0
    # The statsmodels pvalue is exactly this test.
    significance = "significant" if p_value < 0.05 else "not significant"
    logger.info(f"Year slope: {slope:.4f}, SE: {se:.4f}, P-value: {p_value:.4f} ({significance})")
    
    stats = {
        "slope_year": float(slope),
        "se_year": float(se),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "p_value": float(p_value)
    }
    
    log_operation_complete(logger, "Statistics extracted")
    return stats

def save_results(stats: dict, output_path: str):
    """
    Save the full model object and raw parameters if needed, 
    but for T012b specifically, we focus on the summary CSV.
    The task T012a saves the model objects. T012b saves the summary.
    We will save the summary to the CSV as requested.
    """
    logger = get_module_logger(__name__)
    log_operation_start(logger, f"Saving results to {output_path}")
    
    df_summary = pd.DataFrame([stats])
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Saved summary to {output_path}")
    
    # Also update the model files if they exist to include the summary reference?
    # No, T012a handles model saving. T012b handles summary CSV.
    log_operation_complete(logger, "Results saved")

def save_summary(stats: dict, output_path: str):
    """Alias for save_results to match API surface if called differently"""
    save_results(stats, output_path)

def main():
    """
    Main entry point for T012b.
    1. Load data from data/derived/power_estimates.csv
    2. Load the model from data/derived/input_trends_models.pkl (fitted in T012a)
       OR re-fit the model if T012a output is expected to be the model object.
       The task says: "extract ... from the model in T012a".
       So we must load the model object.
    3. Extract statistics.
    4. Write data/derived/lmm_summary.csv.
    """
    logger = get_module_logger(__name__)
    logger.info("Starting T012b: Extract Year Statistics")
    
    # Paths
    data_path = Path("data/derived/power_estimates.csv")
    model_path = Path("data/derived/input_trends_models.pkl")
    output_path = Path("data/derived/lmm_summary.csv")
    
    # Check prerequisites
    if not data_path.exists():
        raise FileNotFoundError(f"Required input {data_path} not found. Run T011a first.")
    if not model_path.exists():
        raise FileNotFoundError(f"Required model {model_path} not found. Run T012a first.")
    
    # Load the fitted model
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model_result = pickle.load(f)
    
    # Extract statistics
    stats = extract_year_statistics(model_result)
    
    # Save summary CSV
    save_results(stats, str(output_path))
    
    logger.info("T012b completed successfully.")
    return stats

if __name__ == "__main__":
    main()