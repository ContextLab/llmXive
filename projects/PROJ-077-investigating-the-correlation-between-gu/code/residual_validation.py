"""
Residual Normality Validation Module (Task T025b)

Implements Shapiro-Wilk test and other diagnostics for regression residuals
to validate the normality assumption of the Secondary Path regression model.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

# Import project config and logging
from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger(__name__)

# Constants
OUTPUT_PATH = Path("data/processed/regression_diagnostics.json")
REGRESSION_RESULTS_PATH = Path("data/processed/regression_results.csv")
CLEANED_DATA_PATH = Path("data/processed/cleaned_data.csv")

def load_regression_data() -> pd.DataFrame:
    """
    Load the cleaned dataset required for regression residual validation.
    
    Returns:
        pd.DataFrame: The cleaned dataset with necessary columns.
        
    Raises:
        FileNotFoundError: If the cleaned data file does not exist.
        ValueError: If required columns are missing.
    """
    ensure_directories()
    
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Required cleaned data file not found at {CLEANED_DATA_PATH}. "
            "Please run data ingestion pipeline first."
        )
    
    df = pd.read_csv(CLEANED_DATA_PATH)
    
    required_cols = ['shannon_index', 'fluid_intelligence', 'Age', 'BMI', 'Sex', 'DQS']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(
            f"Missing required columns in cleaned data: {missing_cols}. "
            f"Available columns: {df.columns.tolist()}"
        )
    
    logger.info(f"Loaded {len(df)} rows from {CLEANED_DATA_PATH}")
    return df

def run_regression_model(df: pd.DataFrame) -> Tuple[sm.RegressionResults, pd.Series]:
    """
    Fit the multivariate linear regression model as defined in T023.
    
    Model: Fluid Intelligence ~ Shannon Index + Age + Sex + BMI + DQS
    
    Args:
        df: Cleaned dataset with required columns.
        
    Returns:
        Tuple[sm.RegressionResults, pd.Series]: The fitted model results and residuals.
    """
    # Prepare features
    predictors = ['shannon_index', 'Age', 'BMI', 'DQS']
    # Encode Sex as dummy variables (0 for M, 1 for F assuming binary)
    df['Sex_encoded'] = (df['Sex'] == 'F').astype(int)
    predictors.append('Sex_encoded')
    
    X = df[predictors]
    y = df['fluid_intelligence']
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit OLS model
    model = sm.OLS(y, X)
    results = model.fit()
    
    logger.info(f"Regression model fitted: R-squared = {results.rsquared:.4f}")
    
    return results, results.resid

def perform_shapiro_wilk_test(residuals: pd.Series) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality on residuals.
    
    Args:
        residuals: The residual series from the regression model.
        
    Returns:
        Dict[str, Any]: Dictionary containing statistic, p-value, and interpretation.
    """
    if len(residuals) < 3:
        raise ValueError("Shapiro-Wilk test requires at least 3 observations.")
    
    # Remove NaN residuals if any
    clean_residuals = residuals.dropna()
    
    if len(clean_residuals) < 3:
        raise ValueError("After removing NaNs, insufficient data for Shapiro-Wilk test.")
    
    statistic, p_value = stats.shapiro(clean_residuals)
    
    interpretation = "PASS" if p_value > 0.05 else "FAIL"
    logger.info(f"Shapiro-Wilk Test: W={statistic:.4f}, p-value={p_value:.4f} -> {interpretation}")
    
    return {
        "test": "Shapiro-Wilk",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "n_observations": int(len(clean_residuals)),
        "interpretation": interpretation,
        "alpha": 0.05
    }

def check_normality_assumption(residuals: pd.Series) -> Dict[str, Any]:
    """
    Perform additional normality checks: Kolmogorov-Smirnov and visual inspection stats.
    
    Args:
        residuals: The residual series from the regression model.
        
    Returns:
        Dict[str, Any]: Dictionary with KS test results and skewness/kurtosis.
    """
    clean_residuals = residuals.dropna()
    
    # Kolmogorov-Smirnov test against normal distribution
    # Note: KS test is less powerful for normality than Shapiro-Wilk but useful as secondary check
    ks_stat, ks_p = stats.kstest(clean_residuals, 'norm', 
                                 args=(clean_residuals.mean(), clean_residuals.std()))
    
    # Calculate skewness and kurtosis
    skewness = float(stats.skew(clean_residuals))
    kurtosis = float(stats.kurtosis(clean_residuals))  # Excess kurtosis
    
    # Interpretation
    ks_interpretation = "PASS" if ks_p > 0.05 else "FAIL"
    
    logger.info(f"KS Test: D={ks_stat:.4f}, p={ks_p:.4f} -> {ks_interpretation}")
    logger.info(f"Skewness: {skewness:.4f}, Excess Kurtosis: {kurtosis:.4f}")
    
    return {
        "test": "Kolmogorov-Smirnov",
        "statistic": float(ks_stat),
        "p_value": float(ks_p),
        "interpretation": ks_interpretation,
        "skewness": skewness,
        "excess_kurtosis": kurtosis,
        "n_observations": int(len(clean_residuals))
    }

def generate_diagnostics_report(
    shapiro_result: Dict[str, Any], 
    ks_result: Dict[str, Any],
    model_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compile all diagnostics into a single report structure.
    
    Args:
        shapiro_result: Results from Shapiro-Wilk test.
        ks_result: Results from KS test and descriptive stats.
        model_summary: Optional string summary of the regression model.
        
    Returns:
        Dict[str, Any]: Complete diagnostics report.
    """
    overall_status = "PASS" if shapiro_result["interpretation"] == "PASS" else "FAIL"
    
    report = {
        "task_id": "T025b",
        "description": "Residual Normality Validation for Secondary Path Regression",
        "status": overall_status,
        "shapiro_wilk": shapiro_result,
        "kolmogorov_smirnov": ks_result,
        "model_info": {
            "response_variable": "fluid_intelligence",
            "predictors": ["shannon_index", "Age", "BMI", "Sex", "DQS"],
            "n_observations": ks_result["n_observations"]
        },
        "conclusion": (
            "The normality assumption for regression residuals is MET." if overall_status == "PASS" 
            else "The normality assumption for regression residuals is VIOLATED. "
                  "Consider robust regression or transformation of variables."
        )
    }
    
    if model_summary:
        report["model_summary_text"] = model_summary
        
    return report

def save_report(report: Dict[str, Any]) -> None:
    """
    Save the diagnostics report to the specified JSON file.
    
    Args:
        report: The diagnostics report dictionary.
    """
    ensure_directories()
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved diagnostics report to {OUTPUT_PATH}")

def run_validation_pipeline() -> Dict[str, Any]:
    """
    Execute the full residual validation pipeline.
    
    Returns:
        Dict[str, Any]: The generated diagnostics report.
    """
    log_pipeline_start("T025b", "Residual Normality Validation")
    
    try:
        # 1. Load data
        df = load_regression_data()
        
        # 2. Run regression model
        model_results, residuals = run_regression_model(df)
        
        # 3. Perform Shapiro-Wilk test
        shapiro_result = perform_shapiro_wilk_test(residuals)
        
        # 4. Perform additional normality checks
        ks_result = check_normality_assumption(residuals)
        
        # 5. Generate report
        report = generate_diagnostics_report(shapiro_result, ks_result)
        
        # 6. Save report
        save_report(report)
        
        log_pipeline_end("T025b", "Success")
        return report
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        log_pipeline_end("T025b", f"Failed: {str(e)}")
        raise

def main():
    """Entry point for the residual validation script."""
    print("Starting Residual Normality Validation (T025b)...")
    try:
        report = run_validation_pipeline()
        print(f"Validation complete. Status: {report['status']}")
        print(f"Shapiro-Wilk p-value: {report['shapiro_wilk']['p_value']:.4f}")
        print(f"Conclusion: {report['conclusion']}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
