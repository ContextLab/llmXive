"""
External Validation Proxy for Synthetic Distribution.

This module attempts to validate the synthetic distribution against a small,
verified proxy dataset (if available). If no proxy exists, it documents the
limitation in the output JSON.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# SciPy for KS test
from scipy.stats import ks_2samp

# Add project root to path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config

PROXY_FILE_NAME = "proxy_dataset.json"
METRICS_TO_CHECK = ["sequence_entropy", "tool_repetition_freq", "arg_semantic_variance"]


def load_json_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file containing a list of trace dictionaries."""
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    # If it's a single object or a dict with a list inside, try to find it
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                return data[key]
    return []


def extract_metric_values(data: List[Dict[str, Any]], metric_name: str) -> List[float]:
    """Extract a specific metric value from a list of trace dictionaries."""
    values = []
    for item in data:
        if metric_name in item:
            val = item[metric_name]
            if isinstance(val, (int, float)) and not (isinstance(val, float) and (val != val)): # Check for NaN
                values.append(float(val))
    return values


def run_ks_test(synthetic_values: List[float], proxy_values: List[float], metric_name: str) -> Dict[str, Any]:
    """
    Perform a Kolmogorov-Smirnov test between two distributions.
    Returns a dict with statistic and p-value.
    """
    if len(synthetic_values) < 2 or len(proxy_values) < 2:
        return {
            "metric": metric_name,
            "ks_statistic": None,
            "p_value": None,
            "reason": "insufficient_data_points"
        }

    statistic, p_value = ks_2samp(synthetic_values, proxy_values)
    return {
        "metric": metric_name,
        "ks_statistic": float(statistic),
        "p_value": float(p_value),
        "is_significant_shift": p_value < 0.05
    }


def run_validation_proxy() -> Dict[str, Any]:
    """
    Main logic for T000.
    Attempts to find a proxy dataset, run KS tests, and report results.
    """
    config = get_config()
    # Assuming proxy would be in data/raw or a specific proxy dir if it existed
    # The task says "if available". We check common locations.
    possible_proxy_paths = [
        Path(config.DATA_DIR) / "proxy" / PROXY_FILE_NAME,
        Path(config.DATA_DIR) / PROXY_FILE_NAME,
        Path(config.DATA_DIR) / "raw" / PROXY_FILE_NAME
    ]

    proxy_path = None
    for p in possible_proxy_paths:
        if p.exists():
            proxy_path = p
            break

    output_dir = Path(config.PROCESSED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "validation_proxy.json"

    result = {
        "task_id": "T000",
        "status": "completed",
        "proxy_found": False,
        "results": []
    }

    if not proxy_path:
        result["reason"] = "no_proxy_available"
        result["message"] = "No verified proxy dataset found in expected locations."
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return result

    # Load Proxy
    proxy_data = load_json_data(proxy_path)
    if not proxy_data:
        result["reason"] = "no_proxy_available"
        result["message"] = "Proxy file found but contains no data."
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return result

    result["proxy_found"] = True
    result["proxy_path"] = str(proxy_path)

    # We need synthetic data to compare against.
    # Since T001/T002 haven't run yet (T000 has no dependency), we cannot load generated data.
    # The task constraint says: "If no proxy exists, document the limitation".
    # It also implies we compare "between proxy and synthetic".
    # If synthetic data doesn't exist yet, we cannot perform the test.
    # However, T000 is Phase 0, T001/T002 are also Phase 0.
    # If this script runs standalone before generation, we must handle the missing synthetic data.
    # The most robust behavior for a "validation proxy" task that runs before generation is
    # to document that synthetic data is missing.

    synthetic_data_path = Path(config.DATA_DIR) / "training" # Placeholder, might not exist yet
    synthetic_data = []

    # Try to find any generated training data
    if synthetic_data_path.exists():
        for f in synthetic_data_path.glob("*.json"):
            synthetic_data.extend(load_json_data(f))

    if not synthetic_data:
        # If we have a proxy but no synthetic data generated yet, we can't run the test.
        # We document this state.
        result["reason"] = "synthetic_data_not_generated"
        result["message"] = "Proxy found, but no synthetic training data generated yet to compare against."
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        return result

    # Perform KS tests
    ks_results = []
    all_significant = False

    for metric in METRICS_TO_CHECK:
        proxy_vals = extract_metric_values(proxy_data, metric)
        synth_vals = extract_metric_values(synthetic_data, metric)

        if not proxy_vals or not synth_vals:
            ks_results.append({
                "metric": metric,
                "ks_statistic": None,
                "p_value": None,
                "reason": "missing_metric_data"
            })
            continue

        test_result = run_ks_test(synth_vals, proxy_vals, metric)
        ks_results.append(test_result)
        if test_result.get("is_significant_shift", False):
            all_significant = True

    result["ks_tests"] = ks_results
    result["is_valid_shift"] = all_significant

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def main():
    """Entry point for the script."""
    print("Running External Validation Proxy (T000)...")
    try:
        result = run_validation_proxy()
        print(f"Validation Proxy completed. Status: {result['status']}")
        if result.get("reason"):
            print(f"Reason: {result['reason']}")
        if result.get("ks_tests"):
            for test in result["ks_tests"]:
                if test.get("p_value") is not None:
                    print(f"  {test['metric']}: p={test['p_value']:.4f}, shift={test.get('is_significant_shift')}")
    except Exception as e:
        print(f"Error during validation proxy: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
