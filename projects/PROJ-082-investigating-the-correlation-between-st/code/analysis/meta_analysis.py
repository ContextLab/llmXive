import json
import sys
import math
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Import logger utilities from the provided API surface
from utils.logger import get_logger, log_convergence_warning, log_fallback

logger = get_logger(__name__)

def load_effect_sizes_and_se(file_path: Path) -> Tuple[List[float], List[float]]:
    """Load effect sizes and standard errors from a JSON file.
    
    Reads the 'extracted_studies.csv' output from T013 (converted to JSON for this step
    or expects a JSON list of studies with 'r' and 'n').
    Note: The task description says input is from T014a which counts studies, but the 
    actual data needed for meta-analysis is the effect sizes from T013. 
    We assume the input file is a JSON list of study records with 'r' and 'n'.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    effects = []
    ses = []
    
    for study in data:
        r = study.get('r', 0)
        n = study.get('n', 0)
        
        if n <= 2:
            logger.warning(f"Skipping study with n={n} (too small)")
            continue
        
        # Fisher's z transformation
        # Handle edge cases where r is exactly 1 or -1 to avoid log(0)
        if r >= 1.0:
            r = 0.9999
        elif r <= -1.0:
            r = -0.9999
        
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        
        effects.append(z)
        ses.append(se)
    
    return effects, ses

def run_random_effects_model(effects: List[float], ses: List[float]) -> Dict[str, float]:
    """Run a random-effects meta-analysis model using DerSimonian-Laird estimator.
    
    Handles convergence issues by falling back to Fixed-Effects if the random-effects
    calculation produces invalid results (e.g., negative tau^2 leading to issues, 
    or if the model is unstable).
    """
    if not effects:
        return {"weighted_mean_r": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "status": "no_data"}
    
    # Calculate weights (inverse variance)
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    
    # Weighted mean of Fisher's z
    weighted_z = sum(w * z for w, z in zip(weights, effects)) / total_weight
    
    # Between-study variance (Tau^2) - DerSimonian-Laird estimator
    q = sum(w * (z - weighted_z) ** 2 for w, z in zip(weights, effects))
    df = len(effects) - 1
    
    tau_sq = 0.0
    if df > 0:
        c = total_weight - sum(w ** 2 for w in weights) / total_weight
        if c > 0:
            tau_sq = max(0, (q - df) / c)
        else:
            # Fallback if c is zero or negative (should be rare)
            logger.warning("Non-positive 'c' in DL estimator calculation. Using Fixed-Effects.")
            tau_sq = 0.0
    else:
        # Single study case
        tau_sq = 0.0
    
    # Adjusted weights for Random Effects
    adjusted_weights = [1 / (se ** 2 + tau_sq) for se in ses]
    adjusted_total_weight = sum(adjusted_weights)
    
    if adjusted_total_weight == 0:
        logger.error("Adjusted total weight is zero. Falling back to Fixed-Effects logic.")
        # Fallback to simple average if weights are all zero (unlikely but possible)
        adjusted_weighted_z = sum(effects) / len(effects)
        se_pooled = 1 / math.sqrt(len(effects)) # Approximate
    else:
        # Adjusted weighted mean
        adjusted_weighted_z = sum(w * z for w, z in zip(adjusted_weights, effects)) / adjusted_total_weight
        
        # Confidence interval
        se_pooled = 1 / math.sqrt(adjusted_total_weight)
    
    ci_lower = adjusted_weighted_z - 1.96 * se_pooled
    ci_upper = adjusted_weighted_z + 1.96 * se_pooled
    
    # Back-transform to r
    def fisher_inv(z_val):
        return (math.exp(2 * z_val) - 1) / (math.exp(2 * z_val) + 1)
    
    weighted_mean_r = fisher_inv(adjusted_weighted_z)
    ci_lower_r = fisher_inv(ci_lower)
    ci_upper_r = fisher_inv(ci_upper)
    
    return {
        "weighted_mean_r": round(weighted_mean_r, 4),
        "ci_lower": round(ci_lower_r, 4),
        "ci_upper": round(ci_upper_r, 4),
        "tau_squared": round(tau_sq, 6),
        "q_statistic": round(q, 4),
        "df": df,
        "status": "success"
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save meta-analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_meta_analysis(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """Run the full meta-analysis pipeline.
    
    This function implements the gate logic:
    1. It expects the input file to contain the list of studies.
    2. It calculates N (study count) internally from the data.
    3. If N < 10, it skips the model and writes a 'skipped' status to meta_status.json.
       However, the task says: "If N < 10, skip the model and output `data/processed/meta_status.json`... 
       If N >= 10, run the model and output `data/derived/results_quant.json`."
       
       Since this script is T014, it should handle both outputs based on the count.
       We will read the count from the input data.
    """
    # Load data
    try:
        effects, ses = load_effect_sizes_and_se(input_path)
    except Exception as e:
        logger.error(f"Failed to load data from {input_path}: {e}")
        raise
    
    study_count = len(effects)
    
    # Gate Logic: Check N
    if study_count < 10:
        logger.info(f"Study count ({study_count}) is less than 10. Skipping meta-analysis model.")
        
        # Output meta_status.json
        status_path = output_path.parent / "meta_status.json"
        status_result = {
            "status": "skipped",
            "reason": f"Insufficient studies (N={study_count} < 10)",
            "study_count": study_count
        }
        save_results(status_result, status_path)
        
        # Also output an empty results_quant.json or a placeholder indicating skip?
        # The task says: "output `data/derived/results_quant.json`" only if N >= 10.
        # So we do not create results_quant.json if skipped.
        
        return status_result
    
    # Run Random-Effects Model
    logger.info(f"Study count ({study_count}) >= 10. Running Random-Effects model.")
    results = run_random_effects_model(effects, ses)
    results["study_count"] = study_count
    
    # Save to results_quant.json
    save_results(results, output_path)
    
    return results

def main() -> None:
    """Main entry point for meta-analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Meta-analysis tool")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file (list of studies)")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file (results_quant.json)")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        results = run_meta_analysis(input_path, output_path)
        print(f"Meta-analysis complete: {results}")
    except Exception as e:
        logger.error(f"Meta-analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()