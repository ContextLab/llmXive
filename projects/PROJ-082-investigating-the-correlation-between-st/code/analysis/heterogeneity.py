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
    """Load effect sizes and standard errors from a JSON file.
    
    Reads from data/processed/extracted_studies.csv or a JSON equivalent.
    Converts r to Fisher's z and calculates SE = 1/sqrt(n-3).
    """
    # Determine input format based on extension or default to CSV if path looks like CSV
    # For this implementation, we expect a JSON list of studies or a CSV path.
    # Since meta_analysis.py outputs results_quant.json, we might need to read from there
    # or from the extracted_studies.csv.
    # The task description says "Append i_squared field to MetaAnalysisResult JSON".
    # We assume the input_path points to the studies data (JSON or CSV).
    
    effects = []
    ses = []
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
        
    if str(file_path).endswith('.csv'):
        import csv
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                r_str = row.get('r')
                n_str = row.get('n')
                
                if r_str is None or n_str is None:
                    continue
                
                try:
                    r = float(r_str)
                    n = int(float(n_str))
                except (ValueError, TypeError):
                    continue
                
                if n <= 3:
                    continue
                
                # Fisher's z transformation
                # Clamp r to (-1, 1) to avoid log domain errors
                r_clamped = max(-0.9999, min(0.9999, r))
                z = 0.5 * math.log((1 + r_clamped) / (1 - r_clamped))
                se = 1 / math.sqrt(n - 3)
                
                effects.append(z)
                ses.append(se)
    else:
        # Assume JSON
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle if data is a dict with a 'studies' key or a list
        studies = data if isinstance(data, list) else data.get('studies', [])
        
        for study in studies:
            r = study.get('r', 0)
            n = study.get('n', 0)
            
            if n <= 3:
                continue
            
            # Fisher's z transformation
            r_clamped = max(-0.9999, min(0.9999, float(r)))
            z = 0.5 * math.log((1 + r_clamped) / (1 - r_clamped))
            se = 1 / math.sqrt(n - 3)
            
            effects.append(z)
            ses.append(se)
    
    return effects, ses

def calculate_i_squared(effects: List[float], ses: List[float]) -> Tuple[float, float, int]:
    """Calculate I-squared statistic for heterogeneity.
    
    Returns:
        Tuple of (i_squared, q_statistic, degrees_of_freedom)
    """
    if len(effects) < 2:
        return 0.0, 0.0, 0
    
    # Calculate weights
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    
    if total_weight == 0:
        return 0.0, 0.0, len(effects) - 1
    
    # Weighted mean
    weighted_mean = sum(w * z for w, z in zip(weights, effects)) / total_weight
    
    # Q statistic
    q = sum(w * (z - weighted_mean) ** 2 for w, z in zip(weights, effects))
    
    # Degrees of freedom
    df = len(effects) - 1
    
    if df <= 0:
        return 0.0, q, 0
    
    # Calculate I-squared (Higgins & Thompson)
    # C = sum(w) - sum(w^2)/sum(w)
    c = total_weight - sum(w ** 2 for w in weights) / total_weight
    
    if c == 0:
        return 0.0, q, df
    
    i_squared = max(0.0, (q - df) / c) * 100.0
    
    return i_squared, q, df

def run_heterogeneity_analysis(input_path: Path, results_path: Path) -> Dict[str, Any]:
    """Run heterogeneity analysis.
    
    Args:
        input_path: Path to the file containing study data (CSV or JSON).
        results_path: Path to study_count.json (used to check N).
        
    Returns:
        Dictionary containing i_squared, q_statistic, df, and status.
    """
    study_count = load_study_count_from_json(results_path)
    
    # Gate: Skip if N < 2 (requires at least 2 studies for I2)
    if study_count < 2:
        return {
            "i_squared": 0.0,
            "q_statistic": 0.0,
            "df": 0,
            "status": "insufficient_data",
            "reason": f"Study count ({study_count}) is less than 2."
        }
    
    try:
        effects, ses = load_effect_sizes_and_se(input_path)
    except FileNotFoundError as e:
        return {
            "i_squared": 0.0,
            "q_statistic": 0.0,
            "df": 0,
            "status": "error",
            "reason": str(e)
        }
    
    if len(effects) < 2:
        return {
            "i_squared": 0.0,
            "q_statistic": 0.0,
            "df": 0,
            "status": "insufficient_data",
            "reason": f"Less than 2 valid studies found in input ({len(effects)})."
        }
    
    i_squared, q, df = calculate_i_squared(effects, ses)
    
    # Precision Requirement: Exactly two decimal places for I2 (SC-002, FR-002)
    return {
        "i_squared": round(i_squared, 2),
        "q_statistic": round(q, 4),
        "df": df,
        "status": "success"
    }

def update_output_json(heterogeneity_results: Dict[str, Any], output_path: Path) -> None:
    """Update the main results JSON with heterogeneity metrics.
    
    Appends i_squared, q_statistic, and df to the existing JSON at output_path.
    """
    if output_path.exists():
        with open(output_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Update with new results
    data.update(heterogeneity_results)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main() -> None:
    """Main entry point for heterogeneity analysis.
    
    Usage:
        python -m code.analysis.heterogeneity --input <input_file> --results <study_count.json> --output <results.json>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Heterogeneity analysis tool (I-squared calculation)")
    parser.add_argument("--input", type=str, required=True, help="Input file with study data (CSV or JSON)")
    parser.add_argument("--results", type=str, required=True, help="Path to study_count.json to check N")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file to update")
    args = parser.parse_args()
    
    results = run_heterogeneity_analysis(Path(args.input), Path(args.results))
    update_output_json(results, Path(args.output))
    
    print(f"Heterogeneity analysis complete: {results}")
    if results.get('status') != 'success':
        print(f"Warning: {results.get('reason', 'Unknown reason')}")

if __name__ == "__main__":
    main()