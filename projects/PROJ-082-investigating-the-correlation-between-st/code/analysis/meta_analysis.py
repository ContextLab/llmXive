import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import meta_analysis

# Import shared utilities from sibling modules to ensure API consistency
from utils.logger import get_logger, log_fallback, log_convergence_warning
from utils.config import get_project_root

logger = get_logger(__name__)

def load_study_count_from_json(file_path: Path) -> int:
    """
    Reads the 'N' value from study_count.json.
    Raises FileNotFoundError if the file does not exist.
    Raises KeyError if 'N' is missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Missing study count. Run T014a first. File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'N' not in data:
        raise KeyError(f"'N' key missing in {file_path}")
    
    return int(data['N'])

def load_effect_sizes_and_se(csv_path: Path) -> Tuple[List[float], List[float]]:
    """
    Loads effect sizes (r) and standard errors (se) from the extracted studies CSV.
    Returns two lists: effects and standard_errors.
    Filters out rows where r or se are missing/NaN.
    """
    import csv
    
    effects = []
    ses = []
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Extracted studies CSV not found: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            se_val = row.get('se')
            
            # Skip if missing or invalid
            if r_val is None or se_val is None or r_val == '' or se_val == '':
                continue
            
            try:
                r_float = float(r_val)
                se_float = float(se_val)
                
                # Filter out NaN or Inf
                if math.isnan(r_float) or math.isinf(r_float):
                    continue
                if math.isnan(se_float) or math.isinf(se_float):
                    continue
                
                effects.append(r_float)
                ses.append(se_float)
            except ValueError:
                # Log warning for non-numeric values if needed
                continue
    
    return effects, ses

def run_random_effects_model(effects: List[float], ses: List[float]) -> Dict[str, Any]:
    """
    Runs a Random-Effects meta-analysis using statsmodels.
    Handles convergence failures by falling back to Fixed-Effects.
    
    Returns a dictionary with:
    - pooled_effect: The estimated pooled effect size
    - ci_lower, ci_upper: 95% Confidence Interval
    - i_squared: Heterogeneity statistic
    - model_type: 'random_effects' or 'fixed_effects_fallback'
    - reliability: 'reliable' or 'unreliable'
    - success: bool
    - message: str
    """
    if not effects or not ses:
        return {
            "pooled_effect": None,
            "ci_lower": None,
            "ci_upper": None,
            "i_squared": None,
            "model_type": "none",
            "reliability": "unreliable",
            "success": False,
            "message": "No valid effect sizes or standard errors provided."
        }

    effects_arr = np.array(effects)
    ses_arr = np.array(ses)
    variances = ses_arr ** 2

    result = {
        "pooled_effect": None,
        "ci_lower": None,
        "ci_upper": None,
        "i_squared": None,
        "model_type": "random_effects",
        "reliability": "reliable",
        "success": False,
        "message": ""
    }

    # Attempt Random-Effects (DerSimonian-Laird)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # statsmodels meta_analysis defaults to DL (Random Effects)
            ma = meta_analysis(effects_arr, variances, method='DL')
            
            if w:
                for warning in w:
                    if "convergence" in str(warning.message).lower():
                        log_convergence_warning(f"Random-effects model convergence warning: {warning.message}")
                        # Trigger fallback logic
                        raise ConvergenceWarning("Model did not converge, falling back to Fixed-Effects.")

            # statsmodels returns (pooled, se, ci_lb, ci_ub, z_stat, p_value, k)
            # We need to extract i_squared manually or from the object if available
            pooled_effect = ma.pooled_effect
            se_pooled = ma.se_pooled
            ci_lb = ma.ci_lb
            ci_ub = ma.ci_ub
            
            # Calculate I-squared manually if not directly exposed in older versions
            # I^2 = (Q - (k-1)) / Q
            # Q = sum(w_i * (y_i - pooled)^2)
            # w_i = 1 / (v_i + tau^2)
            # tau^2 is estimated by DL
            tau2 = ma.tau2 if hasattr(ma, 'tau2') else 0.0
            
            if tau2 > 0:
                weights = 1.0 / (variances + tau2)
            else:
                # Fallback to inverse variance weights if tau2 is 0 (fixed effects)
                weights = 1.0 / variances
            
            Q = np.sum(weights * (effects_arr - pooled_effect)**2)
            k = len(effects)
            
            if Q > (k - 1):
                i_sq = (Q - (k - 1)) / Q
            else:
                i_sq = 0.0
            
            result["pooled_effect"] = float(pooled_effect)
            result["ci_lower"] = float(ci_lb)
            result["ci_upper"] = float(ci_ub)
            result["i_squared"] = float(i_sq)
            result["success"] = True
            result["message"] = "Random-effects model completed successfully."
            
    except Exception as e:
        # Fallback to Fixed-Effects
        log_fallback(f"Random-effects model failed ({type(e).__name__}: {e}). Falling back to Fixed-Effects.")
        result["model_type"] = "fixed_effects_fallback"
        result["reliability"] = "unreliable"
        
        try:
            # Fixed Effects: Inverse Variance Weighting
            weights = 1.0 / variances
            pooled_effect = np.sum(weights * effects_arr) / np.sum(weights)
            se_pooled = 1.0 / np.sqrt(np.sum(weights))
            
            z_score = pooled_effect / se_pooled
            # 95% CI
            from scipy.stats import norm
            z_crit = norm.ppf(0.975)
            ci_lb = pooled_effect - z_crit * se_pooled
            ci_ub = pooled_effect + z_crit * se_pooled
            
            # I-squared for fixed effects is technically not applicable in the same way,
            # but we report 0 or the calculated heterogeneity if we assume the model is wrong.
            # Standard practice: report I^2 as calculated from the data regardless of model,
            # but note the model type.
            Q = np.sum(weights * (effects_arr - pooled_effect)**2)
            if Q > (k - 1):
                i_sq = (Q - (k - 1)) / Q
            else:
                i_sq = 0.0
            
            result["pooled_effect"] = float(pooled_effect)
            result["ci_lower"] = float(ci_lb)
            result["ci_upper"] = float(ci_ub)
            result["i_squared"] = float(i_sq)
            result["success"] = True
            result["message"] = "Fixed-effects fallback completed."
            
        except Exception as fallback_err:
            result["success"] = False
            result["message"] = f"Both models failed. Random: {e}, Fixed: {fallback_err}"

    return result

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the meta-analysis results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def run_meta_analysis(study_count_path: Path, extracted_csv_path: Path, output_json_path: Path) -> Dict[str, Any]:
    """
    Main orchestration function for T014.
    1. Reads N from study_count.json.
    2. If N < 10, writes skipped status to meta_status.json.
    3. If N >= 10, runs model, writes results to results_quant.json and status to meta_status.json.
    """
    project_root = get_project_root()
    
    # Ensure output directories exist
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    status_path = project_root / "data" / "processed" / "meta_status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        n = load_study_count_from_json(study_count_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise e
    except KeyError as e:
        logger.error(str(e))
        raise e

    # Gate Logic: Check N
    if n < 10:
        logger.warning(f"Insufficient studies (N={n}). Skipping meta-analysis.")
        status_result = {
            "status": "skipped",
            "reason": "Insufficient studies",
            "N": n,
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_result, f, indent=2)
        
        # Also create a placeholder results file if needed, or just status
        # The spec says: "If N < 10: Set status: skipped... and include N in the output."
        # It does not explicitly say to write results_quant.json, but T016 expects results.json eventually.
        # We will write a minimal results file to prevent downstream crashes if T016 tries to read it.
        results_output = {
            "status": "skipped",
            "N": n,
            "data_insufficient": True,
            "limitation": "Insufficient studies for quantitative meta-analysis (N < 10)."
        }
        save_results(results_output, output_json_path)
        
        return status_result

    # Load data
    try:
        effects, ses = load_effect_sizes_and_se(extracted_csv_path)
    except FileNotFoundError as e:
        logger.error(f"Could not load extracted studies: {e}")
        raise e

    if not effects:
        logger.warning("No valid effect sizes found in extracted studies.")
        status_result = {
            "status": "skipped",
            "reason": "No valid effect sizes found",
            "N": n,
            "egger_skipped_reason": "Skipped: No valid effect sizes found"
        }
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_result, f, indent=2)
        results_output = {
            "status": "skipped",
            "reason": "No valid effect sizes found",
            "N": n
        }
        save_results(results_output, output_json_path)
        return status_result

    # Run Model
    model_results = run_random_effects_model(effects, ses)
    
    # Construct final output
    final_results = {
        "status": "completed",
        "N": n,
        "k": len(effects),
        "pooled_effect": model_results["pooled_effect"],
        "ci_lower": model_results["ci_lower"],
        "ci_upper": model_results["ci_upper"],
        "i_squared": model_results["i_squared"],
        "model_type": model_results["model_type"],
        "reliability": model_results["reliability"],
        "message": model_results["message"]
    }
    
    # Save Quantitative Results
    save_results(final_results, output_json_path)
    
    # Save Status
    status_result = {
        "status": "completed",
        "N": n,
        "k": len(effects),
        "model_type": model_results["model_type"]
    }
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status_result, f, indent=2)

    return status_result

def main():
    """
    Entry point for script execution.
    """
    project_root = get_project_root()
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    extracted_csv_path = project_root / "data" / "processed" / "extracted_studies.csv"
    output_json_path = project_root / "data" / "derived" / "results_quant.json"
    
    try:
        run_meta_analysis(study_count_path, extracted_csv_path, output_json_path)
        logger.info("Meta-analysis task completed successfully.")
    except FileNotFoundError as e:
        logger.critical(f"Critical file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Meta-analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()