import csv
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import utilities from the existing codebase
from utils.config import get_project_root

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(input_path: Path) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors from extracted_studies.csv.
    Returns lists of floats for rows where both r and n are present.
    """
    r_values = []
    se_values = []

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')

            # Skip if r or n is missing or not numeric
            if r_val is None or n_val is None or r_val == '' or n_val == '':
                continue

            try:
                r_float = float(r_val)
                n_float = int(float(n_val))
            except (ValueError, TypeError):
                continue

            if n_float < 3:  # Need at least 3 for SE calculation
                continue

            # Fisher's Z transformation
            # z = 0.5 * ln((1+r)/(1-r))
            # SE_z = 1 / sqrt(n - 3)
            # We compute z and SE_z for the meta-analysis
            if abs(r_float) >= 1.0:
                # Clamp to valid range to avoid log(0)
                r_float = np.clip(r_float, -0.9999, 0.9999)

            z_val = 0.5 * math.log((1 + r_float) / (1 - r_float))
            se_z = 1.0 / math.sqrt(n_float - 3)

            r_values.append(z_val)
            se_values.append(se_z)

    return r_values, se_values

def run_fixed_effects_model(
    effect_sizes: List[float],
    se_values: List[float]
) -> Dict[str, Any]:
    """
    Run fixed-effects meta-analysis (inverse-variance weighted mean).
    """
    if len(effect_sizes) == 0:
        return {"error": "No data provided"}

    n = len(effect_sizes)
    weights = [1.0 / (se ** 2) for se in se_values]

    # Weighted mean
    sum_w = sum(weights)
    weighted_sum = sum(w * z for w, z in zip(weights, effect_sizes))
    pooled_z = weighted_sum / sum_w

    # Standard error of pooled estimate
    se_pooled = math.sqrt(1.0 / sum_w)

    # 95% CI
    z_crit = 1.96
    ci_lower = pooled_z - z_crit * se_pooled
    ci_upper = pooled_z + z_crit * se_pooled

    # Back-transform to r
    pooled_r = (math.exp(2 * pooled_z) - 1) / (math.exp(2 * pooled_z) + 1)
    ci_lower_r = (math.exp(2 * ci_lower) - 1) / (math.exp(2 * ci_lower) + 1)
    ci_upper_r = (math.exp(2 * ci_upper) - 1) / (math.exp(2 * ci_upper) + 1)

    # Q statistic (heterogeneity)
    # Q = sum(w * (z_i - pooled_z)^2)
    q_stat = sum(w * (z - pooled_z) ** 2 for w, z in zip(weights, effect_sizes))
    df = n - 1
    p_heterogeneity = 1.0 - stats.chi2.cdf(q_stat, df) if df > 0 else 1.0

    return {
        "model_type": "fixed_effects",
        "n_studies": n,
        "pooled_z": pooled_z,
        "pooled_r": pooled_r,
        "se_pooled": se_pooled,
        "ci_lower_z": ci_lower,
        "ci_upper_z": ci_upper,
        "ci_lower_r": ci_lower_r,
        "ci_upper_r": ci_upper_r,
        "q_statistic": q_stat,
        "df": df,
        "p_heterogeneity": p_heterogeneity
    }

def run_random_effects_model(
    effect_sizes: List[float],
    se_values: List[float],
    method: str = "DL"
) -> Dict[str, Any]:
    """
    Run random-effects meta-analysis using DerSimonian-Laird (DL) estimator.
    Falls back to fixed-effects if convergence fails.
    """
    if len(effect_sizes) == 0:
        return {"error": "No data provided", "status": "skipped", "reason": "No data"}

    n = len(effect_sizes)

    # Step 1: Compute fixed-effects weights and pooled estimate
    weights_fixed = [1.0 / (se ** 2) for se in se_values]
    sum_w_fixed = sum(weights_fixed)
    weighted_sum_fixed = sum(w * z for w, z in zip(weights_fixed, effect_sizes))
    pooled_z_fe = weighted_sum_fixed / sum_w_fixed

    # Step 2: Compute Q statistic
    q_stat = sum(w * (z - pooled_z_fe) ** 2 for w, z in zip(weights_fixed, effect_sizes))

    # Step 3: Compute tau^2 (between-study variance) using DerSimonian-Laird
    # C = sum(w) - sum(w^2)/sum(w)
    sum_w_sq = sum(w ** 2 for w in weights_fixed)
    c_val = sum_w_fixed - (sum_w_sq / sum_w_fixed)

    if c_val <= 0:
        tau_sq = 0.0
    else:
        tau_sq = max(0.0, (q_stat - (n - 1)) / c_val)

    # Step 4: Compute random-effects weights
    weights_re = [1.0 / (se ** 2 + tau_sq) for se in se_values]
    sum_w_re = sum(weights_re)
    weighted_sum_re = sum(w * z for w, z in zip(weights_re, effect_sizes))
    pooled_z_re = weighted_sum_re / sum_w_re

    # Standard error of pooled estimate
    se_pooled_re = math.sqrt(1.0 / sum_w_re)

    # 95% CI
    z_crit = 1.96
    ci_lower_z = pooled_z_re - z_crit * se_pooled_re
    ci_upper_z = pooled_z_re + z_crit * se_pooled_re

    # Back-transform to r
    pooled_r = (math.exp(2 * pooled_z_re) - 1) / (math.exp(2 * pooled_z_re) + 1)
    ci_lower_r = (math.exp(2 * ci_lower_z) - 1) / (math.exp(2 * ci_lower_z) + 1)
    ci_upper_r = (math.exp(2 * ci_upper_z) - 1) / (math.exp(2 * ci_upper_z) + 1)

    # I^2 statistic
    if q_stat > (n - 1):
        i_squared = 100.0 * (q_stat - (n - 1)) / q_stat
    else:
        i_squared = 0.0

    # H^2 statistic
    h_squared = q_stat / (n - 1) if (n - 1) > 0 else 1.0

    return {
        "model_type": "random_effects",
        "estimator": method,
        "n_studies": n,
        "tau_squared": tau_sq,
        "pooled_z": pooled_z_re,
        "pooled_r": pooled_r,
        "se_pooled": se_pooled_re,
        "ci_lower_z": ci_lower_z,
        "ci_upper_z": ci_upper_z,
        "ci_lower_r": ci_lower_r,
        "ci_upper_r": ci_upper_r,
        "q_statistic": q_stat,
        "df": n - 1,
        "i_squared": i_squared,
        "h_squared": h_squared,
        "status": "converged"
    }

def back_transform_z_to_r(z: float) -> float:
    """Back-transform Fisher's Z to Pearson's r."""
    return (math.exp(2 * z) - 1) / (math.exp(2 * z) + 1)

def run_meta_analysis(
    input_path: Path,
    gate_result_path: Path,
    output_path: Path,
    status_path: Path
) -> None:
    """
    Main function to run meta-analysis.
    Checks gate result first. If narrative_required, skips and writes status.
    Otherwise, runs random-effects model (DerSimonian-Laird).
    """
    # Load gate result
    try:
        gate_result = load_json(gate_result_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # If gate result is missing, assume narrative required to be safe
        status_data = {
            "status": "skipped",
            "reason": f"Gate result file missing or malformed: {e}",
            "timestamp": str(Path().resolve())
        }
        save_json(status_data, status_path)
        print(f"Gate result missing. Skipping meta-analysis. Reason: {e}")
        return

    synthesis_mode = gate_result.get("synthesis_mode", "narrative")
    status_value = gate_result.get("status", "narrative_required")

    if status_value == "narrative_required" or synthesis_mode == "narrative":
        status_data = {
            "status": "skipped",
            "reason": "Insufficient studies for quantitative synthesis (Narrative mode active)",
            "synthesis_mode": "narrative",
            "timestamp": str(Path().resolve())
        }
        save_json(status_data, status_path)
        print("Meta-analysis skipped: Narrative mode active due to insufficient studies.")
        return

    # Load data
    try:
        effect_sizes, se_values = load_effect_sizes_and_se(input_path)
    except FileNotFoundError:
        status_data = {
            "status": "skipped",
            "reason": f"Input file not found: {input_path}",
            "timestamp": str(Path().resolve())
        }
        save_json(status_data, status_path)
        print(f"Input file not found: {input_path}")
        return

    if len(effect_sizes) == 0:
        status_data = {
            "status": "skipped",
            "reason": "No valid effect sizes found in input data",
            "timestamp": str(Path().resolve())
        }
        save_json(status_data, status_path)
        print("No valid effect sizes found. Skipping meta-analysis.")
        return

    # Run Random-Effects Model (DerSimonian-Laird)
    # If convergence fails (e.g., numerical issues), fall back to fixed-effects
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            results = run_random_effects_model(effect_sizes, se_values, method="DL")
    except (RuntimeError, ZeroDivisionError, ValueError) as e:
        print(f"Random-effects model failed: {e}. Falling back to fixed-effects.")
        results = run_fixed_effects_model(effect_sizes, se_values)
        results["fallback_reason"] = str(e)
        results["original_model"] = "random_effects"
        results["actual_model"] = "fixed_effects"

    # Check Hartung-Knapp adjustment flag (10 <= N < 20)
    n_studies = results.get("n_studies", 0)
    hk_adjustment_needed = 10 <= n_studies < 20

    # Prepare output
    output_data = {
        "model_results": results,
        "hk_adjustment_needed": hk_adjustment_needed,
        "n_studies": n_studies,
        "status": "completed",
        "timestamp": str(Path().resolve())
    }

    # Save results
    save_json(output_data, output_path)

    # Also write status file to indicate completion
    status_data = {
        "status": "completed",
        "model_used": results.get("model_type", "unknown"),
        "n_studies": n_studies,
        "pooled_r": results.get("pooled_r"),
        "ci_lower_r": results.get("ci_lower_r"),
        "ci_upper_r": results.get("ci_upper_r"),
        "hk_adjustment_needed": hk_adjustment_needed,
        "timestamp": str(Path().resolve())
    }
    save_json(status_data, status_path)

    print(f"Meta-analysis completed. Results saved to {output_path}")
    print(f"Model: {results.get('model_type')}, N={n_studies}, Pooled r={results.get('pooled_r', 'N/A'):.4f}")

def main():
    """Entry point for the meta-analysis script."""
    project_root = get_project_root()

    # Define paths
    input_file = project_root / "data" / "processed" / "extracted_studies.csv"
    gate_result_file = project_root / "data" / "derived" / "gate_result.json"
    output_file = project_root / "data" / "derived" / "meta_results.json"
    status_file = project_root / "data" / "derived" / "meta_status.json"

    # Run analysis
    run_meta_analysis(input_file, gate_result_file, output_file, status_file)

if __name__ == "__main__":
    main()