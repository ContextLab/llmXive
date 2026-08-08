"""
T032: Generate final report in data/results/stats_report.json.

Aggregates:
- P-values and BH-adjusted q-values from src/evaluation/stats.py (T029)
- Reconstruction errors from data/results/reconstruction_error.json (T022b)
- Linearity correlation from data/results/linearity_check.json (T030)
"""
import json
import os
from pathlib import Path

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RESULTS_DIR = PROJECT_ROOT / "data" / "results"
REPORT_PATH = RESULTS_DIR / "stats_report.json"

# Paths to dependency outputs
STATS_REPORT_PATH = RESULTS_DIR / "stats_report.json"  # From T029/T031
RECONSTRUCTION_ERROR_PATH = RESULTS_DIR / "reconstruction_error.json"  # From T022b
LINEARITY_CHECK_PATH = RESULTS_DIR / "linearity_check.json"  # From T030

def load_json_safe(path: Path) -> dict:
    """Load JSON if exists, else return empty dict with warning."""
    if not path.exists():
        print(f"⚠️  Warning: Required input file not found: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️  Error decoding JSON from {path}: {e}")
        return {}

def main():
    print("🚀 Generating final stats report (T032)...")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Statistical Results (P-values, BH-adjusted q-values)
    # This comes from T029/T031 which wrote to stats_report.json (or similar)
    # We assume T029/T031 output a structure with 'p_values' and 'q_values'
    stats_data = load_json_safe(STATS_REPORT_PATH)
    
    # Extract relevant stats if they exist in the source file
    # T029/T031 might have written a full report; we extract the core stats here.
    # If T029/T031 wrote to a different key or file, we adapt.
    # Assuming the source file contains 'p_values' and 'q_values' keys.
    p_values = stats_data.get("p_values", {})
    q_values = stats_data.get("q_values", {})
    
    # If the source file was the full report, we might need to restructure.
    # For robustness, if 'p_values' is missing but the file has top-level keys,
    # we assume the file itself is the stats block.
    if not p_values and stats_data:
        # Heuristic: if keys look like strategies, treat as p-values
        if all(isinstance(v, (int, float)) for v in stats_data.values()):
            p_values = stats_data
            q_values = stats_data.get("q_values", {}) # Fallback if q-values separate

    # 2. Load Reconstruction Errors (T022b)
    recon_data = load_json_safe(RECONSTRUCTION_ERROR_PATH)
    reconstruction_errors = recon_data.get("errors", {})
    if not reconstruction_errors and recon_data:
        # If the file is flat, assume it's the error dict
        reconstruction_errors = recon_data

    # 3. Load Linearity Check (T030)
    linearity_data = load_json_safe(LINEARITY_CHECK_PATH)
    linearity_correlation = linearity_data.get("correlation")
    linearity_valid = linearity_data.get("valid", False)
    
    if linearity_correlation is None and linearity_data:
        # Fallback if key is different
        linearity_correlation = linearity_data.get("pearson_r")
        linearity_valid = linearity_data.get("is_valid", False)

    # 4. Assemble Final Report
    final_report = {
        "task_id": "T032",
        "description": "Final aggregated statistical report for US3",
        "statistics": {
            "p_values": p_values,
            "q_values_bh_correct": q_values,
            "methodology": "Benjamini-Hochberg correction applied to paired t-tests/Wilcoxon"
        },
        "reconstruction_error": {
            "metric": "cosine_distance",
            "values": reconstruction_errors,
            "source_task": "T022b"
        },
        "linearity_check": {
            "correlation": linearity_correlation,
            "validity_flag": linearity_valid,
            "threshold": 0.6,
            "source_task": "T030"
        },
        "summary": {
            "total_strategies_evaluated": len(p_values),
            "linearity_holds": linearity_valid if linearity_correlation is not None else None,
            "avg_reconstruction_error": (
                sum(reconstruction_errors.values()) / len(reconstruction_errors)
                if reconstruction_errors else None
            )
        }
    }

    # Write Output
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    print(f"✅ Final report written to: {REPORT_PATH}")
    print(f"   - P-values included: {len(p_values)} comparisons")
    print(f"   - Linearity valid: {linearity_valid}")
    print(f"   - Reconstruction errors: {len(reconstruction_errors)} entries")

if __name__ == "__main__":
    main()