"""
Main orchestrator for the EEG Cognitive Load Prediction Pipeline.

This script orchestrates the full pipeline: Data -> Features -> Model -> Report.
It merges outputs from T028 (Model Training), T038 (Permutation Test),
T041 (Baseline Comparison), and T042 (Runtime Profiling) into a single
`results/model_metrics.json` file, checks the R² against the threshold
defined in `pipeline_config.yaml`, and exits with an error if the threshold
is not met.
"""
import argparse
import json
import os
import sys
import traceback
import time
from pathlib import Path

# Config utilities
from config import load_config, get_config_value

# Runtime profiling gate
from utils.runtime_profiler import check_and_halt

# Pipeline step main functions
from models.train import main as train_main
from models.permutation_test import main as perm_main
from models.baseline import main as baseline_main
from utils.runtime_profiler import main as profiler_main
from models.sensitivity import run_sensitivity_analysis

# Expected output files from the individual steps
TRAIN_OUTPUT = "results/train_results.json"
PERM_OUTPUT = "results/permutation_test.json"
BASELINE_OUTPUT = "results/baseline_comparison.json"
PROFILER_OUTPUT = "results/runtime_profile.json"
SENSITIVITY_OUTPUT = "results/sensitivity_report.csv"
FINAL_OUTPUT = "model_metrics.json"

def run_step_if_needed(step_name: str, func, output_path: str):
    """Run a pipeline step if its expected output file does not exist."""
    if not os.path.exists(output_path):
        print(f"[{step_name}] Output not found ({output_path}). Running step...")
        try:
            func()
            if not os.path.exists(output_path):
                print(f"[{step_name}] WARNING: Step completed but output still missing.")
        except Exception as e:
            print(f"[{step_name}] ERROR: Step failed with exception: {e}")
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"[{step_name}] Output already present. Skipping.")

def load_json_safe(path: str):
    """Load a JSON file, returning an empty dict on failure."""
    if not os.path.exists(path):
        print(f"Warning: Expected file {path} not found.")
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {path}: {e}")
        return {}

def aggregate_results(output_dir: str):
    """Merge results from all pipeline components into a single JSON report."""
    results = {
        "pipeline_status": "completed",
        "merged_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "components": {}
    }

    # Load each component's JSON output
    results["components"]["training"] = load_json_safe(TRAIN_OUTPUT)
    results["components"]["permutation_test"] = load_json_safe(PERM_OUTPUT)
    results["components"]["baseline_comparison"] = load_json_safe(BASELINE_OUTPUT)
    results["components"]["runtime_profile"] = load_json_safe(PROFILER_OUTPUT)

    # Sensitivity report is a CSV; we just note its existence
    if os.path.exists(SENSITIVITY_OUTPUT):
        results["components"]["sensitivity_analysis"] = {
            "file": SENSITIVITY_OUTPUT,
            "status": "exists"
        }
    else:
        results["components"]["sensitivity_analysis"] = {
            "status": "missing"
        }

    # Write merged results
    os.makedirs(output_dir, exist_ok=True)
    final_path = os.path.join(output_dir, FINAL_OUTPUT)
    with open(final_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Aggregated results written to {final_path}")
    return final_path

def verify_r2_threshold(merged_path: str, config: dict):
    """Compare the final R² against the threshold defined in the config."""
    # Load merged results
    merged = load_json_safe(merged_path)
    training_res = merged.get("components", {}).get("training", {})
    r2 = training_res.get("r2")
    if r2 is None:
        print("R² value not found in training results; cannot apply threshold gate.")
        return

    # Retrieve threshold; default to 0.0 if not defined
    r2_threshold = config.get("model", {}).get("r2_threshold", 0.0)
    print(f"Final R²: {r2:.4f} | Threshold: {r2_threshold:.4f}")

    if r2 < r2_threshold:
        print("Threshold Gate Failed: R² < threshold")
        sys.exit(1)
    else:
        print("R² meets the required threshold.")

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate the full EEG Cognitive Load Pipeline."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing processed EEG data."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to write output reports."
    )
    args = parser.parse_args()

    # Initial runtime check
    check_and_halt()

    print("Starting Pipeline Orchestration (T030)...")
    print(f"Data directory: {args.data_dir}")
    print(f"Output directory: {args.output_dir}")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Run Training (T028)
    run_step_if_needed("T028-Training", train_main, TRAIN_OUTPUT)
    check_and_halt()

    # 2. Run Permutation Test (T038)
    run_step_if_needed("T038-Permutation", perm_main, PERM_OUTPUT)
    check_and_halt()

    # 3. Run Baseline Comparison (T041)
    run_step_if_needed("T041-Baseline", baseline_main, BASELINE_OUTPUT)
    check_and_halt()

    # 4. Run Runtime Profiler (T042) – may have already run, ensure output exists
    run_step_if_needed("T042-Profiler", profiler_main, PROFILER_OUTPUT)
    check_and_halt()

    # 5. (Optional) Run Sensitivity Analysis (T029)
    # This step is optional for merging, but we trigger it for completeness.
    if not os.path.exists(SENSITIVITY_OUTPUT):
        print("Running sensitivity analysis (T029)...")
        try:
            run_sensitivity_analysis()
        except Exception as e:
            print(f"Sensitivity analysis failed: {e}")
            traceback.print_exc()
            # Continue without failing the whole pipeline

    # 6. Aggregate all results
    merged_path = aggregate_results(args.output_dir)

    # 7. Load pipeline config and enforce R² threshold
    config = load_config()
    verify_r2_threshold(merged_path, config)

    # Final verification
    if os.path.exists(merged_path):
        print("Pipeline completed successfully.")
        print(f"Final merged report: {merged_path}")
        sys.exit(0)
    else:
        print("Pipeline failed to produce the final merged report.")
        sys.exit(1)

if __name__ == "__main__":
    main()
