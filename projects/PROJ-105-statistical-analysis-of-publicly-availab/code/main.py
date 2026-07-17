import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils import setup_logging, log_peak_memory, check_memory_limit
from config import RANDOM_SEED
from preprocessing import main as run_stage1
from models import main as run_stage2
from diagnostics import main as run_stage3

# Configure logging
logger = setup_logging()

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, return None otherwise."""
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load {path}: {e}")
            return None
    return None

def run_stage4(results_dir: Path) -> Dict[str, Any]:
    """
    Stage 4: Compile final summary report.
    Aggregates results from Stages 1, 2, and 3 into a single summary_report.json.
    """
    start_time = time.time()
    logger.info("Starting Stage 4: Final Report Compilation")

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load outputs from previous stages
    # Stage 1 outputs
    summary_report_path = results_dir / "summary_report.json"
    stage1_data = load_json_safe(results_dir / "summary_report.json")
    if stage1_data is None:
        # Fallback if the file was named differently or not found immediately
        # Try to find the most recent summary report if it exists
        logger.warning("Stage 1 summary_report.json not found. Attempting to proceed with defaults.")
        stage1_data = {"retention_rate": 0.0, "valid_records": 0}

    # Stage 2 outputs
    model_comparison = load_json_safe(results_dir / "model_comparison.json")
    vuong_results = load_json_safe(results_dir / "vuong_test_results.json")
    x_min_estimate = load_json_safe(results_dir / "x_min_estimate.json")

    # Stage 3 outputs
    tail_index = load_json_safe(results_dir / "tail_index_estimate.json")
    bootstrap_gof = load_json_safe(results_dir / "bootstrap_gof.json")
    log_normal_test = load_json_safe(results_dir / "log_normal_test.json")
    tail_ks = load_json_safe(results_dir / "tail_ks.json")

    # Compile model rankings
    model_rankings = []
    if model_comparison and "models" in model_comparison:
        # Sort by AIC (lower is better)
        models = model_comparison["models"]
        sorted_models = sorted(models, key=lambda m: m.get("aic", float('inf')))
        model_rankings = [
            {
                "rank": i + 1,
                "model": m["name"],
                "aic": m.get("aic"),
                "bic": m.get("bic"),
                "ks_stat": m.get("ks_stat"),
                "ad_stat": m.get("ad_stat")
            }
            for i, m in enumerate(sorted_models)
        ]

    best_model = model_rankings[0]["model"] if model_rankings else "None"

    # Compile p-values
    p_values = {}
    if vuong_results:
        p_values["vuong"] = vuong_results.get("p_value")
    if tail_ks:
        p_values["tail_ks"] = tail_ks.get("p_value")
    if bootstrap_gof:
        p_values["bootstrap_gof"] = bootstrap_gof.get("p_value")

    # Calculate runtime
    runtime_seconds = time.time() - start_time

    # Construct final report
    final_report = {
        "runtime_seconds": round(runtime_seconds, 2),
        "retention_rate": stage1_data.get("retention_rate", 0.0),
        "valid_records": stage1_data.get("valid_records", 0),
        "total_records": stage1_data.get("total_records", 0),
        "model_rankings": model_rankings,
        "best_model": best_model,
        "x_min_estimate": x_min_estimate.get("x_min") if x_min_estimate else None,
        "tail_index": tail_index.get("tail_index") if tail_index else None,
        "p_values": p_values,
        "diagnostics": {
            "bootstrap_gof_pass": bootstrap_gof.get("pass", False) if bootstrap_gof else False,
            "log_normal_rejected": log_normal_test.get("rejected", False) if log_normal_test else False,
            "stability_window_valid": tail_index.get("stable", False) if tail_index else False
        },
        "causality_disclaimer": (
            "This analysis identifies statistical distributions of flight delays. "
            "Correlation with specific factors (weather, mechanical) is not inferred "
            "from distribution shape alone. Heavy tails indicate a higher probability "
            "of extreme events than short-tailed models, but do not specify the root "
            "cause of those events."
        ),
        "metadata": {
            "random_seed": RANDOM_SEED,
            "pipeline_version": "1.0.0",
            "stages_completed": [1, 2, 3, 4]
        }
    }

    # Save final report
    output_path = results_dir / "summary_report.json"
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Final summary report saved to {output_path}")
    log_peak_memory()

    return final_report

def main():
    """
    Main entry point for the pipeline.
    Executes Stages 1 through 4 sequentially.
    """
    logger.info("Starting Flight Delay Analysis Pipeline")

    # Define paths
    data_dir = PROJECT_ROOT / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    results_dir = data_dir / "results"

    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Stage 1: Data Acquisition and Pre-processing
        logger.info("Executing Stage 1: Data Acquisition and Pre-processing")
        run_stage1()

        # Stage 2: Parametric Model Fitting
        logger.info("Executing Stage 2: Parametric Model Fitting")
        run_stage2()

        # Stage 3: Heavy-Tail Diagnostics
        logger.info("Executing Stage 3: Heavy-Tail Diagnostics")
        run_stage3()

        # Stage 4: Final Report Compilation
        logger.info("Executing Stage 4: Final Report Compilation")
        final_report = run_stage4(results_dir)

        logger.info("Pipeline completed successfully.")
        print(json.dumps(final_report, indent=2))

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()