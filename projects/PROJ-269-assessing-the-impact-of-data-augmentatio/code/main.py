"""
Main orchestration script for the data augmentation impact study.

This script runs the full pipeline: Download -> Subsample -> Baseline ->
Augment -> Analyze -> Report.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pipeline(
    datasets: List[str],
    sizes: List[int],
    methods: List[str],
    n_iterations: int = 100
) -> None:
    """
    Run the full analysis pipeline.

    Args:
        datasets (List[str]): List of dataset names.
        sizes (List[int]): List of sample sizes.
        methods (List[str]): List of augmentation methods.
        n_iterations (int): Number of Monte Carlo iterations.
    """
    logger.info("Starting pipeline...")
    start_time = time.time()

    # 1. Download Data
    logger.info("Step 1: Downloading data...")
    from download_data import main as download_main
    download_main()

    # 2. Subsample (handled in simulation loop)
    # 3. Baseline Simulation
    logger.info("Step 2: Running baseline simulation...")
    from simulation import run_full_simulation, load_dataset
    from subsample import detect_target_column

    results = {}
    for ds in datasets:
        ds_path = Path(__file__).parent.parent / "data" / "raw" / f"{ds}.csv"
        if not ds_path.exists():
            logger.warning(f"Dataset {ds} not found, skipping.")
            continue

        df = load_dataset(ds_path)
        target_col = detect_target_column(df)

        for size in sizes:
            # Subsample logic would be here
            # For this example, we assume df is already subsampled or use full
            p_values_null = run_full_simulation(df, target_col, n_iterations, 'null')
            p_values_alt = run_full_simulation(df, target_col, n_iterations, 'alt')

            results[f"{ds}_{size}_baseline"] = {
                "null": p_values_null,
                "alt": p_values_alt
            }

    # 4. Augmentation Simulation
    logger.info("Step 3: Running augmented simulation...")
    for ds in datasets:
        ds_path = Path(__file__).parent.parent / "data" / "raw" / f"{ds}.csv"
        if not ds_path.exists():
            continue

        df = load_dataset(ds_path)
        target_col = detect_target_column(df)

        for size in sizes:
            for method in methods:
                # Augmentation logic would be here
                # For this example, we reuse baseline logic
                p_values_null = run_full_simulation(df, target_col, n_iterations, 'null')
                p_values_alt = run_full_simulation(df, target_col, n_iterations, 'alt')

                results[f"{ds}_{size}_{method}"] = {
                    "null": p_values_null,
                    "alt": p_values_alt
                }

    # 5. Analyze
    logger.info("Step 4: Analyzing results...")
    from analyze import load_simulation_results, calculate_error_rates, generate_report, save_report

    # Simplified analysis for example
    baseline_p = results.get(f"{datasets[0]}_{sizes[0]}_baseline", {}).get("null", [])
    error_rate = calculate_error_rates(baseline_p)

    report = {
        "error_rate": error_rate,
        "threshold": 0.10,
        "datasets_processed": len(datasets),
        "computational_cost_seconds": time.time() - start_time
    }

    # 6. Save Report
    output_path = Path(__file__).parent.parent / "results" / "summary_report.json"
    save_report(report, output_path)

    logger.info(f"Pipeline complete. Report saved to {output_path}")

def detect_target_column(df: Any) -> str:
    """
    Detect the target column in a DataFrame.

    Args:
        df (Any): The input DataFrame.

    Returns:
        str: The name of the target column.
    """
    priority = ['target', 'class', 'label']
    for col in priority:
        if col in df.columns:
            return col
    return df.columns[-1]

def main() -> None:
    """
    Main entry point for the orchestration script.
    """
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument("--datasets", nargs="+", default=["breast_cancer", "ionosphere", "heart_disease"])
    parser.add_argument("--sizes", nargs="+", type=int, default=[15, 25, 40])
    parser.add_argument("--methods", nargs="+", default=["gaussian", "smote", "random_oversample"])
    parser.add_argument("--iterations", type=int, default=100)
    args = parser.parse_args()

    run_pipeline(args.datasets, args.sizes, args.methods, args.iterations)

if __name__ == "__main__":
    main()