"""
Meta-analysis module implementing Random-Effects model with Fixed-Effects fallback.
Handles gate logic based on study count N.
"""
import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import combine_effects

# Ensure imports match the existing API surface
# We assume the existence of utils.logger for logging
try:
    from utils.logger import get_logger, log_convergence_warning, log_fallback
except ImportError:
    # Fallback if utils is not in path during direct execution
    import logging
    logger = logging.getLogger(__name__)
    def get_logger(name): return logging.getLogger(name)
    def log_convergence_warning(msg): logger.warning(msg)
    def log_fallback(msg): logger.warning(msg)

logger = get_logger(__name__)

def load_study_count_from_json(json_path: str) -> int:
    """
    Reads the study count N from the generated study_count.json file.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Study count file not found: {json_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'N' not in data:
        raise ValueError(f"Invalid study count file {json_path}: Missing 'N' key")
    
    return int(data['N'])

def load_effect_sizes_and_se(csv_path: str) -> Tuple[List[float], List[float]]:
    """
    Loads effect sizes (r) and standard errors (se) from the extracted studies CSV.
    Expects columns: 'r', 'se_r' (or calculated se).
    """
    import csv
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {csv_path}")
    
    r_values = []
    se_values = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows that are not in the quantitative pool
            # The parser should have marked them, but we filter by presence of numeric r
            r_str = row.get('r', '').strip()
            se_str = row.get('se_r', '').strip()
            
            if not r_str or not se_str:
                continue
            
            try:
                r_val = float(r_str)
                se_val = float(se_str)
                if not math.isnan(r_val) and not math.isnan(se_val) and se_val > 0:
                    r_values.append(r_val)
                    se_values.append(se_val)
            except ValueError:
                continue
    
    return r_values, se_values

def run_random_effects_model(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Runs the Random-Effects meta-analysis using statsmodels.
    Handles convergence failure by falling back to Fixed-Effects.
    """
    if not r_values or not se_values:
        raise ValueError("No valid effect sizes or standard errors provided.")
    
    r_arr = np.array(r_values)
    se_arr = np.array(se_values)
    var_arr = se_arr ** 2
    
    result = {
        "model_type": "random_effects",
        "reliability": "reliable",
        "convergence_success": True
    }
    
    try:
        # statsmodels meta-analysis often uses Fisher's Z transformation for better normality
        # However, if the input is already 'r', we might need to transform or use a generic inverse-variance.
        # The standard approach in statsmodels for generic effect sizes is combine_effects.
        # We use the 'FE' and 'RE' methods.
        
        # Attempt Random Effects (DerSimonian-Laird or similar)
        # statsmodels combine_effects expects effect sizes and variances
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # 'RE' for Random Effects
            pooled_res = combine_effects(effect_sizes=r_arr, 
                                         variances=var_arr, 
                                         method='RE')
            
            # Check for convergence warnings
            if w:
                for warning in w:
                    if "convergence" in str(warning.message).lower():
                        log_convergence_warning(f"Random Effects model convergence issue: {warning.message}")
                        raise ConvergenceWarning("Convergence issue detected in Random Effects model")
                        
        result["weighted_mean_r"] = float(pooled_res.effect)
        result["ci_lower"] = float(pooled_res.ci_lb)
        result["ci_upper"] = float(pooled_res.ci_ub)
        result["p_value"] = float(pooled_res.pvalue)
        result["i_squared"] = float(pooled_res.heterogeneity_i2)
        result["q_statistic"] = float(pooled_res.heterogeneity_q)
        result["k"] = len(r_values)
        
    except (RuntimeError, Exception) as e:
        # Fallback to Fixed Effects
        if "Convergence" in str(type(e).__name__) or "convergence" in str(e).lower():
            log_fallback("Random Effects model failed to converge. Falling back to Fixed Effects.")
            result["convergence_success"] = False
        else:
            # If it's a different error, we might still try FE as a last resort or fail
            logger.warning(f"Random Effects model failed with error: {e}. Attempting Fixed Effects fallback.")
            log_fallback(f"Random Effects model failed: {e}. Falling back to Fixed Effects.")
        
        # Run Fixed Effects
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                pooled_res_fe = combine_effects(effect_sizes=r_arr, 
                                                variances=var_arr, 
                                                method='FE')
            
            result["model_type"] = "fixed_effects_fallback"
            result["reliability"] = "unreliable"
            result["weighted_mean_r"] = float(pooled_res_fe.effect)
            result["ci_lower"] = float(pooled_res_fe.ci_lb)
            result["ci_upper"] = float(pooled_res_fe.ci_ub)
            result["p_value"] = float(pooled_res_fe.pvalue)
            # I-squared is typically 0 or undefined in FE, but we report the heterogeneity stats if available
            result["i_squared"] = 0.0 
            result["q_statistic"] = float(pooled_res_fe.heterogeneity_q)
            result["k"] = len(r_values)
            
        except Exception as fe_err:
            logger.error(f"Fixed Effects fallback also failed: {fe_err}")
            raise RuntimeError(f"Both Random and Fixed Effects models failed: {fe_err}")

    return result

def save_results(output_path: str, status: str, reason: str, data: Dict[str, Any]):
    """
    Saves the meta-analysis results to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    final_data = {
        "status": status,
        "reason": reason,
        "n": data.get("k", 0),
        "timestamp": data.get("timestamp", None)
    }
    
    if status == "completed":
        final_data.update({
            "model_type": data.get("model_type"),
            "reliability": data.get("reliability"),
            "weighted_mean_r": data.get("weighted_mean_r"),
            "ci_lower": data.get("ci_lower"),
            "ci_upper": data.get("ci_upper"),
            "p_value": data.get("p_value"),
            "i_squared": data.get("i_squared"),
            "q_statistic": data.get("q_statistic"),
            "k": data.get("k")
        })
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def run_meta_analysis(
    study_count_path: str,
    extracted_studies_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point for meta-analysis.
    1. Reads N from study_count.json.
    2. If N < 10, skips analysis and signals narrative fallback.
    3. If N >= 10, runs Random-Effects model (with FE fallback).
    4. Saves results to meta_status.json (or results_quant.json as per spec).
    """
    import os
    from datetime import datetime
    
    # 1. Load N
    try:
        N = load_study_count_from_json(study_count_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        # Create a status indicating failure to find input
        save_results(output_path, "failed", f"Input file missing: {e}", {})
        return {"status": "failed", "reason": str(e)}
    
    logger.info(f"Loaded study count N={N}")
    
    # 2. Gate Logic
    if N < 10:
        logger.info(f"Insufficient studies (N={N} < 10). Skipping meta-analysis.")
        result_data = {
            "status": "skipped",
            "reason": "Insufficient studies",
            "N": N,
            "timestamp": datetime.now().isoformat()
        }
        # According to spec, if N < 10, we must signal the orchestrator.
        # We write the status file. The orchestrator (T016a) will read this.
        save_results(output_path, "skipped", "Insufficient studies", result_data)
        return result_data
    
    # 3. Run Analysis
    try:
        r_values, se_values = load_effect_sizes_and_se(extracted_studies_path)
        if not r_values:
            logger.warning("No valid effect sizes found in extracted studies.")
            save_results(output_path, "skipped", "No valid data", {"N": N})
            return {"status": "skipped", "reason": "No valid data"}
        
        analysis_result = run_random_effects_model(r_values, se_values)
        analysis_result["timestamp"] = datetime.now().isoformat()
        
        save_results(output_path, "completed", None, analysis_result)
        return analysis_result
        
    except Exception as e:
        logger.error(f"Meta-analysis execution failed: {e}")
        save_results(output_path, "failed", str(e), {"N": N})
        return {"status": "failed", "reason": str(e)}

def main():
    """
    Command-line entry point.
    Expects arguments: --study-count <path> --extracted <path> --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Meta-Analysis")
    parser.add_argument("--study-count", required=True, help="Path to study_count.json")
    parser.add_argument("--extracted", required=True, help="Path to extracted_studies.csv")
    parser.add_argument("--output", required=True, help="Path to output JSON (meta_status.json)")
    
    args = parser.parse_args()
    
    result = run_meta_analysis(
        study_count_path=args.study_count,
        extracted_studies_path=args.extracted,
        output_path=args.output
    )
    
    # Exit with code 1 if failed or skipped to signal orchestrator if needed,
    # though typically the orchestrator checks the JSON content.
    if result.get("status") in ["failed", "skipped"]:
        logger.warning(f"Meta-analysis result: {result['status']} - {result.get('reason', 'N/A')}")
        # Do not crash, let the orchestrator handle the flow
        sys.exit(0) 
    
    sys.exit(0)

if __name__ == "__main__":
    main()