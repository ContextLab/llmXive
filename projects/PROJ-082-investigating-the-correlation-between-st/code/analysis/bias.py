import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np

def load_study_count_from_json(file_path: Path) -> int:
    """Load study count from a JSON file."""
    if not file_path.exists():
        return 0
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('N', 0)

def load_effect_sizes_and_se(file_path: Path) -> Tuple[List[float], List[float]]:
    """Load effect sizes and standard errors from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    effects = []
    ses = []
    
    for study in data:
        r = study.get('r', 0)
        n = study.get('n', 0)
        
        if n <= 2:
            continue
        
        # Fisher's z transformation
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        
        effects.append(z)
        ses.append(se)
    
    return effects, ses

def run_eggerr_regression(effects: List[float], ses: List[float]) -> Dict[str, Any]:
    """Run Egger's linear regression test for publication bias."""
    if len(effects) < 10:
        return {
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }
    
    # Standard error as predictor
    x = np.array(ses)
    y = np.array(effects)
    
    # Linear regression: y = intercept + slope * x
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        return {
            "egger_skipped_reason": "Skipped: Variance in standard errors is zero"
        }

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    # Calculate standard error of intercept
    residuals = y - (intercept + slope * x)
    mse = np.sum(residuals ** 2) / (n - 2)
    se_intercept = math.sqrt(mse * sum_x2 / denominator)
    
    # t-statistic for intercept
    t_stat = intercept / se_intercept if se_intercept != 0 else 0
    
    # Two-tailed p-value (approximation using normal distribution for large n)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    return {
        "egger_intercept": round(intercept, 4),
        "egger_se_intercept": round(se_intercept, 4),
        "egger_t_statistic": round(t_stat, 4),
        "egger_p_value": round(p_value, 4),
        "egger_result": "Significant" if p_value < 0.05 else "Not significant"
    }

def run_bias_assessment(input_path: Path, output_path: Path, results_path: Path) -> Dict[str, Any]:
    """Run the full bias assessment pipeline."""
    study_count = load_study_count_from_json(results_path)
    
    if study_count < 10:
        result = {
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }
    else:
        effects, ses = load_effect_sizes_and_se(input_path)
        result = run_eggerr_regression(effects, ses)
        result["study_count"] = study_count
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def main() -> None:
    """Main entry point for bias assessment."""
    import argparse
    parser = argparse.ArgumentParser(description="Bias assessment tool")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with effect sizes")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    parser.add_argument("--results", type=str, required=True, help="Results JSON file with study count")
    args = parser.parse_args()
    
    result = run_bias_assessment(Path(args.input), Path(args.output), Path(args.results))
    print(f"Bias assessment complete: {result}")

if __name__ == "__main__":
    main()