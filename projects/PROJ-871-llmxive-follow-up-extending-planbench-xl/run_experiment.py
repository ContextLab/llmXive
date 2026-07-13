"""
Main experiment runner for llmXive PlanBench-XL follow-up.

Orchestrates the full pipeline:
1. Load raw PlanBench-XL data
2. Inject synthetic failures and build signature index
3. Run Baseline Agent execution
4. Run Augmented Agent execution
5. Perform statistical analysis
6. Generate final report

Usage:
    python run_experiment.py
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from dataset.loader import download_planbench_xl, main as loader_main
from dataset.injector import inject_failures, save_injected_data, main as injector_main
from dataset.indexer import build_failure_index, save_index, main as indexer_main
from run_baseline import run_baseline_experiment
from run_augmented import run_augmented_experiment
from analysis.log_parser import get_aggregated_counts
from analysis.stats import calculate_statistical_significance
from analysis.report import generate_report


def ensure_directories():
    """Ensure all required data directories exist."""
    dirs = [
        "data/raw",
        "data/derived",
        "data/logs",
        "data/results",
    ]
    for dir_path in dirs:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {full_path}")


def run_pipeline():
    """Execute the full experiment pipeline."""
    print("=" * 60)
    print("llmXive PlanBench-XL Follow-up: Full Experiment Pipeline")
    print("=" * 60)

    # Step 1: Ensure directories
    print("\n[1/6] Setting up directories...")
    ensure_directories()

    # Step 2: Download and prepare data
    print("\n[2/6] Loading PlanBench-XL dataset...")
    raw_data_path = PROJECT_ROOT / "data/raw" / "planbench_xl.jsonl"
    # Check if raw data exists, if not download
    if not raw_data_path.exists():
        print("Raw data not found. Downloading PlanBench-XL...")
        download_planbench_xl(str(raw_data_path))
    else:
        print(f"Raw data found at {raw_data_path}")

    # Step 3: Inject synthetic failures
    print("\n[3/6] Injecting synthetic failures...")
    injected_path = PROJECT_ROOT / "data/derived" / "implicit_failure_subset.jsonl"
    if not injected_path.exists():
        # Run injector to create the subset
        injector_main()
    else:
        print(f"Injected data found at {injected_path}")

    # Step 4: Build failure signature index
    print("\n[4/6] Building failure signature index...")
    index_path = PROJECT_ROOT / "data/derived" / "failure_signatures.json"
    if not index_path.exists():
        # Run indexer to create the index
        indexer_main()
    else:
        print(f"Signature index found at {index_path}")

    # Step 5: Run Baseline Agent
    print("\n[5/6] Running Baseline Agent execution...")
    baseline_log_path = PROJECT_ROOT / "data/logs" / "baseline_execution.jsonl"
    if not baseline_log_path.exists():
        run_baseline_experiment()
    else:
        print(f"Baseline log found at {baseline_log_path}")

    # Step 6: Run Augmented Agent
    print("\n[6/6] Running Augmented Agent execution...")
    augmented_log_path = PROJECT_ROOT / "data/logs" / "augmented_execution.jsonl"
    if not augmented_log_path.exists():
        run_augmented_experiment()
    else:
        print(f"Augmented log found at {augmented_log_path}")

    # Step 7: Statistical Analysis
    print("\n[7/6] Performing statistical analysis...")
    baseline_counts = get_aggregated_counts(str(baseline_log_path))
    augmented_counts = get_aggregated_counts(str(augmented_log_path))

    print(f"Baseline counts: {baseline_counts}")
    print(f"Augmented counts: {augmented_counts}")

    stats_result = calculate_statistical_significance(baseline_counts, augmented_counts)
    print(f"Statistical result: {stats_result}")

    # Step 8: Generate Report
    print("\n[8/6] Generating final report...")
    report_path = PROJECT_ROOT / "data/results" / "final_report.json"

    report_data = {
        "baseline_counts": baseline_counts,
        "augmented_counts": augmented_counts,
        "statistical_analysis": stats_result,
        "timestamp": str(Path(__file__).parent)
    }

    generate_report(report_data, str(report_path))
    print(f"Final report saved to {report_path}")

    print("\n" + "=" * 60)
    print("Experiment pipeline completed successfully!")
    print("=" * 60)

    return report_data


def main():
    """Entry point for the experiment runner."""
    try:
        result = run_pipeline()
        print("\nPipeline completed. Final report:")
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())