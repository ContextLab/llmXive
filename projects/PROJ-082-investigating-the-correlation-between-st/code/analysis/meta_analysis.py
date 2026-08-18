import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import meta_analysis, combine_effects
from statsmodels.stats.weightstats import DescrStatsW

# Local imports matching the provided API surface
from utils.logger import get_logger, log_error_context
from utils.config import get_project_root

logger = get_logger(__name__)

def load_study_count_from_json() -> int:
    """
    Loads the study count N from data/processed/study_count.json.
    Raises FileNotFoundError if the file is missing.
    """
    project_root = get_project_root()
    path = project_root / "data" / "processed" / "study_count.json"
    
    if not path.exists():
        raise FileNotFoundError(
            f"Missing study count. Run T014a first. Expected path: {path}"
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "N" not in data:
        raise ValueError(f"Invalid study_count.json format: missing 'N' key. Path: {path}")
    
    return int(data["N"])

def load_effect_sizes_and_se() -> Tuple[List[float], List[float]]:
    """
    Loads effect sizes (r) and standard errors (se) from data/processed/extracted_studies.csv.
    Only includes rows where 'r' and 'n' are valid numbers.
    Returns two lists: effects, ses.
    """
    project_root = get_project_root()
    path = project_root / "data" / "processed" / "extracted_studies.csv"
    
    effects = []
    ses = []
    
    if not path.exists():
        logger.warning(f"Extracted studies file not found: {path}. Returning empty lists.")
        return effects, ses
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')
            
            # Skip if r or n is missing or not a number
            if r_val is None or n_val is None:
                continue
            
            try:
                r = float(r_val)
                n = int(float(n_val)) # Handle potential string floats
                
                if n < 2:
                    continue # Invalid sample size
                
                # Calculate standard error for r (Fisher's z transformation approximation)
                # SE_z = 1 / sqrt(N - 3)
                # SE_r approx = SE_z (for large N) or use Fisher transform back
                # Standard approach: Transform r to z, compute SE_z, then back-transform if needed.
                # However, statsmodels meta_analysis often expects effect size and SE directly.
                # We will use the standard SE for r: sqrt( (1-r^2) / (n-2) ) ? 
                # Actually, for meta-analysis of correlations, Fisher's Z is standard.
                # Let's compute Z and SE_z, then we might need to convert back or pass Z.
                # The prompt asks for random effects model. statsmodels `meta_analysis` 
                # usually takes effect size and variance/se.
                # Let's stick to the standard error of the correlation coefficient itself 
                # if the model expects r, OR convert to Fisher Z if the model expects Z.
                # Given the task mentions "r", we will compute SE_r.
                # SE_r = sqrt( (1 - r^2) / (n - 2) ) is for testing against 0.
                # For meta-analysis, Fisher's Z is preferred.
                # Let's implement Fisher's Z transformation to ensure normality.
                
                # Fisher Z transformation
                z = 0.5 * math.log((1 + r) / (1 - r))
                se_z = 1.0 / math.sqrt(n - 3)
                
                # We will store Z and SE_z for the meta-analysis, then convert back if needed.
                # But the output usually expects r.
                # Let's store Z and SE_z in the lists, and handle the model input accordingly.
                # Actually, let's just store r and a calculated SE_r for simplicity if the model allows,
                # but Fisher Z is scientifically more robust.
                # Let's store Z and SE_z.
                effects.append(z)
                ses.append(se_z)
                
            except (ValueError, ZeroDivisionError):
                continue
    
    return effects, ses

def run_random_effects_model(
    effects: List[float], 
    ses: List[float]
) -> Dict[str, Any]:
    """
    Runs a Random-Effects meta-analysis using statsmodels.
    Falls back to Fixed-Effects if convergence fails.
    Returns a dictionary with results.
    """
    if not effects or not ses:
        return {
            "status": "skipped",
            "reason": "No valid effect sizes found",
            "model_type": "none"
        }
    
    effects_arr = np.array(effects)
    ses_arr = np.array(ses)
    weights = 1.0 / (ses_arr ** 2)
    
    result = {
        "status": "completed",
        "model_type": "random_effects",
        "reliability": "high"
    }
    
    try:
        # Use statsmodels meta-analysis
        # We are analyzing Fisher's Z values.
        # statsmodels.stats.meta_analysis import combine_effects
        # combine_effects(effect_size, variance, method='REML')
        # variance = se^2
        
        variances = ses_arr ** 2
        
        # Random Effects (REML)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                res = combine_effects(effect_size=effects_arr, variance=variances, method='REML')
                result["pooled_effect_z"] = float(res[0])
                result["pooled_effect_se_z"] = float(res[1])
                result["i_squared"] = float(res[2]) if len(res) > 2 else 0.0
                result["tau_squared"] = float(res[3]) if len(res) > 3 else 0.0
                
                # Check for convergence warnings
                if w:
                    for warning in w:
                        if "convergence" in str(warning.message).lower():
                            raise RuntimeError("Convergence warning detected")
            except Exception as e:
                logger.warning(f"Random-effects model failed: {e}. Falling back to Fixed-Effects.")
                raise
        
        # Convert pooled Z back to r
        pooled_r = math.tanh(result["pooled_effect_z"])
        result["pooled_effect_r"] = pooled_r
        
        # CI for Z -> CI for r
        z_lower = result["pooled_effect_z"] - 1.96 * result["pooled_effect_se_z"]
        z_upper = result["pooled_effect_z"] + 1.96 * result["pooled_effect_se_z"]
        result["ci_lower_r"] = math.tanh(z_lower)
        result["ci_upper_r"] = math.tanh(z_upper)
        
        # Calculate I-squared if not present (Cochran's Q)
        # Q = sum(w_i * (z_i - pooled_z)^2)
        # I2 = max(0, (Q - (k-1)) / Q)
        k = len(effects_arr)
        if k > 1:
            q = np.sum(weights * (effects_arr - result["pooled_effect_z"])**2)
            i2 = max(0, (q - (k - 1)) / q)
            result["i_squared"] = float(i2)
        
    except Exception as e:
        logger.warning(f"Random-effects model failed (convergence or other): {e}. Falling back to Fixed-Effects.")
        result["model_type"] = "fixed_effects_fallback"
        result["reliability"] = "unreliable"
        
        # Fixed Effects
        try:
            res_fixed = combine_effects(effect_size=effects_arr, variance=variances, method='FE')
            result["pooled_effect_z"] = float(res_fixed[0])
            result["pooled_effect_se_z"] = float(res_fixed[1])
            
            pooled_r = math.tanh(result["pooled_effect_z"])
            result["pooled_effect_r"] = pooled_r
            
            z_lower = result["pooled_effect_z"] - 1.96 * result["pooled_effect_se_z"]
            z_upper = result["pooled_effect_z"] + 1.96 * result["pooled_effect_se_z"]
            result["ci_lower_r"] = math.tanh(z_lower)
            result["ci_upper_r"] = math.tanh(z_upper)
            
            # I-squared for FE is usually 0 or calculated differently, but we can estimate
            k = len(effects_arr)
            if k > 1:
                weights_fe = 1.0 / variances
                q = np.sum(weights_fe * (effects_arr - result["pooled_effect_z"])**2)
                i2 = max(0, (q - (k - 1)) / q)
                result["i_squared"] = float(i2)
            else:
                result["i_squared"] = 0.0
                
        except Exception as e2:
            logger.error(f"Fixed-effects model also failed: {e2}")
            result["status"] = "failed"
            result["reason"] = str(e2)
            result["pooled_effect_r"] = None
            result["pooled_effect_z"] = None
            result["i_squared"] = None
            result["ci_lower_r"] = None
            result["ci_upper_r"] = None
    
    return result

def save_results(results: Dict[str, Any], status: str, reason: str = None, n: int = None):
    """
    Saves the meta-analysis results to data/derived/results_quant.json
    and status to data/processed/meta_status.json.
    """
    project_root = get_project_root()
    
    # Save status
    status_path = project_root / "data" / "processed" / "meta_status.json"
    status_data = {
        "status": status,
        "reason": reason,
        "N": n
    }
    if status == "skipped":
        status_data["egger_skipped_reason"] = "Skipped: Insufficient studies (N < 10) for Egger's regression"
    
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Saved meta_status.json to {status_path}")
    
    # Save results if completed
    if status == "completed":
        results_path = project_root / "data" / "derived" / "results_quant.json"
        # Ensure directory exists
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved results_quant.json to {results_path}")

def run_meta_analysis():
    """
    Main entry point for the meta-analysis task.
    """
    try:
        # 1. Load N
        n = load_study_count_from_json()
        logger.info(f"Loaded study count N={n}")
        
        # 2. Gate Logic: Check N
        if n < 10:
            logger.info(f"Skipping meta-analysis: N={n} < 10")
            save_results({}, status="skipped", reason="Insufficient studies", n=n)
            return
        
        # 3. Load data
        effects, ses = load_effect_sizes_and_se()
        logger.info(f"Loaded {len(effects)} valid effect sizes.")
        
        if not effects:
            logger.warning("No valid effect sizes found. Skipping analysis.")
            save_results({}, status="skipped", reason="No valid data", n=n)
            return
        
        # 4. Run model
        results = run_random_effects_model(effects, ses)
        
        # 5. Save results
        if results.get("status") == "completed":
            save_results(results, status="completed", n=n)
        else:
            save_results(results, status="failed", reason=results.get("reason", "Unknown error"), n=n)
            
    except FileNotFoundError as e:
        logger.error(str(e))
        # If study count is missing, we cannot proceed.
        # We should still write a status indicating the error if possible, 
        # but the spec says raise FileNotFoundError. 
        # However, for the pipeline to continue gracefully in T016, 
        # we might want to catch it there. Here we just let it propagate 
        # or log and exit.
        sys.exit(1)
    except Exception as e:
        logger.error(f"Meta-analysis failed with unexpected error: {e}")
        sys.exit(1)

def main():
    run_meta_analysis()

if __name__ == "__main__":
    main()
