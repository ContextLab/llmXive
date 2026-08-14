"""
Meta-analysis module implementing Random-Effects model with Fixed-Effects fallback.
Handles convergence failures and gate logic based on study count N.
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

# Local imports to match API surface
from utils.logger import get_logger, log_error_context
from utils.config import get_project_root

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = get_project_root()
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
STUDY_COUNT_PATH = DATA_PROCESSED / "study_count.json"
META_STATUS_PATH = DATA_PROCESSED / "meta_status.json"
RESULTS_QUANT_PATH = DATA_DERIVED / "results_quant.json"

# Ensure directories exist
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
DATA_DERIVED.mkdir(parents=True, exist_ok=True)

def load_study_count_from_json(path: Path) -> int:
    """Load N from study_count.json."""
    if not path.exists():
        raise FileNotFoundError(f"Study count file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return int(data.get('N', 0))

def load_effect_sizes_and_se(csv_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors (SE) from the extracted studies CSV.
    Expected columns: 'r', 'se' (or 'standard_error').
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {csv_path}")
    
    r_values = []
    se_values = []
    
    import csv
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows marked as narrative pool only (no quantitative r)
            if row.get('narrative_pool') == 'True' or row.get('narrative_pool') == 'true':
                if 'r' not in row or row['r'] is None or row['r'] == '':
                    continue
            
            r_val = row.get('r')
            se_val = row.get('se') or row.get('standard_error')
            
            if r_val is None or se_val is None:
                logger.warning(f"Skipping row with missing r or SE: {row}")
                continue
            
            try:
                r_float = float(r_val)
                se_float = float(se_val)
                if math.isnan(r_float) or math.isnan(se_float):
                    continue
                if se_float <= 0:
                    logger.warning(f"Invalid SE (<=0) for r={r_float}, skipping.")
                    continue
                r_values.append(r_float)
                se_values.append(se_float)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse numeric values from row: {row}")
                continue
    
    return r_values, se_values

def run_random_effects_model(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Run Random-Effects meta-analysis using statsmodels.
    Falls back to Fixed-Effects if convergence fails.
    Returns a dictionary with results and status flags.
    """
    if len(r_values) < 2:
        raise ValueError("Need at least 2 studies for meta-analysis.")

    effects = np.array(r_values)
    se = np.array(se_values)

    result = {
        "model_type": "random_effects",
        "reliability": "reliable",
        "convergence_warning": False
    }

    try:
        # Use statsmodels meta_analysis combine_effects
        # method='RE' for Random Effects (DerSimonian-Laird)
        # method='FE' for Fixed Effects
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # statsmodels combine_effects expects (effect, var)
            # var = SE^2
            variances = se ** 2
            
            # Try Random Effects first
            pooled_result = combine_effects(effects, variances, method='RE')
            
            # Check for warnings indicating convergence issues
            if any("convergence" in str(warn.message).lower() for warn in w):
                result["convergence_warning"] = True
                logger.warning("Random-Effects model convergence warning detected. Falling back to Fixed-Effects.")
                # Fallback to Fixed Effects
                pooled_result = combine_effects(effects, variances, method='FE')
                result["model_type"] = "fixed_effects_fallback"
                result["reliability"] = "unreliable"
                
        result["pooled_effect"] = float(pooled_result.effect)
        result["pooled_se"] = float(pooled_result.se)
        result["ci_lower"] = float(pooled_result.ci[0])
        result["ci_upper"] = float(pooled_result.ci[1])
        result["z_value"] = float(pooled_result.z)
        result["p_value"] = float(pooled_result.p)
        
        # Heterogeneity stats if available
        if hasattr(pooled_result, 'i2'):
            result["i_squared"] = round(float(pooled_result.i2), 2)
        else:
            result["i_squared"] = None
            
        if hasattr(pooled_result, 'tau2'):
            result["tau_squared"] = float(pooled_result.tau2)
        else:
            result["tau_squared"] = None

    except Exception as e:
        logger.error(f"Meta-analysis model failed: {e}")
        # Last resort fallback
        logger.warning("Falling back to simple weighted mean due to model failure.")
        # Manual weighted mean calculation as absolute fallback
        weights = 1.0 / (se ** 2)
        weighted_mean = np.average(effects, weights=weights)
        pooled_se = math.sqrt(1.0 / np.sum(weights))
        
        result["model_type"] = "fixed_effects_fallback"
        result["reliability"] = "unreliable"
        result["pooled_effect"] = float(weighted_mean)
        result["pooled_se"] = float(pooled_se)
        result["ci_lower"] = float(weighted_mean - 1.96 * pooled_se)
        result["ci_upper"] = float(weighted_mean + 1.96 * pooled_se)
        result["z_value"] = float(weighted_mean / pooled_se)
        result["p_value"] = 2 * (1 - 0.5 * (1 + math.erf(abs(result["z_value"]) / math.sqrt(2))))
        result["i_squared"] = None
        result["tau_squared"] = None
        result["convergence_warning"] = True

    return result

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save meta-analysis results to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def run_meta_analysis() -> Dict[str, Any]:
    """
    Main entry point for meta-analysis task.
    Reads N from study_count.json.
    If N < 10: Skips analysis, writes status 'skipped'.
    If N >= 10: Runs analysis, writes results and status 'completed'.
    """
    logger.info("Starting meta-analysis task T014.")
    
    # 1. Load N
    try:
        n = load_study_count_from_json(STUDY_COUNT_PATH)
        logger.info(f"Loaded study count N={n}")
    except FileNotFoundError as e:
        logger.error(f"Critical: {e}")
        status = {
            "status": "error",
            "reason": "study_count.json missing",
            "N": 0
        }
        save_results(status, META_STATUS_PATH)
        return status

    # 2. Gate Logic
    if n < 10:
        logger.warning(f"Insufficient studies (N={n} < 10). Skipping meta-analysis.")
        status = {
            "status": "skipped",
            "reason": "Insufficient studies",
            "N": n
        }
        save_results(status, META_STATUS_PATH)
        return status

    # 3. Load Data
    extracted_csv = DATA_PROCESSED / "extracted_studies.csv"
    try:
        r_vals, se_vals = load_effect_sizes_and_se(extracted_csv)
        if len(r_vals) < 2:
            raise ValueError("Not enough valid effect sizes for analysis.")
        logger.info(f"Loaded {len(r_vals)} valid studies for analysis.")
    except Exception as e:
        logger.error(f"Failed to load effect sizes: {e}")
        status = {
            "status": "error",
            "reason": f"Data loading failed: {str(e)}",
            "N": n
        }
        save_results(status, META_STATUS_PATH)
        return status

    # 4. Run Model
    try:
        results = run_random_effects_model(r_vals, se_vals)
        results["N"] = n
        results["status"] = "completed"
        
        # Save detailed results
        save_results(results, RESULTS_QUANT_PATH)
        
        # Update status file
        status = {
            "status": "completed",
            "model_type": results.get("model_type", "unknown"),
            "reliability": results.get("reliability", "unknown"),
            "N": n,
            "k_studies_analyzed": len(r_vals)
        }
        save_results(status, META_STATUS_PATH)
        
        logger.info("Meta-analysis completed successfully.")
        return results
        
    except Exception as e:
        logger.error(f"Meta-analysis execution failed: {e}", exc_info=True)
        status = {
            "status": "error",
            "reason": str(e),
            "N": n
        }
        save_results(status, META_STATUS_PATH)
        return status

def main():
    """CLI entry point."""
    run_meta_analysis()

if __name__ == "__main__":
    main()
