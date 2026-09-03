import csv
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# --------------------------------------------------------------------------
# Utility Functions (Shared with other analysis modules)
# --------------------------------------------------------------------------

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(input_path: Path) -> List[Tuple[float, float, str, int]]:
    """
    Load effect sizes (r) and standard errors (SE) from extracted_studies.csv.
    Returns a list of tuples: (r, se, author, year).
    Raises ValueError if data is missing or invalid.
    """
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_str = row.get('r', '').strip()
            n_str = row.get('n', '').strip()
            author = row.get('author', 'Unknown')
            year = row.get('year', 0)

            if not r_str or not n_str:
                continue

            try:
                r = float(r_str)
                n = int(float(n_str))
                if n <= 1:
                    continue
                # Fisher's Z transformation for SE calculation
                # SE_z = 1 / sqrt(N - 3)
                se_z = 1.0 / math.sqrt(n - 3)
                # Back-transform SE to r scale is complex, but for meta-analysis
                # we often work in Z-space and back-transform the pooled result.
                # However, standard meta-analysis libraries often take r and SE_r directly.
                # Approximation for SE_r: SE_r = sqrt((1-r^2)^2 / (N-1)) is common but less stable.
                # We will perform the meta-analysis in Fisher's Z space to be statistically robust.
                # So we return Z and SE_z.
                z = 0.5 * math.log((1 + r) / (1 - r))
                data.append((z, se_z, author, year))
            except (ValueError, ZeroDivisionError):
                continue

    if not data:
        raise ValueError("No valid effect sizes (r) and sample sizes (n) found in input.")
    
    return data

# --------------------------------------------------------------------------
# Meta-Analysis Models
# --------------------------------------------------------------------------

def run_fixed_effects_model(z_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Computes a fixed-effects meta-analysis (Inverse Variance Weighted).
    Returns pooled Z, SE, and CI.
    """
    weights = [1.0 / (se ** 2) for se in se_values]
    sum_w = sum(weights)
    sum_wz = sum(w * z for w, z in zip(weights, z_values))
    
    pooled_z = sum_wz / sum_w
    pooled_se = math.sqrt(1.0 / sum_w)
    
    # 95% CI
    z_crit = 1.96
    ci_lower = pooled_z - z_crit * pooled_se
    ci_upper = pooled_z + z_crit * pooled_se
    
    return {
        "pooled_effect": pooled_z,
        "se": pooled_se,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "model_type": "fixed_effects"
    }

def run_random_effects_model(z_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Computes a DerSimonian-Laird Random-Effects Model.
    Returns pooled Z, SE, tau^2, I^2, and CI.
    """
    n = len(z_values)
    if n < 2:
        # Fallback to fixed effects if not enough studies for heterogeneity
        return run_fixed_effects_model(z_values, se_values)

    # 1. Fixed effects weights
    w_i = [1.0 / (se ** 2) for se in se_values]
    sum_w = sum(w_i)
    sum_wz = sum(w * z for w, z in zip(w_i, z_values))
    q_num = sum(w * z ** 2 for w, z in zip(w_i, z_values))
    
    pooled_z_fe = sum_wz / sum_w
    
    # Q Statistic
    Q = sum(w * z ** 2 for w, z in zip(w_i, z_values)) - (sum_wz ** 2 / sum_w)
    df = n - 1
    
    # 2. Calculate Tau^2 (DerSimonian-Laird)
    sum_w_sq = sum(w ** 2 for w in w_i)
    C = sum_w - (sum_w_sq / sum_w)
    
    if C <= 0:
        tau_sq = 0.0
    else:
        tau_sq = max(0.0, (Q - df) / C)
    
    # 3. Random Effects Weights
    w_i_re = [1.0 / (se ** 2 + tau_sq) for se in se_values]
    sum_w_re = sum(w_i_re)
    sum_wz_re = sum(w * z for w, z in zip(w_i_re, z_values))
    
    pooled_z_re = sum_wz_re / sum_w_re
    pooled_se_re = math.sqrt(1.0 / sum_w_re)
    
    # 95% CI
    z_crit = 1.96
    ci_lower = pooled_z_re - z_crit * pooled_se_re
    ci_upper = pooled_z_re + z_crit * pooled_se_re
    
    # I^2 Calculation
    if Q > df and C > 0:
        i_sq = max(0.0, (Q - df) / Q) * 100.0
    else:
        i_sq = 0.0
    
    return {
        "pooled_effect": pooled_z_re,
        "se": pooled_se_re,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "tau_squared": tau_sq,
        "q_statistic": Q,
        "i_squared": i_sq,
        "model_type": "random_effects",
        "df": df
    }

def back_transform_z_to_r(z: float) -> float:
    """Converts Fisher's Z back to Pearson's r."""
    return (math.exp(2 * z) - 1) / (math.exp(2 * z) + 1)

# --------------------------------------------------------------------------
# Main Task Logic
# --------------------------------------------------------------------------

def run_meta_analysis() -> Dict[str, Any]:
    """
    Orchestrates the meta-analysis based on gate results.
    1. Reads gate_result.json to determine synthesis mode.
    2. If quantitative_ok, runs Random-Effects (DerSimonian-Laird).
    3. Handles convergence failures by falling back to Fixed-Effects.
    4. Sets hk_adjustment_needed flag if 10 <= N < 20.
    5. Writes results to data/derived/meta_results.json and meta_status.json.
    """
    project_root = get_project_root()
    gate_path = project_root / "data" / "derived" / "gate_result.json"
    extracted_path = project_root / "data" / "processed" / "extracted_studies.csv"
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    meta_status_path = project_root / "data" / "derived" / "meta_status.json"
    
    # Load Gate Result
    if not gate_path.exists():
        raise FileNotFoundError(f"Gate result file not found: {gate_path}")
    
    gate_data = load_json(gate_path)
    status = gate_data.get("status")
    
    if status != "quantitative_ok":
        # Skip quantitative analysis
        status_output = {
            "status": "skipped",
            "reason": "Insufficient studies or narrative mode active",
            "gate_status": status
        }
        save_json(meta_status_path, status_output)
        return status_output
    
    # Load Study Count to check N for HK adjustment
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    n_studies = 0
    if study_count_path.exists():
        n_studies = load_json(study_count_path).get("N", 0)
    
    # Load Data
    try:
        data = load_effect_sizes_and_se(extracted_path)
    except ValueError as e:
        status_output = {
            "status": "failed",
            "reason": str(e),
            "gate_status": status
        }
        save_json(meta_status_path, status_output)
        return status_output
    
    z_values = [d[0] for d in data]
    se_values = [d[1] for d in data]
    
    # Run Random-Effects Model
    result = {}
    model_status = "success"
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error") # Catch warnings as errors for convergence
            result = run_random_effects_model(z_values, se_values)
    except Exception as e:
        # Convergence failure or numerical instability
        model_status = "fallback_to_fixed"
        warnings.warn(f"Random-effects model failed: {e}. Falling back to fixed-effects.")
        result = run_fixed_effects_model(z_values, se_values)
        result["fallback_reason"] = str(e)
    
    # Back-transform results to r for readability
    pooled_r = back_transform_z_to_r(result["pooled_effect"])
    # Approximate CI back-transformation (simple delta method or just transform bounds)
    ci_lower_r = back_transform_z_to_r(result["ci_lower"])
    ci_upper_r = back_transform_z_to_r(result["ci_upper"])
    
    # Determine HK Adjustment Need
    hk_adjustment_needed = False
    if 10 <= n_studies < 20:
        hk_adjustment_needed = True
    
    # Prepare Output
    output = {
        "status": "completed",
        "model_type": result.get("model_type", "unknown"),
        "pooled_effect_z": result["pooled_effect"],
        "pooled_effect_r": pooled_r,
        "se_z": result["se"],
        "ci_lower_z": result["ci_lower"],
        "ci_upper_z": result["ci_upper"],
        "ci_lower_r": ci_lower_r,
        "ci_upper_r": ci_upper_r,
        "n_studies": n_studies,
        "hk_adjustment_needed": hk_adjustment_needed,
        "model_status": model_status
    }
    
    # Add heterogeneity stats if available
    if "tau_squared" in result:
        output["tau_squared"] = result["tau_squared"]
    if "i_squared" in result:
        output["i_squared"] = result["i_squared"]
    if "q_statistic" in result:
        output["q_statistic"] = result["q_statistic"]
    
    # Save Results
    save_json(meta_results_path, output)
    
    status_output = {
        "status": "completed",
        "model_type": result.get("model_type", "unknown"),
        "n_studies": n_studies,
        "hk_adjustment_needed": hk_adjustment_needed
    }
    save_json(meta_status_path, status_output)
    
    return output

def main():
    """Entry point for the meta-analysis task."""
    try:
        result = run_meta_analysis()
        print(f"Meta-analysis completed successfully.")
        print(f"Status: {result.get('status')}")
        if result.get('status') == 'completed':
            print(f"Pooled r: {result.get('pooled_effect_r', 0):.4f}")
            print(f"HK Adjustment Needed: {result.get('hk_adjustment_needed', False)}")
    except Exception as e:
        print(f"Meta-analysis failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()