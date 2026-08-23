"""
Linear Mixed-Effects Model Fitting for Attentional Bias Analysis.

This module implements Model A (random intercepts) and Model B (random intercepts + slopes)
using statsmodels to analyze the relationship between visual salience and attentional metrics.

Dependencies:
- T029c: Checks the power gate flag before execution.
- T026: Requires aligned_metrics.csv from US2.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Project imports
from config import get_paths, load_config
from utils.logging import get_logger, log_error_context

# Setup logger
logger = get_logger(__name__)

# Constants
POWER_GATE_FLAG_PATH = "data/interim/invalid_for_inference_flag.json"
ALIGNED_DATA_PATH = "data/processed/aligned_metrics.csv"
RESULTS_OUTPUT_PATH = "data/processed/results.json"
MODEL_A_SUMMARY_PATH = "data/interim/model_a_summary.txt"
MODEL_B_SUMMARY_PATH = "data/interim/model_b_summary.txt"

def check_power_gate() -> Tuple[bool, Optional[str]]:
    """
    Checks if the power gate flag exists (indicating the study is invalid).
    
    Returns:
        Tuple[bool, str or None]: (is_valid, reason). 
        If is_valid is False, reason contains the explanation.
    """
    paths = get_paths()
    flag_path = paths.data_interim / POWER_GATE_FLAG_PATH
    
    if flag_path.exists():
        try:
            with open(flag_path, 'r', encoding='utf-8') as f:
                flag_data = json.load(f)
            reason = flag_data.get("reason", "Power gate failed: Power < 0.8")
            logger.error(f"Power gate check failed. Study halted. Reason: {reason}")
            return False, reason
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse power gate flag file: {e}. Proceeding with caution.")
            # If we can't read the flag, we might proceed, but log heavily.
            # However, per spec, if T029c wrote it, it's a hard block.
            return False, "Corrupted power gate flag file"
    
    logger.info("Power gate check passed. Proceeding with model fitting.")
    return True, None

def load_aligned_data() -> pd.DataFrame:
    """
    Loads the aligned metrics dataset generated in T026.
    """
    paths = get_paths()
    data_path = paths.data_processed / ALIGNED_DATA_PATH
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Aligned data not found at {data_path}. "
            "Ensure T026 (Alignment) has completed successfully."
        )
    
    df = pd.read_csv(data_path)
    
    required_cols = ['TrialID', 'SubjectID', 'SalienceScore', 'DwellTime', 'FirstFixationProb']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(
            f"Aligned data missing required columns: {missing_cols}. "
            "Expected columns: {required_cols}"
        )
    
    # Basic validation
    if df.empty:
        raise ValueError("Aligned data is empty. Cannot fit models.")
        
    logger.info(f"Loaded {len(df)} trials from {data_path}")
    return df

def fit_model_a(df: pd.DataFrame) -> Tuple[Any, str]:
    """
    Fits Model A: Random Intercepts only.
    Formula: DwellTime ~ SalienceScore + (1 | SubjectID)
    """
    logger.info("Fitting Model A (Random Intercepts)...")
    formula_a = "DwellTime ~ SalienceScore + (1 | SubjectID)"
    
    try:
        model = smf.mixedlm(formula_a, df, groups=df["SubjectID"])
        result = model.fit(reml=False) # Use ML for model comparison if needed later
        summary = result.summary().as_text()
        
        with open(MODEL_A_SUMMARY_PATH, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Model A fitted successfully.")
        return result, summary
    except Exception as e:
        log_error_context(logger, "Failed to fit Model A", e)
        raise

def fit_model_b(df: pd.DataFrame) -> Tuple[Any, str]:
    """
    Fits Model B: Random Intercepts + Random Slopes for Salience.
    Formula: DwellTime ~ SalienceScore + (SalienceScore | SubjectID)
    """
    logger.info("Fitting Model B (Random Intercepts + Slopes)...")
    formula_b = "DwellTime ~ SalienceScore + (SalienceScore | SubjectID)"
    
    try:
        # Note: Random slopes can sometimes fail to converge if data is sparse.
        # We catch convergence warnings/errors here.
        model = smf.mixedlm(formula_b, df, groups=df["SubjectID"])
        result = model.fit(reml=False)
        summary = result.summary().as_text()
        
        with open(MODEL_B_SUMMARY_PATH, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Model B fitted successfully.")
        return result, summary
    except Exception as e:
        log_error_context(logger, "Failed to fit Model B (likely convergence issues).", e)
        # If Model B fails, we still return Model A results but flag Model B as failed
        return None, f"Model B fitting failed: {str(e)}"

def extract_results(result: Any) -> Dict[str, Any]:
    """
    Extracts key statistical metrics from a fitted model result.
    """
    if result is None:
        return {"status": "failed", "message": "Model result is None"}
    
    try:
        # Get fixed effects
        fixed_effects = result.params
        p_values = result.pvalues
        std_err = result.bse
        
        # Focus on the SalienceScore coefficient
        salience_idx = 'SalienceScore'
        if salience_idx in fixed_effects:
            coef = float(fixed_effects[salience_idx])
            p_val = float(p_values[salience_idx])
            std_err_val = float(std_err[salience_idx])
            t_val = float(result.tvalues[salience_idx])
            ci_low, ci_high = result.conf_int().loc[salience_idx]
            
            return {
                "status": "success",
                "coefficient": coef,
                "std_error": std_err_val,
                "t_value": t_val,
                "p_value": p_val,
                "confidence_interval": [float(ci_low), float(ci_high)],
                "log_likelihood": float(result.llf),
                "aic": float(result.aic),
                "bic": float(result.bic)
            }
        else:
            return {"status": "error", "message": "SalienceScore not found in fixed effects"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def write_final_results(
    model_a_result: Optional[Any], 
    model_b_result: Optional[Any], 
    model_b_error: Optional[str]
) -> None:
    """
    Aggregates results into a final JSON report.
    """
    report = {
        "task_id": "T032",
        "description": "Linear Mixed-Effects Model Fitting",
        "model_a": extract_results(model_a_result),
        "model_b": extract_results(model_b_result) if model_b_result else {"status": "failed", "message": model_b_error},
        "disclaimer": "Correlational only - see FR-007 and SCR-002 regarding low-level covariates."
    }
    
    paths = get_paths()
    output_path = paths.data_processed / RESULTS_OUTPUT_PATH
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final results written to {output_path}")

def main():
    """
    Main entry point for T032.
    1. Check Power Gate (T029c).
    2. Load Aligned Data (T026).
    3. Fit Model A and Model B.
    4. Write results.
    """
    logger.info("Starting Task T032: LMM Fit")
    
    # 1. Check Power Gate
    is_valid, reason = check_power_gate()
    if not is_valid:
        logger.error(f"Task T032 aborted due to power gate failure: {reason}")
        # Write a failure report so downstream tasks know why
        paths = get_paths()
        error_report = {
            "task_id": "T032",
            "status": "aborted",
            "reason": reason,
            "disclaimer": "Correlational only - see FR-007"
        }
        with open(paths.data_processed / RESULTS_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2)
        return 1
    
    # 2. Load Data
    try:
        df = load_aligned_data()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Failed to load data: {e}")
        return 1
    
    # 3. Fit Models
    model_a_res = None
    model_b_res = None
    model_b_err = None
    
    try:
        model_a_res, _ = fit_model_a(df)
    except Exception:
        logger.error("Model A fitting failed completely. Cannot proceed.")
        return 1
    
    try:
        model_b_res, model_b_err = fit_model_b(df)
    except Exception as e:
        logger.warning(f"Model B fitting failed unexpectedly: {e}")
        model_b_err = str(e)
    
    # 4. Write Results
    write_final_results(model_a_res, model_b_res, model_b_err)
    
    logger.info("Task T032 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
