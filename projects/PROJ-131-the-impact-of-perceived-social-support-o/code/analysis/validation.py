import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_analysis_cohort(cohort_path: str) -> pd.DataFrame:
    """
    Load the analysis cohort from the CSV file.
    """
    if not os.path.exists(cohort_path):
        raise FileNotFoundError(f"Analysis cohort not found at {cohort_path}. "
                                "Ensure T014 has been executed successfully.")
    logger.info(f"Loading analysis cohort from {cohort_path}")
    df = pd.read_csv(cohort_path)
    logger.info(f"Loaded cohort with {len(df)} rows and {len(df.columns)} columns")
    return df

def check_harassment_variance(df: pd.DataFrame, threshold_sd: float = 0.5, min_n: int = 30) -> Dict[str, Any]:
    """
    Check the variance of Harassment Exposure (binary).
    Requirement: SD > threshold_sd and N > min_n.
    """
    col_name = 'harassment_exposure'
    if col_name not in df.columns:
        raise ValueError(f"Column '{col_name}' not found in cohort. "
                         "Cannot perform variance check.")

    n = df[col_name].count()
    sd = df[col_name].std()

    logger.info(f"Harassment Exposure: N={n}, SD={sd:.4f}")

    passed = (n > min_n) and (sd > threshold_sd)
    status = "PASS" if passed else "FAIL"

    return {
        "check": "harassment_exposure_variance",
        "column": col_name,
        "n": int(n),
        "sd": float(sd),
        "threshold_sd": threshold_sd,
        "min_n": min_n,
        "passed": passed,
        "status": status
    }

def check_vif(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute VIF for the model matrix including interaction term.
    Model: Outcome ~ SocialSupport + HarassmentExposure + Interaction + Covariates
    Covariates: age, gender, education, income (if present)

    Steps:
    1. Select relevant columns.
    2. Create interaction term.
    3. Center variables using StandardScaler (with_mean=True, with_std=False).
    4. Fit OLS to get design matrix.
    5. Compute VIF for each predictor.
    """
    required_cols = ['social_support', 'harassment_exposure']
    covariates = ['age', 'gender', 'education', 'income']
    available_covariates = [c for c in covariates if c in df.columns]

    # Ensure required columns exist
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing for VIF calculation.")

    # Create a working copy
    model_df = df[required_cols + available_covariates].copy()

    # Drop rows with any NaN in these columns for VIF calculation
    model_df = model_df.dropna()
    if len(model_df) < 10:
        logger.warning("Insufficient rows for VIF calculation after dropping NaNs.")
        return {
            "check": "vif",
            "status": "FAIL",
            "error": "Insufficient data",
            "max_vif": None
        }

    # Create interaction term
    model_df['interaction'] = model_df['social_support'] * model_df['harassment_exposure']

    # Center variables (StandardScaler with_std=False to only center)
    scaler = StandardScaler(with_mean=True, with_std=False)
    # We need to scale all numeric columns including the interaction
    numeric_cols = model_df.columns.tolist()
    scaled_values = scaler.fit_transform(model_df[numeric_cols])
    scaled_df = pd.DataFrame(scaled_values, columns=numeric_cols, index=model_df.index)

    # Add constant for OLS (required by statsmodels)
    X = sm.add_constant(scaled_df)

    # Compute VIF for each column (excluding constant)
    vif_data = []
    max_vif = 0.0
    vif_failed = False

    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({"variable": col, "vif": float(vif)})
            if vif > max_vif:
                max_vif = vif
            if vif >= 5.0:
                vif_failed = True
        except Exception as e:
            logger.error(f"Error computing VIF for {col}: {e}")
            vif_failed = True

    logger.info(f"VIF Check - Max VIF: {max_vif:.4f}")
    for v in vif_data:
        logger.info(f"  {v['variable']}: {v['vif']:.4f}")

    passed = not vif_failed and (max_vif < 5.0)
    status = "PASS" if passed else "FAIL"

    return {
        "check": "vif",
        "max_vif": float(max_vif),
        "threshold_vif": 5.0,
        "passed": passed,
        "status": status,
        "details": vif_data
    }

def validate_analysis_cohort(cohort_path: str) -> Dict[str, Any]:
    """
    Main validation function for the analysis cohort (Task T015).
    Performs:
    1. Harassment Exposure Variance Check
    2. VIF Check (Collinearity)

    Returns a report dictionary. Raises RuntimeError if validation fails.
    """
    logger.info("Starting analysis cohort validation (T015)...")

    # Load data
    df = load_analysis_cohort(cohort_path)

    # 1. Variance Check
    variance_report = check_harassment_variance(df)

    # 2. VIF Check
    vif_report = check_vif(df)

    # Compile final report
    report = {
        "validation_status": "PASSED",
        "checks": [variance_report, vif_report],
        "details": {
            "variance_check": variance_report,
            "vif_check": vif_report
        }
    }

    # Determine overall status
    if not variance_report["passed"] or not vif_report["passed"]:
        report["validation_status"] = "FAILED"
        error_msg = "Cohort validity check failed. Aborting."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Cohort validation PASSED.")
    return report

def main():
    """
    Entry point for T015.
    Loads config, runs validation, and writes report to data/results/validation_report.json.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    report_path = project_root / "data" / "results" / "validation_report.json"

    # Ensure output directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        report = validate_analysis_cohort(str(cohort_path))

        # Write report to JSON
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Validation report saved to {report_path}")
        print(f"Validation successful. Report saved to {report_path}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    main()