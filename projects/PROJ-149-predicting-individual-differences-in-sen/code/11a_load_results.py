"""
T031a: Load Results Aggregator
Ingests all metrics (adjusted R², Bonferroni‑corrected p-values, robustness deltas,
sensitivity thresholds, feasibility logs) into a unified dictionary.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import config helpers to resolve paths
# We use a safe wrapper to handle the various calling conventions seen in the project
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution if config isn't in path yet (unlikely in project root)
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, ensure_dirs


def safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if missing or invalid."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}")
        return None


def safe_load_csv(path: str) -> Optional[pd.DataFrame]:
    """Safely load a CSV file, returning None if missing."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError as e:
        print(f"Warning: Could not load {path}: {e}")
        return None


def load_model_results() -> Dict[str, Any]:
    """Load primary model results."""
    # T017/T023 output
    path = get_path("data/processed/model_results.json")
    data = safe_load_json(path)
    if not data:
        # Return a placeholder structure to avoid crashing downstream if missing
        return {
            "adjusted_r2": None,
            "test_r2": None,
            "optimal_lambda": None,
            "rmse": None,
            "test_rmse": None,
            "post_hoc_power_analysis": {}
        }
    return data


def load_correlations_corrected() -> pd.DataFrame:
    """Load Bonferroni-corrected correlations."""
    # T021 output
    path = get_path("data/processed/correlations_corrected.csv")
    df = safe_load_csv(path)
    if df is None:
        return pd.DataFrame(columns=["band", "r_value", "p_value", "n", "significant"])
    return df


def load_non_linear_comparison() -> Dict[str, Any]:
    """Load non-linear model comparison results."""
    # T024c output
    path = get_path("data/processed/non_linear_comparison.json")
    return safe_load_json(path) or {}


def load_permutation_results() -> Dict[str, Any]:
    """Load permutation test results."""
    # T022 output
    path = get_path("data/processed/permutation_results.json")
    return safe_load_json(path) or {}


def load_robustness_results() -> Dict[str, Any]:
    """Load robustness modeling results."""
    # T025c output
    path = get_path("data/processed/robustness_model_results.json")
    return safe_load_json(path) or {}


def load_sensitivity_results() -> pd.DataFrame:
    """Load sensitivity analysis results."""
    # T026 output
    path = get_path("data/processed/sensitivity_report.csv")
    df = safe_load_csv(path)
    if df is None:
        return pd.DataFrame(columns=["threshold", "significant_count"])
    return df


def load_feasibility_report() -> Dict[str, Any]:
    """Load feasibility report from T008b."""
    # T008b output
    path = get_path("data/processed/feasibility_report.md")
    if not os.path.exists(path):
        return {"status": "unknown", "reason": "File not found"}
    
    # The file is markdown but contains a JSON block or is the JSON itself in some implementations
    # We try to parse it as JSON first, then as a markdown containing JSON
    content = ""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Attempt to extract JSON if it's wrapped in markdown
    try:
        # If the whole file is valid JSON
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # If it's markdown, look for a JSON block
    import re
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return {"status": "parse_error", "raw": content[:200]}
    
    return {"status": "unknown", "raw": content[:200]}


def load_feasibility_metrics_log() -> Dict[str, Any]:
    """Load feasibility metrics log from T032."""
    # T032 output
    path = get_path("data/processed/feasibility_metrics.log")
    if not os.path.exists(path):
        return {}
    
    # Simple parsing of log file if it exists
    # Expected format: key: value lines or JSON lines
    result = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, val = line.split(':', 1)
                result[key.strip()] = val.strip()
    return result


def aggregate_results() -> Dict[str, Any]:
    """
    Ingest all metrics into a unified dictionary.
    """
    results = {
        "model_performance": {},
        "correlations": {},
        "non_linear": {},
        "permutation": {},
        "robustness": {},
        "sensitivity": {},
        "feasibility": {},
        "meta": {
            "script": "code/11a_load_results.py",
            "task_id": "T031a"
        }
    }

    # 1. Model Results (Adjusted R2, Lambda, RMSE, Power Analysis)
    model_data = load_model_results()
    results["model_performance"] = {
        "adjusted_r2": model_data.get("adjusted_r2"),
        "test_r2": model_data.get("test_r2"),
        "optimal_lambda": model_data.get("optimal_lambda"),
        "rmse": model_data.get("rmse"),
        "test_rmse": model_data.get("test_rmse"),
        "power_analysis": model_data.get("post_hoc_power_analysis", {})
    }

    # 2. Correlations (Bonferroni Corrected)
    corr_df = load_correlations_corrected()
    results["correlations"] = {
        "significant_count": int(corr_df["significant"].sum()) if "significant" in corr_df.columns else 0,
        "total_bands": len(corr_df),
        "details": corr_df.to_dict(orient="records")
    }

    # 3. Non-Linear Comparison
    nl_data = load_non_linear_comparison()
    results["non_linear"] = {
        "significant_at_0p05": nl_data.get("significant_at_0p05", False),
        "interpretation": nl_data.get("interpretation", "N/A"),
        "linear_r2": nl_data.get("linear_r2"),
        "poly_r2": nl_data.get("polynomial_r2")
    }

    # 4. Permutation Test
    perm_data = load_permutation_results()
    results["permutation"] = {
        "observed_r2": perm_data.get("observed_r2"),
        "p_value": perm_data.get("p_value"),
        "null_distribution_path": perm_data.get("null_distribution_path")
    }

    # 5. Robustness
    robust_data = load_robustness_results()
    results["robustness"] = {
        "robustness_delta": None, # Calculated if needed, or stored directly
        "details": robust_data
    }
    # Calculate delta if both primary and robustness R2 exist
    if results["model_performance"]["test_r2"] is not None and robust_data.get("test_r2") is not None:
        results["robustness"]["robustness_delta"] = results["model_performance"]["test_r2"] - robust_data.get("test_r2")

    # 6. Sensitivity
    sens_df = load_sensitivity_results()
    results["sensitivity"] = {
        "thresholds_tested": len(sens_df),
        "max_significant_count": int(sens_df["significant_count"].max()) if not sens_df.empty else 0,
        "details": sens_df.to_dict(orient="records")
    }

    # 7. Feasibility
    feas_report = load_feasibility_report()
    feas_log = load_feasibility_metrics_log()
    results["feasibility"] = {
        "report_status": feas_report.get("status"),
        "report_reason": feas_report.get("reason"),
        "log_details": feas_log
    }

    return results


def main():
    """Entry point for T031a."""
    print("Starting T031a: Load Results Aggregation...")
    
    try:
        results = aggregate_results()
        
        # Write the unified dictionary to a JSON file
        output_path = get_path("data/processed/aggregated_results.json")
        ensure_dirs(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Successfully aggregated results to {output_path}")
        print(f"Model Adjusted R2: {results['model_performance']['adjusted_r2']}")
        print(f"Significant Correlations: {results['correlations']['significant_count']}")
        print(f"Feasibility Status: {results['feasibility']['report_status']}")
        
        return 0
    except Exception as e:
        print(f"Error during aggregation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())