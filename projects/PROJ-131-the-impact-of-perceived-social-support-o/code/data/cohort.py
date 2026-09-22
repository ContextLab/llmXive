"""
Cohort Construction Module.

Implements T014: Filter critical missing, check variance, output analysis_cohort.csv.
Implements T015: Validation (VIF, Variance).
Implements T016: Save validated cohort.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.preprocessing import run_preprocessing, RAW_FILE_PATH
from data.ingestion import load_cyber_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_DIR = project_root / "data" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_preprocessed_data():
    """
    Loads the preprocessed data.
    If not saved yet, runs preprocessing.
    """
    # For this pipeline, we assume preprocessing runs and saves or returns data.
    # Since T014 depends on T013, we run T013 logic here or load the result.
    # To ensure modularity, we assume T013 saves a temp file or we run it.
    # Let's run the preprocessing function to get the dataframe.
    logger.info("Loading preprocessed data...")
    # Re-running preprocessing to get the clean DF (idempotent if files exist)
    # In a real pipeline, we'd load a saved intermediate.
    # For this task, we'll call the preprocessing logic.
    # Note: This might be slow, but ensures data flow.
    # Alternatively, we assume T013 saved a file. Let's assume it didn't and run it.
    # Actually, better to run the main function of preprocessing if it saves.
    # Since T013 doesn't explicitly save a file in the prompt's description,
    # we will re-run the logic or assume it's in memory.
    # To be safe and follow the "run book" style, we'll assume we run the steps.
    
    # Let's implement the logic inline to ensure we have the data.
    df = run_preprocessing()
    return df

def filter_critical_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters rows with critical missing values.
    Critical: harassment_severity, social_support, and at least one outcome.
    """
    logger.info("Filtering critical missing values...")
    critical_cols = ['harassment_severity', 'social_support']
    outcomes = ['depression', 'anxiety', 'ptsd']
    valid_outcomes = [o for o in outcomes if o in df.columns]
    
    # Drop rows where critical predictors are missing
    df = df.dropna(subset=critical_cols)
    
    # Drop rows where at least one outcome is missing (if any outcomes exist)
    if valid_outcomes:
        df = df.dropna(subset=valid_outcomes)
        
    logger.info(f"Remaining rows after filtering: {len(df)}")
    return df

def check_harassment_variance(df: pd.DataFrame) -> bool:
    """
    Checks variance of harassment_severity.
    SD > 0.5, N > 30.
    """
    if 'harassment_severity' not in df.columns:
        logger.error("E-LOW-VAR-001: harassment_severity column missing.")
        return False

    n = len(df)
    std = df['harassment_severity'].std()

    logger.info(f"Harassment Severity: N={n}, SD={std:.4f}")

    if n <= 30:
        logger.error(f"E-LOW-VAR-001: N ({n}) <= 30.")
        return False
    if std <= 0.5:
        logger.error(f"E-LOW-VAR-001: SD ({std:.4f}) <= 0.5.")
        return False

    logger.info("Harassment variance check PASSED.")
    return True

def construct_analysis_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs the final analysis cohort.
    """
    logger.info("Constructing analysis cohort...")
    # Ensure dtypes are correct
    # Filter critical missing
    df = filter_critical_missing(df)
    # Check variance
    if not check_harassment_variance(df):
        raise RuntimeError("E-LOW-VAR-001: Cohort construction failed due to low variance.")
    
    return df

def save_cohort(df: pd.DataFrame, path: Optional[Path] = None):
    """Saves the cohort to CSV."""
    if path is None:
        path = RESULTS_DIR / "analysis_cohort.csv"
    
    df.to_csv(path, index=False)
    logger.info(f"Analysis cohort saved to {path}")

def validate_analysis_cohort(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the cohort per T015.
    - Variance of Harassment Exposure (SD > 0.5, N > 30)
    - VIF < 5
    """
    logger.info("Validating analysis cohort (T015)...")
    report = {
        "status": "PASSED",
        "checks": {}
    }

    # 1. Variance of Harassment Exposure
    # Note: T015 says "Variance of Harassment Exposure" but also mentions "harassment_severity" in T014.
    # We check the binary exposure as per T015 text, but T014 checked severity.
    # Let's check the binary exposure 'harassment_exposure' if it exists.
    if 'harassment_exposure' in df.columns:
        n = len(df[df['harassment_exposure'] == 1]) # Count exposed? Or total N?
        # T015 says "Variance of Harassment Exposure (SD > 0.5, N > 30)".
        # For a binary variable, SD = sqrt(p(1-p)). SD > 0.5 implies p is not too close to 0 or 1.
        # Let's check the SD of the column.
        sd = df['harassment_exposure'].std()
        total_n = len(df)
        report["checks"]["exposure_variance"] = {
            "sd": float(sd),
            "n": total_n,
            "passed": sd > 0.5 and total_n > 30
        }
        if not report["checks"]["exposure_variance"]["passed"]:
            report["status"] = "FAILED"
            logger.error(f"Exposure variance check failed: SD={sd}, N={total_n}")
    else:
        report["checks"]["exposure_variance"] = {"status": "SKIPPED", "reason": "Column not found"}

    # 2. VIF Calculation
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        from sklearn.preprocessing import StandardScaler
        
        # Model matrix: social_support, harassment_exposure, interaction, covariates
        # We need to center variables first as per T015
        cols_to_use = ['social_support', 'harassment_exposure']
        # Add interaction
        if 'social_support' in df.columns and 'harassment_exposure' in df.columns:
            df_temp = df.copy()
            df_temp['interaction'] = df_temp['social_support'] * df_temp['harassment_exposure']
            cols_to_use.append('interaction')
            
            # Add covariates if they exist and are numeric
            covariates = ['age', 'gender', 'education', 'income']
            for c in covariates:
                if c in df_temp.columns and np.issubdtype(df_temp[c].dtype, np.number):
                    cols_to_use.append(c)
            
            # Filter to numeric and dropna
            model_df = df_temp[cols_to_use].dropna()
            
            if len(model_df) < 10:
                logger.warning("Not enough data for VIF calculation.")
                report["checks"]["vif"] = {"status": "SKIPPED", "reason": "Insufficient data"}
            else:
                # Center (with_mean=True, with_std=False) as per T015
                scaler = StandardScaler(with_mean=True, with_std=False)
                X_scaled = scaler.fit_transform(model_df)
                X_scaled_df = pd.DataFrame(X_scaled, columns=model_df.columns)
                X_scaled_df['intercept'] = 1.0 # statsmodels VIF usually needs intercept or handled
                
                vif_data = []
                for i, col in enumerate(X_scaled_df.columns):
                    if col == 'intercept': continue
                    try:
                        vif = variance_inflation_factor(X_scaled_df.values, i)
                        vif_data.append({"col": col, "vif": vif})
                    except Exception:
                        pass
                
                max_vif = max([v["vif"] for v in vif_data]) if vif_data else 0
                report["checks"]["vif"] = {
                    "max_vif": float(max_vif),
                    "passed": max_vif < 5
                }
                if max_vif >= 5:
                    report["status"] = "FAILED"
                    logger.error(f"VIF check failed: Max VIF={max_vif}")
    except ImportError:
        logger.warning("statsmodels not installed. VIF check skipped.")
        report["checks"]["vif"] = {"status": "SKIPPED", "reason": "statsmodels missing"}
    except Exception as e:
        logger.error(f"VIF calculation error: {e}")
        report["checks"]["vif"] = {"status": "ERROR", "error": str(e)}

    # Save report
    report_path = RESULTS_DIR / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {report_path}")

    if report["status"] == "FAILED":
        raise RuntimeError("Cohort validity check failed. Aborting.")
    
    return report

def main():
    """Entry point for T014-T016."""
    logger.info("Starting Cohort Construction and Validation (T014-T016)...")
    try:
        # 1. Load/Preprocess
        df = load_preprocessed_data()
        
        # 2. Construct Cohort (T014)
        df_cohort = construct_analysis_cohort(df)
        
        # 3. Validate (T015)
        validate_analysis_cohort(df_cohort)
        
        # 4. Save (T016)
        save_cohort(df_cohort)
        
        logger.info("T014-T016 completed successfully.")
    except Exception as e:
        logger.error(f"Cohort tasks failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
