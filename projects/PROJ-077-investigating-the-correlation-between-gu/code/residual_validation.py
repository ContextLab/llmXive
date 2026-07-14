"""
Residual Normality Validation Module (Task T025b)

Implements Shapiro-Wilk test for regression residuals to validate the 
normality assumption required for OLS inference (Secondary Path).

Saves validation report to data/processed/regression_diagnostics.json
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

# Add project root to path for imports if running as script
if __package__ is None:
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import ensure_directories, INPUT_PATHS, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

# Initialize logger
logger = get_logger(__name__)

def load_regression_data() -> pd.DataFrame:
    """
    Load the processed dataset required for regression analysis.
    This assumes T015 (save_cleaned_data) and T020-T023 have run.
    """
    input_path = INPUT_PATHS.get('processed_data', 'data/processed/cleaned_data.csv')
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                f"Ensure T015 (save_cleaned_data) has been executed.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def run_regression_model(df: pd.DataFrame) -> sm.regression.linear_model.OLSResults:
    """
    Fit the multivariate linear regression model as defined in T023.
    Predictors: shannon_index, Age, Sex, BMI, DQS
    Target: fluid_intelligence
    """
    required_cols = ['fluid_intelligence', 'shannon_index', 'Age', 'Sex', 'BMI', 'DQS']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for regression: {missing_cols}")

    # Prepare data
    X = df[required_cols[1:]] # Predictors
    y = df[required_cols[0]]  # Target

    # Handle categorical 'Sex' if necessary (assuming it's already encoded or string)
    if X['Sex'].dtype == object:
        X = pd.get_dummies(X, columns=['Sex'], drop_first=True)
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit OLS
    model = sm.OLS(y, X, missing='drop')
    results = model.fit()
    
    logger.info("Regression model fitted successfully.")
    return results

def perform_shapiro_wilk_test(residuals: np.ndarray) -> Dict[str, float]:
    """
    Perform Shapiro-Wilk test for normality on residuals.
    Returns dictionary with statistic and p-value.
    """
    if len(residuals) < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 samples.")
    
    stat, p_value = stats.shapiro(residuals)
    return {
        "statistic": float(stat),
        "p_value": float(p_value)
    }

def check_normality_assumption(p_value: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Evaluate the result of the normality test.
    Null Hypothesis (H0): Residuals are normally distributed.
    """
    is_normal = p_value > alpha
    status = "PASS" if is_normal else "FAIL"
    
    return {
        "assumption_met": is_normal,
        "status": status,
        "alpha": alpha,
        "interpretation": (
            "Residuals appear normally distributed (p > 0.05). "
            "OLS inference assumptions are valid." if is_normal
            else "Residuals do NOT appear normally distributed (p <= 0.05). "
                 "OLS inference assumptions may be violated."
        )
    }

def generate_diagnostics_report(results: sm.regression.linear_model.OLSResults) -> Dict[str, Any]:
    """
    Compile all diagnostic information into a report dictionary.
    """
    residuals = results.resid
    
    shapiro_result = perform_shapiro_wilk_test(residuals)
    normality_check = check_normality_assumption(shapiro_result['p_value'])
    
    report = {
        "test_name": "Shapiro-Wilk Normality Test",
        "test_description": "Validates the normality assumption of regression residuals for OLS inference.",
        "sample_size": int(len(residuals)),
        "shapiro_wilk": shapiro_result,
        "normality_assessment": normality_check,
        "model_summary": {
            "r_squared": float(results.rsquared),
            "adj_r_squared": float(results.rsquared_adj),
            "f_statistic": float(results.fvalue),
            "f_pvalue": float(results.f_pvalue)
        }
    }
    
    return report

def save_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the diagnostics report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved regression diagnostics report to {output_path}")

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Main pipeline function for Task T025b.
    1. Load cleaned data.
    2. Fit regression model.
    3. Perform Shapiro-Wilk test.
    4. Generate and save report.
    """
    log_pipeline_start("Residual Normality Validation (T025b)")
    
    try:
        # 1. Load Data
        df = load_regression_data()
        
        # 2. Fit Model
        results = run_regression_model(df)
        
        # 3. Generate Report
        report = generate_diagnostics_report(results)
        
        # 4. Save Output
        output_path = "data/processed/regression_diagnostics.json"
        save_report(report, output_path)
        
        # Log result status
        status = report['normality_assessment']['status']
        if status == "FAIL":
            log_warning(f"Normality assumption failed (p={report['shapiro_wilk']['p_value']:.4f}). "
                        "Interpret regression coefficients with caution.")
        else:
            log_provenance("Normality assumption validated for OLS inference.")
        
        log_pipeline_end("Residual Normality Validation completed.")
        return report
        
    except Exception as e:
        log_warning(f"Validation pipeline failed: {str(e)}")
        raise

def main():
    """Entry point for script execution."""
    ensure_directories()
    run_validation_pipeline()

if __name__ == "__main__":
    main()
