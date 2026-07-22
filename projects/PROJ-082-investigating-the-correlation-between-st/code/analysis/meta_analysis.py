import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import combine_effects, MetaAnalysis

from utils.logger import get_logger, log_error_context, log_fallback
from utils.config import get_project_root, get_output_path

logger = get_logger(__name__)

def load_study_count_from_json(path: Path) -> int:
    """Load N from the study count JSON file."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return int(data.get('N', 0))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to load study count from {path}: {e}")
        return 0

def load_effect_sizes_and_se(input_path: Path) -> Tuple[List[float], List[float], List[str]]:
    """
    Load effect sizes (r) and standard errors (SE) from the extracted studies CSV.
    Returns lists of r, se, and study_id for identified studies.
    Raises an exception if the file is missing or malformed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    r_values = []
    se_values = []
    study_ids = []

    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include studies with valid r and n for quantitative analysis
            try:
                r = float(row['r'])
                n = int(row['n'])
                study_id = f"{row['author']}_{row['year']}"
                
                # Calculate SE for r: SE = 1 / sqrt(N - 3)
                # This is the standard error for Fisher's z, but often used as approximation for r
                # More precise: SE_z = 1/sqrt(N-3), then transform back.
                # However, statsmodels MetaAnalysis usually expects effect sizes and their SEs.
                # We will use the SE of Fisher's Z transformed r for the model, 
                # but store the original r for reporting.
                
                # Fisher's Z transformation
                # Z = 0.5 * ln((1+r)/(1-r))
                # SE_Z = 1 / sqrt(N - 3)
                
                if n <= 3:
                    logger.warning(f"Skipping study {study_id}: N={n} is too small for SE calculation.")
                    continue

                z_val = 0.5 * math.log((1 + r) / (1 - r))
                se_z = 1.0 / math.sqrt(n - 3)
                
                r_values.append(z_val) # Store Z for the model
                se_values.append(se_z)
                study_ids.append(study_id)
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Skipping row due to invalid data: {row}. Error: {e}")
                continue

    if len(r_values) == 0:
        raise ValueError("No valid effect sizes found in input file.")
    
    return r_values, se_values, study_ids

def run_random_effects_model(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Run a Random-Effects meta-analysis using statsmodels.
    Handles convergence failures by falling back to Fixed-Effects.
    """
    effects = np.array(r_values)
    se = np.array(se_values)

    # statsmodels MetaAnalysis expects effect sizes and their standard errors
    # We are using Fisher's Z transformed effects
    ma = MetaAnalysis(effect_size=effects, se_effect=se)

    result = {
        "model_type": "random_effects",
        "reliability": "reliable",
        "convergence_warning": False
    }

    try:
        # Run random effects model (DerSimonian-Laird by default in statsmodels if not specified, 
        # but we want to be explicit or handle the specific method if needed. 
        # statsmodels combine_effects handles this)
        
        # Calculate pooled effect
        # statsmodels MetaAnalysis has a method to combine effects
        # We'll use the built-in logic which defaults to REML or DL depending on version/settings
        # For robustness, we try the standard combine_effects call.
        
        # Note: statsmodels MetaAnalysis.combine_effects returns a tuple (pooled_effect, se_pooled, ci_lower, ci_upper, ...)
        # We need to extract the relevant stats.
        
        # Let's use the explicit method from statsmodels.stats.meta_analysis
        # combine_effects(effect, se_effect, method_taylor='DL')
        
        pooled_z, se_pooled_z, ci_low_z, ci_up_z, z_stat, p_val = combine_effects(
            effects, se, method_taylor='DL'
        )

        # Transform back to r
        pooled_r = (math.exp(2 * pooled_z) - 1) / (math.exp(2 * pooled_z) + 1)
        ci_low_r = (math.exp(2 * ci_low_z) - 1) / (math.exp(2 * ci_low_z) + 1)
        ci_up_r = (math.exp(2 * ci_up_z) - 1) / (math.exp(2 * ci_up_z) + 1)

        # Calculate I-squared (Heterogeneity)
        # Q statistic
        Q = np.sum(((effects - pooled_z) ** 2) / (se ** 2))
        df = len(effects) - 1
        if df > 0:
            i_squared = max(0, (Q - df) / Q) * 100
        else:
            i_squared = 0.0

        # Egger's test p-value (placeholder, T021 handles this, but we can include a basic check or leave null)
        # T021 will calculate this properly. We just need the main effect here.
        
        result.update({
            "weighted_mean_r": round(pooled_r, 4),
            "weighted_mean_z": round(pooled_z, 4),
            "se_pooled": round(se_pooled_z, 4),
            "ci_lower_r": round(ci_low_r, 4),
            "ci_upper_r": round(ci_up_r, 4),
            "z_statistic": round(z_stat, 4),
            "p_value": round(p_val, 4),
            "i_squared": round(i_squared, 2),
            "q_statistic": round(Q, 4),
            "k": len(effects),
            "status": "completed"
        })

    except Exception as e:
        logger.warning(f"Random-effects model failed with error: {e}. Falling back to Fixed-Effects.")
        log_fallback("meta_analysis", "random_effects", "fixed_effects", str(e))
        
        # Fallback to Fixed-Effects
        try:
            pooled_z, se_pooled_z, ci_low_z, ci_up_z, z_stat, p_val = combine_effects(
                effects, se, method_taylor='FE'
            )
            
            pooled_r = (math.exp(2 * pooled_z) - 1) / (math.exp(2 * pooled_z) + 1)
            ci_low_r = (math.exp(2 * ci_low_z) - 1) / (math.exp(2 * ci_low_z) + 1)
            ci_up_r = (math.exp(2 * ci_up_z) - 1) / (math.exp(2 * ci_up_z) + 1)
            
            Q = np.sum(((effects - pooled_z) ** 2) / (se ** 2))
            df = len(effects) - 1
            i_squared = 0.0 # Not applicable for FE in same way, usually 0 or undefined
            
            result.update({
                "model_type": "fixed_effects_fallback",
                "reliability": "unreliable",
                "weighted_mean_r": round(pooled_r, 4),
                "weighted_mean_z": round(pooled_z, 4),
                "se_pooled": round(se_pooled_z, 4),
                "ci_lower_r": round(ci_low_r, 4),
                "ci_upper_r": round(ci_up_r, 4),
                "z_statistic": round(z_stat, 4),
                "p_value": round(p_val, 4),
                "i_squared": 0.0,
                "q_statistic": round(Q, 4),
                "k": len(effects),
                "status": "completed",
                "convergence_warning": True
            })
        except Exception as fallback_e:
            logger.error(f"Fixed-Effects fallback also failed: {fallback_e}")
            raise RuntimeError(f"Meta-analysis failed completely: {fallback_e}")

    return result

def save_results(results: Dict[str, Any], output_path: Path, status_path: Path, n: int):
    """
    Save the meta-analysis results to the derived JSON file.
    Also updates the meta_status.json file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the main results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved meta-analysis results to {output_path}")

    # Write the status file
    status_data = {
        "status": results.get("status", "completed"),
        "n": n,
        "model_type": results.get("model_type", "unknown"),
        "reliability": results.get("reliability", "unknown")
    }
    
    # If skipped, ensure status is set correctly
    if n < 10:
        status_data["status"] = "skipped"
        status_data["reason"] = "Insufficient studies"
    
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Saved meta-analysis status to {status_path}")

def run_meta_analysis():
    """
    Main entry point for the meta-analysis task.
    1. Read N from study_count.json.
    2. If N < 10, write skipped status and exit.
    3. If N >= 10, run the model and write results.
    """
    project_root = get_project_root()
    input_csv = project_root / "data" / "processed" / "extracted_studies.csv"
    study_count_json = project_root / "data" / "processed" / "study_count.json"
    output_json = project_root / "data" / "derived" / "results_quant.json"
    status_json = project_root / "data" / "processed" / "meta_status.json"

    # Load N
    n = load_study_count_from_json(study_count_json)
    logger.info(f"Loaded study count N={n}")

    # Gate Logic
    if n < 10:
        logger.info(f"N={n} is less than 10. Skipping quantitative meta-analysis.")
        # Write skipped status
        save_results(
            {
                "status": "skipped",
                "reason": "Insufficient studies",
                "n": n,
                "model_type": "none",
                "reliability": "n/a"
            },
            output_json,
            status_json,
            n
        )
        # Signal to orchestrator that narrative should be invoked (handled by T016a logic reading this file)
        return

    # Load data
    logger.info("Loading effect sizes and standard errors...")
    try:
        r_values, se_values, study_ids = load_effect_sizes_and_se(input_csv)
        logger.info(f"Loaded {len(r_values)} valid studies.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        # If data loading fails, we still need to write a status indicating failure/skip
        save_results(
            {
                "status": "failed",
                "reason": "Data loading error",
                "error": str(e),
                "n": n
            },
            output_json,
            status_json,
            n
        )
        sys.exit(1)

    # Run Model
    logger.info("Running Random-Effects Meta-Analysis...")
    try:
        results = run_random_effects_model(r_values, se_values)
        logger.info(f"Analysis complete. Weighted Mean r = {results['weighted_mean_r']}")
    except Exception as e:
        logger.error(f"Meta-analysis calculation failed: {e}")
        sys.exit(1)

    # Save Results
    save_results(results, output_json, status_json, n)

def main():
    run_meta_analysis()

if __name__ == "__main__":
    main()
