import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

def load_study_count_from_json(file_path: Path) -> int:
    """Load study count from a JSON file."""
    if not file_path.exists():
        logger.warning(f"Study count file not found: {file_path}. Returning 0.")
        return 0
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        count = data.get('N', 0)
        if not isinstance(count, int) or count < 0:
            logger.warning(f"Invalid study count value in {file_path}: {count}. Returning 0.")
            return 0
        return count
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse study count JSON {file_path}: {e}")
        return 0

def load_effect_sizes_and_se(file_path: Path) -> Tuple[List[float], List[float]]:
    """Load effect sizes (Fisher's z) and standard errors from a JSON file."""
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return [], []
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse input JSON {file_path}: {e}")
        return [], []
    
    effects = []
    ses = []
    
    for i, study in enumerate(data):
        r = study.get('r')
        n = study.get('n')
        
        if r is None or n is None:
            logger.debug(f"Skipping study {i}: missing r or n")
            continue
        
        if not isinstance(n, (int, float)) or n <= 2:
            logger.debug(f"Skipping study {i}: invalid n ({n})")
            continue
        
        # Clamp r to (-1, 1) to avoid log domain errors
        r = float(r)
        r = max(-0.9999, min(0.9999, r))
        
        # Fisher's z transformation
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        
        effects.append(z)
        ses.append(se)
    
    if len(effects) == 0:
        logger.warning("No valid effect sizes loaded.")
    
    return effects, ses

def run_eggerr_regression(effects: List[float], ses: List[float]) -> Dict[str, Any]:
    """Run Egger's linear regression test for publication bias.
    
    Egger's test regresses the standardized effect (z / SE) against precision (1/SE).
    However, a common simplified implementation (and the one implied by the previous
    stub logic) regresses the effect size (z) against the standard error (SE).
    We will implement the regression of z on SE, as that matches the previous
    logic's variable naming and intent, while ensuring mathematical correctness.
    
    Model: z_i = beta_0 + beta_1 * SE_i + epsilon_i
    Test: H0: beta_0 = 0 (no bias)
    """
    n = len(effects)
    if n < 2:
        return {
            "egger_skipped_reason": "Skipped: Insufficient data points (N < 2) for regression."
        }
    
    x = np.array(ses, dtype=float)
    y = np.array(effects, dtype=float)
    
    # Linear regression: y = intercept + slope * x
    # Using least squares
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    denominator = n * sum_x2 - sum_x ** 2
    
    if abs(denominator) < 1e-12:
        return {
            "egger_skipped_reason": "Skipped: Variance in standard errors is effectively zero."
        }
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    # Calculate residuals and MSE
    predicted = intercept + slope * x
    residuals = y - predicted
    mse = np.sum(residuals ** 2) / (n - 2) if n > 2 else 0.0
    
    if mse < 0:
        mse = 0.0
    
    # Standard error of the intercept
    # Var(intercept) = MSE * sum(x^2) / (n * sum(x^2) - sum(x)^2)
    se_intercept_sq = mse * sum_x2 / denominator
    se_intercept = math.sqrt(se_intercept_sq) if se_intercept_sq > 0 else 0.0
    
    # t-statistic for intercept
    if se_intercept == 0:
        t_stat = 0.0
    else:
        t_stat = intercept / se_intercept
    
    # Two-tailed p-value using normal approximation (z-test)
    # For small samples, a t-distribution with n-2 df would be more accurate,
    # but scipy.stats is not guaranteed to be available without explicit import checks
    # in this constrained environment, and numpy's erf is standard.
    # Using normal approximation: P(|Z| > |t|)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    return {
        "egger_intercept": round(float(intercept), 4),
        "egger_se_intercept": round(float(se_intercept), 4),
        "egger_t_statistic": round(float(t_stat), 4),
        "egger_p_value": round(float(p_value), 4),
        "egger_result": "Significant" if p_value < 0.05 else "Not significant",
        "n_studies": n
    }

def run_bias_assessment(input_path: Path, output_path: Path, results_path: Path) -> Dict[str, Any]:
    """Run the full bias assessment pipeline.
    
    Reads N from results_path (study_count.json).
    If N < 10, outputs the skip reason.
    Otherwise, loads effect sizes from input_path, runs Egger's test, and saves results.
    """
    # Load N from study_count.json
    study_count = load_study_count_from_json(results_path)
    logger.info(f"Loaded study count N={study_count} from {results_path}")
    
    if study_count < 10:
        result = {
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression",
            "n_studies": study_count
        }
        logger.warning(result["egger_skipped_reason"])
    else:
        effects, ses = load_effect_sizes_and_se(input_path)
        if len(effects) < 2:
            result = {
                "egger_skipped_reason": "Skipped: Insufficient valid effect sizes for regression.",
                "n_studies": study_count,
                "valid_effects": len(effects)
            }
            logger.warning(result["egger_skipped_reason"])
        else:
            result = run_eggerr_regression(effects, ses)
            result["n_studies"] = study_count
            logger.info(f"Egger's test completed: p={result.get('egger_p_value', 'N/A')}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def main() -> None:
    """Main entry point for bias assessment."""
    import argparse
    parser = argparse.ArgumentParser(description="Bias assessment tool (Egger's test)")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with effect sizes (list of dicts with 'r', 'n')")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file for bias results")
    parser.add_argument("--results", type=str, required=True, help="Results JSON file (study_count.json) to check N")
    args = parser.parse_args()
    
    result = run_bias_assessment(Path(args.input), Path(args.output), Path(args.results))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
