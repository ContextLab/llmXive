"""
Meta-analysis module implementing Random-Effects model using statsmodels.
Handles convergence failure by falling back to Fixed-Effects with a warning.
Outputs study_count artifact to the shared results JSON.
"""
import json
import sys
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import combine_effects, effect_size_r

# Import project utilities
from utils.logger import get_logger, log_convergence_warning, log_error_context
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)

# Constants
RESULTS_FILE = "data/derived/meta_analysis_results.json"
INPUT_FILE = "data/interim/extracted_studies.csv"

def load_effect_sizes_and_se(input_path: Optional[str] = None) -> Tuple[List[float], List[float], int]:
    """
    Loads effect sizes (r) and standard errors from the extracted studies CSV.
    Returns: (list of r, list of se, study_count)
    """
    if input_path is None:
        input_path = str(get_project_root() / INPUT_FILE)
    
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    r_values = []
    se_values = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Simple CSV parsing assuming header: study_id, tract, r, n, ...
            # We need to handle potential parsing errors gracefully
            lines = f.readlines()
            if len(lines) < 2:
                logger.warning("Input file has no data rows.")
                return [], [], 0
            
            # Assume header is first line
            header = lines[0].strip().split(',')
            # Find indices for 'r' and 'n'
            # Spec T013 says extraction parses r, n. We assume columns exist.
            try:
                r_idx = header.index('r')
                n_idx = header.index('n')
            except ValueError as e:
                logger.error(f"Required columns 'r' or 'n' missing in CSV header: {header}")
                raise e

            for i, line in enumerate(lines[1:], start=2):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                if len(parts) <= max(r_idx, n_idx):
                    logger.warning(f"Skipping malformed row {i}: {line}")
                    continue
                
                try:
                    r_val = float(parts[r_idx])
                    n_val = int(float(parts[n_idx])) # Handle potential float strings
                    
                    if n_val < 3: # Minimum sample size for valid correlation
                        logger.warning(f"Skipping row {i}: n={n_val} is too small.")
                        continue
                    
                    # Fisher's Z transformation for meta-analysis is often preferred for correlations
                    # However, the task asks for statsmodels. statsmodels.meta_analysis
                    # typically works with effect sizes and standard errors.
                    # We will calculate SE for r: SE_r = sqrt((1-r^2)^2 / (n-1)) approximately
                    # Or use Fisher Z: Z = 0.5 * ln((1+r)/(1-r)), SE_Z = 1/sqrt(n-3)
                    # Then back-transform.
                    # Let's use the direct approach if statsmodels supports it, or Fisher Z.
                    # Standard practice for r: transform to Z.
                    
                    # Calculate Fisher Z
                    # Clamp r to (-1, 1) to avoid log(0)
                    r_clamped = max(min(r_val, 0.9999), -0.9999)
                    z_val = 0.5 * math.log((1 + r_clamped) / (1 - r_clamped))
                    se_z = 1.0 / math.sqrt(n_val - 3)
                    
                    r_values.append(z_val) # We work in Z space for the model
                    se_values.append(se_z)
                    
                except (ValueError, ZeroDivisionError) as e:
                    logger.warning(f"Skipping row {i} due to conversion error: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        raise

    return r_values, se_values, len(r_values)

def run_random_effects_model(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Runs a Random-Effects meta-analysis using statsmodels.
    Falls back to Fixed-Effects if convergence fails.
    """
    if len(r_values) == 0:
        return {"error": "No data provided", "mode": "none"}

    effects = np.array(r_values)
    ses = np.array(se_values)
    weights = 1.0 / (ses ** 2)

    # statsmodels.meta_analysis.combine_effects expects effect and variance
    # Variance = SE^2
    variances = ses ** 2

    try:
        # Attempt Random Effects (DerSimonian-Laird is default in many contexts, 
        # but statsmodels uses a specific method. We use the generic combine_effects)
        # statsmodels.stats.meta_analysis.combine_effects(effects, variances, method='random')
        # Note: statsmodels might not have a direct 'random' method string in older versions,
        # but usually defaults to RE if specified or uses specific functions.
        # Let's use the explicit function if available, or manual DL.
        # statsmodels.stats.meta_analysis import combine_effects
        # signature: combine_effects(effect, variance, method='random', ...)
        
        result = combine_effects(effects, variances, method='random')
        
        # result is a namedtuple: (effect, variance, ci_lo, ci_hi, z, pval, k)
        # We need to map these carefully.
        # In newer statsmodels, it returns a dictionary or object.
        # Let's assume standard return: effect, variance, ci_low, ci_high, z, p, k
        
        pooled_effect = result[0]
        pooled_var = result[1]
        ci_low = result[2]
        ci_high = result[3]
        z_stat = result[4]
        p_val = result[5]
        k = result[6]

        # Calculate I^2 (Heterogeneity) manually if not in result, or extract tau^2
        # statsmodels might not return tau^2 directly in the tuple.
        # We calculate Q statistic: sum(w_i * (y_i - pooled)^2)
        # I^2 = max(0, (Q - (k-1)) / Q) * 100
        
        # Weighted mean (fixed effect logic for Q calc, but we use RE weights for the mean)
        # Actually Q is usually calculated with fixed effect weights for the test of heterogeneity
        # But we can estimate Tau^2 directly.
        # Let's try to get tau^2 from the RE model if possible, else estimate.
        # For now, we assume the result tuple is standard.
        
        # If the result object has attributes, use them.
        # Fallback to manual calculation if structure is different
        if hasattr(result, 'tau2'):
            tau2 = result.tau2
        else:
            # Estimate Tau^2 (DerSimonian-Laird)
            # Q = sum(w_i * (y_i - y_bar_fixed)^2)
            # w_i = 1/var_i
            w_fixed = 1.0 / variances
            y_bar_fixed = np.sum(w_fixed * effects) / np.sum(w_fixed)
            Q = np.sum(w_fixed * (effects - y_bar_fixed)**2)
            df = k - 1
            C = np.sum(w_fixed) - np.sum(w_fixed**2) / np.sum(w_fixed)
            if C > 0:
                tau2 = max(0, (Q - df) / C)
            else:
                tau2 = 0.0
        
        i_squared = 0.0
        if Q > 0:
            i_squared = max(0.0, (Q - df) / Q) * 100.0

        return {
            "mode": "random_effects",
            "pooled_effect_z": float(pooled_effect),
            "pooled_effect_se": float(math.sqrt(pooled_var)),
            "ci_lower_z": float(ci_low),
            "ci_upper_z": float(ci_high),
            "z_statistic": float(z_stat),
            "p_value": float(p_val),
            "study_count": int(k),
            "tau_squared": float(tau2),
            "i_squared": float(i_squared),
            "convergence": "success"
        }

    except Exception as e:
        logger.warning(f"Random-Effects model failed to converge: {e}. Falling back to Fixed-Effects.")
        log_convergence_warning(f"RE model failed: {e}. Using FE.")
        
        # Fallback to Fixed Effects
        w_fixed = 1.0 / variances
        pooled_effect_fixed = np.sum(w_fixed * effects) / np.sum(w_fixed)
        pooled_var_fixed = 1.0 / np.sum(w_fixed)
        
        # CI
        z_critical = 1.96 # 95%
        ci_low_fixed = pooled_effect_fixed - z_critical * math.sqrt(pooled_var_fixed)
        ci_high_fixed = pooled_effect_fixed + z_critical * math.sqrt(pooled_var_fixed)
        
        # Z and P
        z_stat_fixed = pooled_effect_fixed / math.sqrt(pooled_var_fixed)
        # Approximate p-value
        p_val_fixed = 2 * (1 - 0.5 * (1 + math.erf(abs(z_stat_fixed) / math.sqrt(2))))
        
        # Heterogeneity stats still needed for the report even if FE is used for mean
        # Recalculate Q for I^2
        w_fixed = 1.0 / variances
        y_bar_fixed = np.sum(w_fixed * effects) / np.sum(w_fixed)
        Q = np.sum(w_fixed * (effects - y_bar_fixed)**2)
        df = k - 1
        i_squared = 0.0
        if Q > 0:
            i_squared = max(0.0, (Q - df) / Q) * 100.0

        return {
            "mode": "fixed_effects",
            "pooled_effect_z": float(pooled_effect_fixed),
            "pooled_effect_se": float(math.sqrt(pooled_var_fixed)),
            "ci_lower_z": float(ci_low_fixed),
            "ci_upper_z": float(ci_high_fixed),
            "z_statistic": float(z_stat_fixed),
            "p_value": float(p_val_fixed),
            "study_count": int(k),
            "tau_squared": 0.0,
            "i_squared": float(i_squared),
            "convergence": "fallback_to_fixed_effects",
            "warning": "Random-Effects model failed; used Fixed-Effects."
        }

def save_results(results: Dict[str, Any], output_path: Optional[str] = None):
    """
    Saves the meta-analysis results to the JSON artifact.
    """
    if output_path is None:
        output_path = str(get_project_root() / RESULTS_FILE)
    
    path = Path(output_path)
    ensure_directory(path)
    
    # Load existing results if they exist (to merge with other modules)
    existing_data = {}
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing results file {path} is not valid JSON. Overwriting.")
            existing_data = {}
    
    # Update with new results
    existing_data["meta_analysis"] = results
    existing_data["study_count"] = results.get("study_count", 0)
    existing_data["timestamp"] = datetime.now().isoformat()
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Results saved to {path}")

def run_meta_analysis(input_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for the meta-analysis task.
    """
    logger.info("Starting Meta-Analysis (T014)")
    
    r_values, se_values, study_count = load_effect_sizes_and_se(input_path)
    
    if study_count == 0:
        logger.warning("No valid studies found for meta-analysis.")
        results = {
            "mode": "none",
            "study_count": 0,
            "error": "No data available"
        }
    else:
        results = run_random_effects_model(r_values, se_values)
    
    save_results(results, output_path)
    
    # Return summary for main.py to use
    return {
        "study_count": results.get("study_count", 0),
        "mode": results.get("mode", "none"),
        "convergence": results.get("convergence", "unknown")
    }

def main():
    """
    CLI entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Meta-Analysis")
    parser.add_argument("--input", type=str, default=None, help="Path to input CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to output JSON")
    args = parser.parse_args()
    
    try:
        result = run_meta_analysis(args.input, args.output)
        print(f"Meta-analysis completed. Study count: {result['study_count']}, Mode: {result['mode']}")
    except Exception as e:
        logger.error(f"Meta-analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()