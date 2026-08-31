"""
Heterogeneity analysis module for meta-analysis.
Calculates I² statistic to quantify heterogeneity among study effect sizes.
"""
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# --- Helper Functions ---

def get_project_root() -> Path:
    """
    Returns the project root directory (parent of 'code').
    """
    current_file = Path(__file__).resolve()
    # Assumes code/analysis/heterogeneity.py structure
    return current_file.parent.parent.parent

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Loads a JSON file and returns its content as a dictionary.
    Raises FileNotFoundError if the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """
    Saves a dictionary to a JSON file with indentation.
    Creates parent directories if they do not exist.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(input_path: Path) -> Tuple[List[float], List[float]]:
    """
    Loads effect sizes (r) and standard errors (se) from a CSV file.
    Expects columns: 'r' and 'se'.
    Returns two lists: effects, ses.
    Raises ValueError if required columns are missing or data is invalid.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    effects = []
    ses = []

    with open(input_path, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if 'r' not in headers or 'se' not in headers:
            raise ValueError("Input CSV must contain 'r' and 'se' columns.")

        for row in reader:
            try:
                r_val = float(row['r'])
                se_val = float(row['se'])
                # Filter out invalid or infinite values
                if math.isfinite(r_val) and math.isfinite(se_val) and se_val > 0:
                    effects.append(r_val)
                    ses.append(se_val)
            except (ValueError, TypeError):
                # Skip rows with non-numeric data
                continue

    if len(effects) == 0:
        raise ValueError("No valid effect sizes found in input CSV.")

    return effects, ses

def load_study_count_from_json(file_path: Path) -> int:
    """
    Loads the study count (N) from a JSON file.
    Expects a key 'N' or 'k'.
    """
    data = load_json(file_path)
    if 'N' in data:
        return int(data['N'])
    elif 'k' in data:
        return int(data['k'])
    else:
        raise ValueError("JSON file must contain 'N' or 'k' key.")

def calculate_i_squared(effects: List[float], ses: List[float]) -> float:
    """
    Calculates the I² statistic using the DerSimonian-Laird method.
    
    I² = max(0, (Q - df) / Q) * 100%
    where Q is Cochran's Q statistic and df = k - 1.
    
    Args:
        effects: List of effect sizes (r).
        ses: List of standard errors corresponding to effects.
    
    Returns:
        I² value as a percentage (float).
    """
    k = len(effects)
    if k < 2:
        # Cannot calculate heterogeneity with less than 2 studies
        return 0.0

    # Calculate weights (inverse variance)
    # w_i = 1 / se_i^2
    weights = [1.0 / (se ** 2) for se in ses]

    # Calculate weighted mean effect
    sum_w = sum(weights)
    weighted_mean = sum(w * e for w, e in zip(weights, effects)) / sum_w

    # Calculate Cochran's Q
    # Q = sum(w_i * (effect_i - weighted_mean)^2)
    Q = sum(w * (e - weighted_mean) ** 2 for w, e in zip(weights, effects))

    df = k - 1

    # Calculate I²
    # I² = max(0, (Q - df) / Q) * 100
    if Q <= df:
        i_squared = 0.0
    else:
        i_squared = ((Q - df) / Q) * 100.0

    return i_squared

def run_heterogeneity_analysis(
    input_csv_path: Path,
    study_count_path: Path,
    output_json_path: Path
) -> Dict[str, Any]:
    """
    Orchestrates the heterogeneity analysis:
    1. Loads study count (for logging/verification).
    2. Loads effect sizes and standard errors.
    3. Calculates I².
    4. Updates/creates the results JSON file.
    
    Args:
        input_csv_path: Path to extracted_studies.csv.
        study_count_path: Path to study_count.json.
        output_json_path: Path to results.json (or meta_results.json).
    
    Returns:
        Dictionary containing the analysis results.
    """
    # Load study count for context
    try:
        N = load_study_count_from_json(study_count_path)
    except (FileNotFoundError, ValueError) as e:
        # Log warning but proceed if possible, or raise if critical
        # For this task, we assume N is available for context but calculation depends on CSV
        N = 0

    # Load effect sizes and SEs
    try:
        effects, ses = load_effect_sizes_and_se(input_csv_path)
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Failed to load effect sizes: {e}")

    # Calculate I²
    i_squared = calculate_i_squared(effects, ses)

    # Prepare result
    result = {
        "i_squared": round(i_squared, 2),
        "k": len(effects),
        "heterogeneity_interpretation": get_heterogeneity_interpretation(i_squared)
    }

    # Update or create output JSON
    update_output_json(output_json_path, result)

    return result

def get_heterogeneity_interpretation(i_squared: float) -> str:
    """
    Provides a qualitative interpretation of the I² statistic.
    Standard thresholds: 0-25% (low), 25-50% (moderate), 50-75% (substantial), 75-100% (considerable).
    """
    if i_squared < 25:
        return "Low heterogeneity"
    elif i_squared < 50:
        return "Moderate heterogeneity"
    elif i_squared < 75:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"

def update_output_json(output_path: Path, new_data: Dict[str, Any]) -> None:
    """
    Loads an existing JSON file, updates it with new_data, and saves it back.
    If the file does not exist, creates a new one with new_data.
    """
    if output_path.exists():
        try:
            existing_data = load_json(output_path)
        except json.JSONDecodeError:
            existing_data = {}
    else:
        existing_data = {}

    existing_data.update(new_data)
    save_json(output_path, existing_data)

def main() -> int:
    """
    Main entry point for the heterogeneity analysis script.
    Expects arguments:
      --input <path_to_extracted_studies.csv>
      --study-count <path_to_study_count.json>
      --output <path_to_results.json>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Calculate I² heterogeneity statistic.")
    parser.add_argument("--input", required=True, help="Path to extracted_studies.csv")
    parser.add_argument("--study-count", required=True, help="Path to study_count.json")
    parser.add_argument("--output", required=True, help="Path to results.json")
    
    args = parser.parse_args()

    input_path = Path(args.input)
    study_count_path = Path(args.study_count)
    output_path = Path(args.output)

    try:
        result = run_heterogeneity_analysis(input_path, study_count_path, output_path)
        print(f"I² calculated: {result['i_squared']}% ({result['heterogeneity_interpretation']})")
        print(f"Results saved to: {output_path}")
        return 0
    except Exception as e:
        print(f"Error during heterogeneity analysis: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())