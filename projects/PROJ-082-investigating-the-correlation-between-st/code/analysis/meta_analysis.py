import json
import sys
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

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

def run_random_effects_model(effects: List[float], ses: List[float]) -> Dict[str, float]:
    """Run a random-effects meta-analysis model."""
    if not effects:
        return {"weighted_mean_r": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    
    # Calculate weights (inverse variance)
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    
    # Weighted mean of Fisher's z
    weighted_z = sum(w * z for w, z in zip(weights, effects)) / total_weight
    
    # Between-study variance (Tau^2) - DerSimonian-Laird estimator
    q = sum(w * (z - weighted_z) ** 2 for w, z in zip(weights, effects))
    df = len(effects) - 1
    
    if df > 0:
        c = total_weight - sum(w ** 2 for w in weights) / total_weight
        tau_sq = max(0, (q - df) / c)
    else:
        tau_sq = 0
    
    # Adjusted weights
    adjusted_weights = [1 / (se ** 2 + tau_sq) for se in ses]
    adjusted_total_weight = sum(adjusted_weights)
    
    # Adjusted weighted mean
    adjusted_weighted_z = sum(w * z for w, z in zip(adjusted_weights, effects)) / adjusted_total_weight
    
    # Confidence interval
    se_pooled = 1 / math.sqrt(adjusted_total_weight)
    ci_lower = adjusted_weighted_z - 1.96 * se_pooled
    ci_upper = adjusted_weighted_z + 1.96 * se_pooled
    
    # Back-transform to r
    weighted_mean_r = (math.exp(2 * adjusted_weighted_z) - 1) / (math.exp(2 * adjusted_weighted_z) + 1)
    ci_lower_r = (math.exp(2 * ci_lower) - 1) / (math.exp(2 * ci_lower) + 1)
    ci_upper_r = (math.exp(2 * ci_upper) - 1) / (math.exp(2 * ci_upper) + 1)
    
    return {
        "weighted_mean_r": round(weighted_mean_r, 4),
        "ci_lower": round(ci_lower_r, 4),
        "ci_upper": round(ci_upper_r, 4),
        "tau_squared": round(tau_sq, 6),
        "q_statistic": round(q, 4),
        "df": df
    }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save meta-analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def run_meta_analysis(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """Run the full meta-analysis pipeline."""
    effects, ses = load_effect_sizes_and_se(input_path)
    
    if not effects:
        results = {
            "weighted_mean_r": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "study_count": 0,
            "status": "no_data"
        }
    else:
        analysis_results = run_random_effects_model(effects, ses)
        results = {
            **analysis_results,
            "study_count": len(effects),
            "status": "success"
        }
    
    save_results(results, output_path)
    return results

def main() -> None:
    """Main entry point for meta-analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Meta-analysis tool")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    args = parser.parse_args()
    
    results = run_meta_analysis(Path(args.input), Path(args.output))
    print(f"Meta-analysis complete: {results}")

if __name__ == "__main__":
    main()