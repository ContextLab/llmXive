import gc
import logging
import os
import sys
import tracemalloc
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evaluator import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.results_writer import write_final_report
from code.config import RESULTS_DIR, DATA_DIR, LOGS_DIR

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logging("smoke_test_profiling.log")

def get_peak_memory_mb():
    """Get current peak memory usage in MB using tracemalloc."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def select_smoke_datasets():
    """
    Select exactly 3 datasets from the cached spectrum report:
    1. One with N < 1000
    2. One with 1000 <= N <= 10000
    3. One with N > 10000
    """
    spectrum_path = DATA_DIR / "spectrum_report.json"
    if not spectrum_path.exists():
        raise FileNotFoundError(f"Spectrum report not found at {spectrum_path}. Run T005 first.")

    with open(spectrum_path, 'r') as f:
        data = json.load(f)

    candidates = data.get("selected_datasets", [])
    if not candidates:
        raise ValueError("No datasets found in spectrum report.")

    small = []
    medium = []
    large = []

    for ds in candidates:
        n_samples = ds.get("n_samples", 0)
        if n_samples < 1000:
            small.append(ds)
        elif 1000 <= n_samples <= 10000:
            medium.append(ds)
        else:
            large.append(ds)

    if not small or not medium or not large:
        raise ValueError(
            f"Insufficient dataset diversity in cache. "
            f"Small (<1k): {len(small)}, Medium (1k-10k): {len(medium)}, Large (>10k): {len(large)}. "
            "Re-run T005 to regenerate the spectrum report."
        )

    # Select one from each bin
    selected = [small[0], medium[0], large[0]]
    logger.info(f"Selected smoke test datasets: {[d['dataset_id'] for d in selected]}")
    return selected

def run_smoke_test_with_profiling():
    """
    Execute the full pipeline on the selected 3 datasets with memory profiling.
    Logs peak memory usage to results/memory_profile.log.
    """
    set_seed(42)
    tracemalloc.start()

    peak_memory_log = []
    dataset_ids = []

    try:
        # 1. Load and select datasets
        smoke_datasets = select_smoke_datasets()
        logger.info("Starting smoke test with profiling...")

        # 2. Process each dataset sequentially
        all_eval_results = []
        for ds_info in smoke_datasets:
            ds_id = ds_info["dataset_id"]
            dataset_ids.append(ds_id)
            logger.info(f"Processing dataset {ds_id}...")

            # Snapshot before processing
            current, peak = tracemalloc.get_traced_memory()
            logger.info(f"  Memory before load: {peak / (1024*1024):.2f} MB")

            # Load
            try:
                X, y, name = load_datasets([ds_id])
                if not X or not y:
                    logger.warning(f"Dataset {ds_id} failed to load or has no data. Skipping.")
                    continue
                X, y = X[0], y[0] # unwrap list from loader
            except Exception as e:
                logger.error(f"Failed to load dataset {ds_id}: {e}")
                continue

            # Preprocess
            X_processed, y_processed = preprocess_data(X, y)

            # Evaluate
            results = run_repeated_stratified_cv(
                X_processed, y_processed,
                model_names=["LogisticRegression", "RandomForest", "LinearSVM"],
                dataset_id=ds_id,
                n_splits=10, n_repeats=10
            )
            all_eval_results.extend(results)

            # Snapshot after processing
            current, peak = tracemalloc.get_traced_memory()
            peak_mb = peak / (1024 * 1024)
            logger.info(f"  Memory after processing {ds_id}: {peak_mb:.2f} MB")
            peak_memory_log.append({
                "dataset_id": ds_id,
                "peak_memory_mb": peak_mb
            })

            # Explicit cleanup
            del X, y, X_processed, y_processed, results
            gc.collect()

        # 3. Write raw evaluations
        from code.results_writer import write_raw_evaluations
        write_raw_evaluations(all_eval_results)

        # 4. Run Analysis
        logger.info("Running analysis...")
        stability_metrics, correlation_results, permutation_results = run_full_analysis()

        # 5. Write Analysis Results
        from code.results_writer import write_stability_metrics, write_correlation_results, write_permutation_results
        write_stability_metrics(stability_metrics)
        write_correlation_results(correlation_results)
        write_permutation_results(permutation_results)

        # 6. Generate Report
        logger.info("Generating final report...")
        write_final_report(stability_metrics, correlation_results, permutation_results)

        # Final Memory Check
        current, peak = tracemalloc.get_traced_memory()
        final_peak_mb = peak / (1024 * 1024)
        logger.info(f"Final Peak Memory: {final_peak_mb:.2f} MB")
        peak_memory_log.append({
            "dataset_id": "TOTAL",
            "peak_memory_mb": final_peak_mb
        })

        # Write Profile Log
        profile_log_path = RESULTS_DIR / "memory_profile.log"
        with open(profile_log_path, 'w') as f:
            f.write("Memory Profiling Report for Smoke Test (3 Datasets)\n")
            f.write("=" * 60 + "\n")
            for entry in peak_memory_log:
                f.write(f"Dataset ID: {entry['dataset_id']}, Peak Memory (MB): {entry['peak_memory_mb']:.2f}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Overall Peak Memory: {final_peak_mb:.2f} MB\n")
            if final_peak_mb < 6000:
                f.write("STATUS: PASS (Under 6GB limit)\n")
            else:
                f.write("STATUS: FAIL (Exceeded 6GB limit)\n")

        logger.info(f"Memory profile log written to {profile_log_path}")
        return True

    except Exception as e:
        logger.error(f"Smoke test failed: {e}", exc_info=True)
        raise
    finally:
        tracemalloc.stop()

def main():
    """Entry point for the script."""
    success = run_smoke_test_with_profiling()
    if success:
        print("Smoke test with profiling completed successfully.")
        sys.exit(0)
    else:
        print("Smoke test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()