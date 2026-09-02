"""
Meta-Analysis Implementation
Runs DerSimonian-Laird Random-Effects model with fallback to Fixed-Effects.
Handles gate logic and Hartung-Knapp adjustment flags.
"""

import csv
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Utility Functions (Standardized with project API surface) ---

def get_project_root() -> Path:
    """Returns the root directory of the project (parent of 'code')."""
    current = Path(__file__).resolve()
    # Navigate up from code/analysis to project root
    return current.parent.parent.parent

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load extracted studies and filter for valid r and n.
    Returns list of dicts with 'r', 'se', 'author', 'year'.
    """
    studies = []
    if not input_path.exists():
        return studies

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')
            
            # Check for valid numeric data
            if r_val is None or n_val is None or r_val == '' or n_val == '':
                continue
            
            try:
                r = float(r_val)
                n = int(n_val)
                if n <= 0:
                    continue
                
                # Fisher's Z transformation for meta-analysis stability
                # z = 0.5 * ln((1+r)/(1-r))
                # SE_z = 1 / sqrt(N - 3)
                # We perform meta-analysis on Z, then back-transform if needed,
                # but standard practice often reports pooled Z or back-transformed r.
                # Here we compute Z and SE_Z for the model.
                
                if abs(r) >= 1.0:
                    # Clamp to avoid log(0) or complex numbers if r is exactly 1 or -1
                    # Though strictly r should be < 1.
                    r = math.copysign(0.9999, r)
                    
                z = 0.5 * math.log((1 + r) / (1 - r))
                se_z = 1.0 / math.sqrt(n - 3)
                
                studies.append({
                    'author': row.get('author', 'Unknown'),
                    'year': row.get('year', 0),
                    'z': z,
                    'se': se_z,
                    'r': r, # Keep original r for reference
                    'n': n
                })
            except (ValueError, ZeroDivisionError):
                continue
                
    return studies

# --- Meta-Analysis Models ---

def run_fixed_effects_model(studies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run Inverse-Variance Fixed Effects Model.
    Returns pooled effect (Z), SE, and CI.
    """
    if not studies:
        return {'pooled_z': 0, 'se': 0, 'ci_lower': 0, 'ci_upper': 0, 'k': 0}

    sum_wz = 0.0
    sum_w = 0.0
    sum_wz2 = 0.0
    sum_w2 = 0.0

    for s in studies:
        w = 1.0 / (s['se'] ** 2)
        sum_w += w
        sum_wz += w * s['z']
        sum_wz2 += w * (s['z'] ** 2)
        sum_w2 += w * w

    pooled_z = sum_wz / sum_w
    se_pooled = math.sqrt(1.0 / sum_w)
    
    # 95% CI
    z_crit = 1.96
    ci_lower = pooled_z - z_crit * se_pooled
    ci_upper = pooled_z + z_crit * se_pooled

    return {
        'pooled_z': pooled_z,
        'se': se_pooled,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'k': len(studies),
        'model_type': 'fixed_effects'
    }

def run_random_effects_model(studies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run DerSimonian-Laird Random-Effects Model.
    Calculates Q, Tau^2, and re-weights.
    """
    if not studies:
        return {'pooled_z': 0, 'se': 0, 'ci_lower': 0, 'ci_upper': 0, 'k': 0, 'tau2': 0}

    # 1. Calculate Q (Heterogeneity)
    # Q = sum(w_i * (z_i - pooled_z_FE)^2)
    # First, get FE pooled Z
    fe_result = run_fixed_effects_model(studies)
    pooled_z_fe = fe_result['pooled_z']
    
    q = 0.0
    for s in studies:
        w = 1.0 / (s['se'] ** 2)
        q += w * ((s['z'] - pooled_z_fe) ** 2)

    k = len(studies)
    df = k - 1
    
    # 2. Calculate C (for Tau^2)
    sum_w = sum(1.0 / (s['se'] ** 2) for s in studies)
    sum_w2 = sum((1.0 / (s['se'] ** 2)) ** 2 for s in studies)
    c = sum_w - (sum_w2 / sum_w)
    
    # 3. Calculate Tau^2 (DerSimonian-Laird)
    tau2 = max(0, (q - df) / c) if c > 0 else 0

    # 4. Calculate new weights and pooled effect
    sum_w_prime = 0.0
    sum_wz_prime = 0.0
    
    for s in studies:
        w_prime = 1.0 / ((s['se'] ** 2) + tau2)
        sum_w_prime += w_prime
        sum_wz_prime += w_prime * s['z']
    
    if sum_w_prime == 0:
        # Fallback to FE if weights collapse
        return run_fixed_effects_model(studies)

    pooled_z = sum_wz_prime / sum_w_prime
    se_pooled = math.sqrt(1.0 / sum_w_prime)
    
    z_crit = 1.96
    ci_lower = pooled_z - z_crit * se_pooled
    ci_upper = pooled_z + z_crit * se_pooled

    return {
        'pooled_z': pooled_z,
        'se': se_pooled,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'k': k,
        'tau2': tau2,
        'q': q,
        'model_type': 'random_effects_dls'
    }

def run_meta_analysis(
    studies_path: Path, 
    gate_path: Path, 
    study_count_path: Path,
    output_status_path: Path,
    output_results_path: Path
) -> Dict[str, Any]:
    """
    Orchestrates the meta-analysis based on gate results.
    """
    # 1. Check Gate
    try:
        gate_data = load_json(gate_path)
    except FileNotFoundError:
        # If gate file missing, assume narrative required for safety
        status_data = {
            "status": "skipped",
            "reason": "Gate file missing. Assuming narrative path."
        }
        save_json(status_data, output_status_path)
        return status_data

    if gate_data.get('status') != 'quantitative_ok':
        status_data = {
            "status": "skipped",
            "reason": gate_data.get('reason', 'Insufficient studies')
        }
        save_json(status_data, output_status_path)
        return status_data

    # 2. Load Data
    studies = load_effect_sizes_and_se(studies_path)
    
    if len(studies) < 2:
        status_data = {
            "status": "skipped",
            "reason": "Less than 2 valid studies for meta-analysis."
        }
        save_json(status_data, output_status_path)
        return status_data

    # 3. Run Model
    # Try Random Effects first
    result = None
    model_status = "random_effects"
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = run_random_effects_model(studies)
        if result['tau2'] == 0 and len(studies) > 2:
            # If tau2 is 0, it's essentially fixed effects, but we keep RE label
            pass
    except Exception as e:
        # Fallback to Fixed Effects on convergence failure
        model_status = "fixed_effects_fallback"
        result = run_fixed_effects_model(studies)

    # 4. Check Hartung-Knapp Condition
    # Read study count N
    try:
        count_data = load_json(study_count_path)
        N = count_data.get('N', 0)
    except (FileNotFoundError, KeyError):
        N = 0

    hk_adjustment_needed = False
    if 10 <= N < 20:
        hk_adjustment_needed = True

    # 5. Prepare Output
    # Back-transform Z to r for interpretability
    pooled_r = math.tanh(result['pooled_z'])
    ci_lower_r = math.tanh(result['ci_lower'])
    ci_upper_r = math.tanh(result['ci_upper'])

    final_results = {
        "pooled_effect_r": round(pooled_r, 4),
        "ci_lower_r": round(ci_lower_r, 4),
        "ci_upper_r": round(ci_upper_r, 4),
        "k": result['k'],
        "model_type": result['model_type'],
        "hk_adjustment_needed": hk_adjustment_needed,
        "status": "completed"
    }

    if model_status == "random_effects_dls":
        final_results['tau2'] = round(result['tau2'], 6)
        final_results['q'] = round(result['q'], 4)

    # 6. Write Files
    save_json({
        "status": "completed",
        "model": model_status
    }, output_status_path)
    
    save_json(final_results, output_results_path)

    return final_results

def main():
    """Entry point for the meta-analysis script."""
    project_root = get_project_root()
    
    studies_path = project_root / 'data' / 'processed' / 'extracted_studies.csv'
    gate_path = project_root / 'data' / 'derived' / 'gate_result.json'
    study_count_path = project_root / 'data' / 'processed' / 'study_count.json'
    
    status_out = project_root / 'data' / 'derived' / 'meta_status.json'
    results_out = project_root / 'data' / 'derived' / 'meta_results.json'

    try:
        result = run_meta_analysis(
            studies_path, 
            gate_path, 
            study_count_path,
            status_out,
            results_out
        )
        print(f"Meta-analysis completed. Status: {result.get('status')}")
        sys.exit(0)
    except Exception as e:
        print(f"Error running meta-analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()