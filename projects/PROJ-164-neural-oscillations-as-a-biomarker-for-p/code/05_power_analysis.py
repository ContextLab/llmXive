import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing utilities from the project
try:
    from utils.io_helpers import load_json, write_json
    from utils.logging_setup import get_logger, log_mode_switch
except ImportError:
    # Fallback for direct execution context if utils not in path yet
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.io_helpers import load_json, write_json
    from utils.logging_setup import get_logger, log_mode_switch

# Constants from spec (FR-007, FR-008)
R2_TARGET = 0.1
POWER_TARGET = 0.80
ALPHA = 0.05
PREDICTOR_COUNT = 5  # Estimated number of features (bands + connectivity)

logger = get_logger(__name__)

def calculate_sample_size_r2(r2: float, power: float, alpha: float, predictors: int) -> int:
    """
    Calculate minimum sample size (N) for a multiple regression given:
    - r2: Expected R-squared (effect size)
    - power: Desired statistical power (1 - beta)
    - alpha: Significance level
    - predictors: Number of independent variables

    Uses the approximation for F-test in multiple regression:
    f2 = R2 / (1 - R2)
    u = predictors
    v = N - u - 1
    We solve for N using non-central F distribution parameters.
    Since we cannot import statsmodels here to avoid heavy dependency if not installed,
    we use a standard approximation or a simplified lookup logic.
    
    However, for robustness and to avoid external heavy deps if not needed,
    we will use scipy.stats if available, or a standard approximation formula.
    
    Formula approximation (Cohen's f2):
    f2 = R2 / (1 - R2)
    N = (L / f2) + u + 1
    Where L is the non-centrality parameter lambda required for the power.
    For alpha=0.05, power=0.80, u=5, L is approximately 12-14.
    
    More precise calculation using scipy if available:
    """
    try:
        from statsmodels.stats.power import FTestAnovaPower
        effect_size = r2 / (1 - r2)
        analysis = FTestAnovaPower()
        n = analysis.solve_power(effect_size=effect_size, 
                                 alpha=alpha, 
                                 power=power, 
                                 n_groups=1, # Not used for regression directly, but F-test
                                 numerator_df=predictors)
        # The solve_power for FTestAnovaPower usually expects n_groups for ANOVA.
        # For regression, we map: numerator_df = predictors, denominator_df = N - predictors - 1.
        # statsmodels FTestPower is better, but FTestAnovaPower is often used as proxy.
        # Let's use a more direct approach with FTestPower if available, or fallback.
        
        # Actually, FTestAnovaPower is for ANOVA. For regression, we need FTestPower.
        # Let's try FTestPower from statsmodels.stats.power
        from statsmodels.stats.power import FTestPower
        f2 = effect_size
        # We need to solve for N given f2, alpha, power, u (numerator df)
        # The denominator df v = N - u - 1.
        # FTestPower.solve_power expects effect_size, alpha, power, nobs1 (numerator?), df2?
        # Let's use the iterative approach or a standard approximation if statsmodels is tricky.
        
        # Standard approximation for multiple regression:
        # N >= (lambda / f2) + u + 1
        # For alpha=0.05, power=0.80, u=5, lambda is roughly 13.0
        # f2 = 0.1 / 0.9 = 0.111
        # N >= 13.0 / 0.111 + 5 + 1 = 117 + 6 = 123
        
        # Let's try to use statsmodels FTestPower correctly
        from statsmodels.stats.power import FTestPower
        f2 = r2 / (1 - r2)
        # We need to find nobs such that power is achieved.
        # FTestPower.solve_power(effect_size, alpha, power, df_num, df_denom=None)
        # df_num = predictors
        # We iterate to find nobs (total sample size)
        
        power_analysis = FTestPower()
        # We can't solve directly for df_denom easily in one call without nobs.
        # We use a simple loop to find N.
        n_min = predictors + 2
        while True:
            df_denom = n_min - predictors - 1
            if df_denom <= 0:
                n_min += 1
                continue
            # Calculate power for this N
            current_power = power_analysis.power(effect_size=f2, alpha=alpha, df_num=predictors, df_denom=df_denom)
            if current_power >= power:
                return n_min
            n_min += 1
            if n_min > 10000: # Safety break
                break
        return n_min

    except ImportError:
        logger.warning("statsmodels not found. Using approximation formula.")
        # Approximation: N = (L / f2) + u + 1
        # L for alpha=0.05, power=0.80, u=5 is approx 12.97 (from tables)
        f2 = r2 / (1 - r2)
        L = 13.0 
        n = (L / f2) + predictors + 1
        return int(n)

def generate_pre_registration(r2_target: float, power: float, alpha: float, predictors: int) -> Dict[str, Any]:
    """
    Generate the pre-registration JSON artifact.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    plan_params = {
        "r2_target": r2_target,
        "power_target": power,
        "alpha": alpha,
        "predictor_count": predictors
    }
    
    # Create a deterministic hash of the plan to ensure integrity
    plan_str = json.dumps(plan_params, sort_keys=True)
    plan_hash = hashlib.sha256(plan_str.encode('utf-8')).hexdigest()
    
    pre_registration = {
        "timestamp": timestamp,
        "analysis_plan_hash": plan_hash,
        "parameters": plan_params,
        "status": "pending"
    }
    return pre_registration

def main():
    """
    Main entry point for Power Analysis task (T009).
    1. Load verified source manifest (from T011).
    2. If data exists (Primary Mode), perform power analysis.
    3. Generate pre-registration.json.
    4. Calculate N_min.
    5. Compare with N_actual (from manifest).
    6. Generate power_analysis_report.json.
    7. Set mode flag if underpowered.
    """
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "verified_source_manifest.json"
    pre_reg_path = project_root / "data" / "pre-registration.json"
    report_path = project_root / "data" / "power_analysis_report.json"
    state_path = project_root / "state" / "projects" / "PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml"

    # Load manifest
    if not manifest_path.exists():
        logger.error("verified_source_manifest.json not found. T011 must run first.")
        # If manifest missing, we can't proceed. Assuming T011 failed or didn't run.
        # We will create a report indicating failure to verify source.
        report = {
            "status": "failed",
            "reason": "Source manifest missing",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        write_json(report_path, report)
        return

    manifest = load_json(manifest_path)
    mode_flag = manifest.get("mode", "Unknown")
    
    if mode_flag == "Data Insufficient":
        logger.info("Data Insufficient mode detected. Skipping power analysis.")
        # Even if data insufficient, we might want to record the plan for transparency?
        # The task says: "Perform prospective power analysis *after* T011 confirms data existence."
        # If T011 says no data, we might not need to run the analysis, but we should record the intent.
        # However, the task specifically says "If N_actual < N_min, set mode flag to Underpowered".
        # If no data, N_actual = 0. N_min > 0. So it is underpowered.
        # But the pipeline usually stops at T012 for Data Insufficient.
        # Let's assume we run it anyway to document the "Underpowered" state if we were to try.
        # But strictly, if mode is Data Insufficient, T012 terminates.
        # We will generate the report indicating Data Insufficient.
        report = {
            "status": "skipped",
            "reason": "Data Insufficient - No dataset found",
            "mode_flag": "Data Insufficient",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        write_json(report_path, report)
        return

    if mode_flag != "Primary":
        logger.warning(f"Mode is {mode_flag}. Power analysis may not be applicable.")
        # Proceed only if we have data to analyze power for
        pass

    # 1. Generate Pre-registration
    pre_reg = generate_pre_registration(R2_TARGET, POWER_TARGET, ALPHA, PREDICTOR_COUNT)
    pre_reg["status"] = "registered"
    write_json(pre_reg_path, pre_reg)
    logger.info(f"Pre-registration saved to {pre_reg_path}")

    # 2. Calculate N_min
    n_min = calculate_sample_size_r2(R2_TARGET, POWER_TARGET, ALPHA, PREDICTOR_COUNT)
    logger.info(f"Minimum sample size required: {n_min}")

    # 3. Get N_actual from manifest
    # Manifest structure from T011: {"mode": "...", "datasets": [...], "subject_count": int}
    n_actual = manifest.get("subject_count", 0)
    if n_actual == 0 and "datasets" in manifest and len(manifest["datasets"]) > 0:
        # Fallback if subject_count not explicitly set but data exists
        # We assume at least 1 if datasets exist, but we need a real number.
        # If T011 didn't count, we might need to re-scan or assume 0.
        # For safety, if not counted, we assume 0 and mark as underpowered.
        n_actual = 0 

    # 4. Determine Status and Mode
    is_underpowered = n_actual < n_min
    final_status = "underpowered" if is_underpowered else "powered"
    
    # 5. Generate Report
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "analysis_plan_hash": pre_reg["analysis_plan_hash"],
        "parameters": {
            "r2_target": R2_TARGET,
            "power_target": POWER_TARGET,
            "alpha": ALPHA,
            "predictor_count": PREDICTOR_COUNT
        },
        "results": {
            "n_min": n_min,
            "n_actual": n_actual,
            "is_underpowered": is_underpowered,
            "status": final_status
        },
        "mode_flag_update": "Underpowered" if is_underpowered else None
    }
    write_json(report_path, report)
    logger.info(f"Power analysis report saved to {report_path}")

    # 6. Update Mode Flag if Underpowered
    if is_underpowered:
        # Update manifest to reflect Underpowered mode
        manifest["mode"] = "Underpowered"
        manifest["reason"] = f"Sample size ({n_actual}) < Minimum required ({n_min})"
        write_json(manifest_path, manifest)
        log_mode_switch("Underpowered", "Power Analysis (T009)")
        logger.warning(f"Mode set to Underpowered. N_actual={n_actual}, N_min={n_min}")
    else:
        logger.info(f"Study is powered. N_actual={n_actual} >= N_min={n_min}")

    return report

if __name__ == "__main__":
    main()
