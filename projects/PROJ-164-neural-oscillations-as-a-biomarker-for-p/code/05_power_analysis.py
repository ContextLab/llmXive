import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from scipy.stats import f

# Import local utilities
try:
    from utils.io_helpers import load_json, write_json
except ImportError:
    # Fallback for direct execution context
    from code.utils.io_helpers import load_json, write_json

def calculate_minimum_sample_size(r2_target: float = 0.1, power: float = 0.80, alpha: float = 0.05, k_predictors: int = 5) -> int:
    """
    Calculate minimum sample size (N) for multiple regression power analysis.
    
    Uses the non-central F-distribution approximation.
    We solve for N such that: P(F(df1, df2, lambda) > F_crit) >= power
    
    Parameters:
        r2_target: Expected R-squared value (effect size)
        power: Desired statistical power (1 - beta)
        alpha: Significance level
        k_predictors: Number of predictors in the model
    
    Returns:
        Minimum integer sample size N
    """
    df1 = k_predictors
    # We iterate to find N. Start with a reasonable guess
    # Approximation: N ~ (Z_alpha + Z_beta)^2 / (effect_size)^2 + k + 1
    # For R2=0.1, effect is moderate. Let's start around 100
    N_guess = 100 + k_predictors + 1
    
    while True:
        df2 = N_guess - k_predictors - 1
        if df2 <= 0:
            N_guess += 1
            continue
          
        # Critical F value
        # We need the inverse CDF of F distribution at 1-alpha
        # scipy.stats.f is not available in standard lib, but we assume scipy is installed per requirements.txt
        # However, to avoid heavy imports in this specific script if not strictly needed, 
        # we implement a simple search or use scipy if available.
        # Given requirements.txt includes scipy, we use it.
        from scipy import stats
        
        f_crit = stats.f.qf(1 - alpha, df1, df2)
        
        # Non-centrality parameter lambda
        # lambda = (R2 / (1 - R2)) * (N - k - 1)
        lambda_ncp = (r2_target / (1 - r2_target)) * df2
        
        # Calculate power: P(F > f_crit | df1, df2, lambda)
        # This is the survival function (1 - CDF) of the non-central F
        current_power = stats.f.sf(f_crit, df1, df2, lambda_ncp)
        
        if current_power >= power:
            return N_guess
        
        N_guess += 1

def generate_pre_registration(analysis_plan_hash: str, r2_target: float, power: float, alpha: float, k_predictors: int) -> Dict[str, Any]:
    """
    Generate the pre-registration JSON artifact.
    
    Updates the existing pre-registration.json if it exists, otherwise creates a new one.
    """
    pre_reg_path = Path("data/processed/pre-registration.json")
    
    # Load existing if present
    existing_data = {}
    if pre_reg_path.exists():
        existing_data = load_json(pre_reg_path)
    
    # Construct the new registration data
    registration_data = {
        "timestamp": datetime.now().isoformat(),
        "analysis_plan_hash": analysis_plan_hash,
        "parameters": {
            "r2_target": r2_target,
            "power": power,
            "alpha": alpha,
            "predictor_count": k_predictors
        },
        "status": "draft"
    }
    
    # Merge or create
    final_data = {**existing_data, **registration_data}
    
    # Ensure directory exists
    pre_reg_path.parent.mkdir(parents=True, exist_ok=True)
    
    write_json(final_data, pre_reg_path)
    return final_data

def main():
    logger = logging.getLogger("PowerAnalysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    logger.info("Starting Power Analysis Gate (T009)...")

    # 1. Read verified_source_manifest.json
    manifest_path = Path("data/processed/verified_source_manifest.json")
    if not manifest_path.exists():
        logger.error("CRITICAL: verified_source_manifest.json not found. T011 must run first.")
        sys.exit(1)

    manifest = load_json(manifest_path)
    status = manifest.get("status", "absent")
    
    if status != "found":
        logger.warning("Source status is 'absent' or unknown. Setting mode to Underpowered/Data Insufficient.")
        # Even if absent, we might need to generate a report indicating why
        n_actual = 0
    else:
        n_actual = manifest.get("N_actual", 0)
        if n_actual == 0:
            logger.warning("N_actual is 0 in manifest. Treating as insufficient.")
    
    logger.info(f"N_actual from manifest: {n_actual}")

    # 2. Define Analysis Parameters
    # These should ideally come from config, but we hardcode as per task spec for this gate
    r2_target = 0.1
    power_target = 0.80
    alpha = 0.05
    # Estimate predictors: typically ~5 bands + connectivity metrics
    k_predictors = 5 

    # 3. Calculate Minimum Sample Size
    logger.info(f"Calculating N_min for R2={r2_target}, Power={power_target}, Alpha={alpha}, k={k_predictors}")
    n_min = calculate_minimum_sample_size(r2_target, power_target, alpha, k_predictors)
    logger.info(f"Minimum required sample size (N_min): {n_min}")

    # 4. Compare and Determine Mode
    mode_flag = "Primary"
    if n_actual < n_min:
        mode_flag = "Underpowered"
        logger.warning(f"UNDERPOWERED: N_actual ({n_actual}) < N_min ({n_min}). Downstream statistical inference skipped.")
    elif n_actual == 0:
        mode_flag = "Data Insufficient"
        logger.warning("DATA INSUFFICIENT: No data found.")

    # 5. Generate Power Analysis Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "r2_target": r2_target,
            "power_target": power_target,
            "alpha": alpha,
            "predictor_count": k_predictors
        },
        "results": {
            "n_actual": n_actual,
            "n_min": n_min,
            "difference": n_actual - n_min,
            "is_powered": n_actual >= n_min
        },
        "mode_flag": mode_flag,
        "status": "completed"
    }

    report_path = Path("data/processed/power_analysis_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report, report_path)
    logger.info(f"Power analysis report written to {report_path}")

    # 6. Update Pre-registration
    # Calculate hash of the analysis plan (simulated here as a static string for now, 
    # in reality this would hash the spec or plan)
    plan_hash = hashlib.sha256(f"R2={r2_target},Power={power_target}".encode()).hexdigest()
    
    pre_reg_data = generate_pre_registration(plan_hash, r2_target, power_target, alpha, k_predictors)
    
    # Update pre-registration with actual predictor count if source found
    if status == "found":
        pre_reg_data["parameters"]["predictor_count"] = k_predictors
        pre_reg_data["source_verified"] = True
        write_json(pre_reg_data, Path("data/processed/pre-registration.json"))
        logger.info("Updated pre-registration.json with actual predictor count.")

    # 7. Update Mode Flag in a global state file if needed (optional, but good practice)
    # The task says "set mode flag", usually this is done in a config or manifest
    # We update the manifest or create a state file
    state_path = Path("state/projects/PROJ-164-power-analysis-state.json")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_data = {
        "task_id": "T009",
        "mode_flag": mode_flag,
        "n_actual": n_actual,
        "n_min": n_min
    }
    write_json(state_data, state_path)
    logger.info(f"Mode flag '{mode_flag}' written to state.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
