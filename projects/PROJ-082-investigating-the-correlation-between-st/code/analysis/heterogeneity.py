import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

def load_study_count_from_json(file_path: Path) -> int:
    """Load study count from a JSON file."""
    if not file_path.exists():
        return 0
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('study_count', 0)

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

def calculate_i_squared(effects: List[float], ses: List[float]) -> float:
    """Calculate I-squared statistic for heterogeneity."""
    if len(effects) < 2:
        return 0.0
    
    # Calculate weights
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    
    # Weighted mean
    weighted_mean = sum(w * z for w, z in zip(weights, effects)) / total_weight
    
    # Q statistic
    q = sum(w * (z - weighted_mean) ** 2 for w, z in zip(weights, effects))
    
    # Degrees of freedom
    df = len(effects) - 1
    
    if df <= 0:
        return 0.0
    
    # Calculate I-squared
    c = total_weight - sum(w ** 2 for w in weights) / total_weight
    if c == 0:
        return 0.0
    
    i_squared = max(0, (q - df) / c) * 100
    
    return i_squared

def run_heterogeneity_analysis(input_path: Path, results_path: Path) -> Dict[str, Any]:
    """Run heterogeneity analysis."""
    study_count = load_study_count_from_json(results_path)
    
    if study_count < 2:
        return {
            "i_squared": 0.0,
            "q_statistic": 0.0,
            "df": 0,
            "status": "insufficient_data"
        }
    
    effects, ses = load_effect_sizes_and_se(input_path)
    
    if len(effects) < 2:
        return {
            "i_squared": 0.0,
            "q_statistic": 0.0,
            "df": 0,
            "status": "insufficient_data"
        }
    
    i_squared = calculate_i_squared(effects, ses)
    
    # Recalculate Q for output
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    weighted_mean = sum(w * z for w, z in zip(weights, effects)) / total_weight
    q = sum(w * (z - weighted_mean) ** 2 for w, z in zip(weights, effects))
    
    return {
        "i_squared": round(i_squared, 2),  # Exactly two decimal places as per SC-002
        "q_statistic": round(q, 4),
        "df": len(effects) - 1,
        "status": "success"
    }

def update_output_json(heterogeneity_results: Dict[str, Any], output_path: Path) -> None:
    """Update the main results JSON with heterogeneity metrics."""
    if output_path.exists():
        with open(output_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    data.update(heterogeneity_results)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main() -> None:
    """Main entry point for heterogeneity analysis."""
    import argparse
    parser = argparse.ArgumentParser(description="Heterogeneity analysis tool")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file with effect sizes")
    parser.add_argument("--results", type=str, required=True, help="Results JSON file with study count")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    args = parser.parse_args()
    
    results = run_heterogeneity_analysis(Path(args.input), Path(args.results))
    update_output_json(results, Path(args.output))
    print(f"Heterogeneity analysis complete: {results}")

if __name__ == "__main__":
    main()