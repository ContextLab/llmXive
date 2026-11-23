"""
Pipeline runner that executes the full analysis flow:
1. Load data (real or synthetic)
2. Preprocess
3. Run Regression (T018, T019)
4. Run Bootstrap (T025)
5. Run Sensitivity (T027, T028)
6. Run Collinearity Check (T022)
7. Run Interpretation (T020)
8. Export Results (T021)
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end
from data.download import load_or_generate_data
from data.preprocess import preprocess_data
from analysis.regression import validate_model_assumptions
from analysis.collinearity_handler import run_collinearity_analysis
from analysis.bootstrap import run_bootstrap_analysis
from analysis.sensitivity import run_sensitivity_analysis
from analysis.interpretation import determine_interpretation_label
from analysis.export_results import run_export

logger = get_logger(__name__)

def run_full_pipeline():
    log_execution_start("full_pipeline")
    
    config = get_config()
    logger.info(f"Starting pipeline with seed: {config.seed}")
    
    # 1. Load Data
    logger.info("Loading data...")
    raw_df, data_source_info = load_or_generate_data()
    
    if raw_df is None or raw_df.empty:
        raise RuntimeError("Failed to load or generate data.")
    
    # 2. Preprocess
    logger.info("Preprocessing data...")
    processed_df = preprocess_data(raw_df)
    
    # 3. Run Regression & Assumptions
    logger.info("Running regression and checking assumptions...")
    # We need to fit the model first to get coefficients.
    # Since regression.py only has validation, we fit the model here manually 
    # using statsmodels to get the coefficients object for export.
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + C(comparison_tendency):C(avatar_condition)"
    # Note: The interaction term logic might need adjustment based on exact variable types.
    # Assuming numeric interaction for simplicity or using the specific column if pre-calculated.
    # If 'interaction' column exists in data:
    if 'interaction' in processed_df.columns:
        formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + interaction"
    
    model = smf.ols(formula, data=processed_df).fit()
    
    # Validate assumptions
    assumptions = validate_model_assumptions(model, processed_df)
    
    # 4. Collinearity
    logger.info("Checking collinearity...")
    collinearity_results = run_collinearity_analysis(processed_df, model)
    
    # 5. Bootstrap
    logger.info("Running bootstrap analysis...")
    bootstrap_results = run_bootstrap_analysis(processed_df, formula, n_iterations=1000)
    
    # 6. Sensitivity
    logger.info("Running sensitivity analysis...")
    # For sensitivity, we need ground truth if synthetic
    sensitivity_results = run_sensitivity_analysis(processed_df, model, data_source_info)
    
    # 7. Interpretation
    logger.info("Determining interpretation...")
    interp_label = determine_interpretation_label(data_source_info)
    
    # 8. Prepare Export Data
    # Coefficients DataFrame
    coeffs_df = model.summary2().tables[1] # This is a DataFrame in statsmodels
    # Convert to a clean DataFrame for export
    clean_coeffs = pd.DataFrame({
        "term": coeffs_df.index,
        "estimate": coeffs_df["Coef."],
        "std_err": coeffs_df["Std.Err."],
        "t_stat": coeffs_df["t"],
        "p_value": coeffs_df["P>|t|"],
        "ci_lower": coeffs_df["[0.025"],
        "ci_upper": coeffs_df["0.975]"]
    })
    
    # Diagnostics Dictionary
    diagnostics = {
        "model_summary": {
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "f_p_value": float(model.f_pvalue)
        },
        "assumptions": assumptions,
        "collinearity": collinearity_results,
        "bootstrap": {
            "ci_width_variance": float(bootstrap_results.get("ci_width_variance", 0)),
            "stability_flag": bootstrap_results.get("stability_flag", False)
        },
        "sensitivity": sensitivity_results,
        "interpretation_label": interp_label
    }
    
    # 9. Export
    logger.info("Exporting results...")
    csv_path, json_path = run_export(clean_coeffs, diagnostics)
    
    logger.info(f"Pipeline complete. Results saved to {csv_path} and {json_path}")
    log_execution_end("full_pipeline")
    return csv_path, json_path

if __name__ == "__main__":
    run_full_pipeline()
