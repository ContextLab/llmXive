import gc
import logging
import os
import sys
import tracemalloc
import json
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evaluator import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.report_generator import run_full_report_aggregation
from code.results_writer import write_final_report
from code.config import RESULTS_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def get_peak_memory_mb():
    """Get peak memory usage in MB using tracemalloc."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def select_smoke_datasets(spectrum_report_path: Path) -> list:
    """
    Select exactly 3 datasets from the spectrum report:
    one with N < 1k, one with 1k <= N < 10k, one with N >= 10k.
    """
    if not spectrum_report_path.exists():
        raise FileNotFoundError(f"Spectrum report not found at {spectrum_report_path}")

    with open(spectrum_report_path, 'r') as f:
        report = json.load(f)

    datasets = report.get('selected_datasets', [])
    if not datasets:
        raise ValueError("No datasets found in spectrum report")

    bins = {
        'small': [],
        'medium': [],
        'large': []
    }

    for ds in datasets:
        n_samples = ds.get('n_samples', 0)
        if n_samples < 1000:
            bins['small'].append(ds)
        elif n_samples < 10000:
            bins['medium'].append(ds)
        else:
            bins['large'].append(ds)

    selected = []
    for key in ['small', 'medium', 'large']:
        if bins[key]:
            selected.append(bins[key][0])
        else:
            logging.warning(f"No dataset found for bin {key}. Skipping.")

    if len(selected) < 3:
        raise ValueError(f"Could not select 3 datasets from spectrum. Only found {len(selected)}.")

    return selected

def run_smoke_test_with_profiling():
    """
    Run the smoke test with memory profiling enabled.
    Logs peak memory usage to results/memory_profile.log.
    """
    # Setup logging
    log_path = setup_logging()
    logging.info("Starting smoke test with memory profiling...")

    # Set seed for reproducibility
    set_seed(42)

    # Start memory tracing
    tracemalloc.start()

    try:
        # 1. Load spectrum report and select datasets
        spectrum_report_path = DATA_RAW_DIR / "spectrum_report.json"
        selected_datasets = select_smoke_datasets(spectrum_report_path)
        logging.info(f"Selected {len(selected_datasets)} datasets for smoke test.")
        for ds in selected_datasets:
            logging.info(f"  - Dataset ID: {ds['id']}, Name: {ds['name']}, N: {ds['n_samples']}")

        # 2. Run evaluation loop for selected datasets
        # We will manually iterate to track memory per dataset
        all_raw_results = []
        dataset_properties = []

        for ds_info in selected_datasets:
            dataset_id = ds_info['id']
            logging.info(f"Processing dataset {dataset_id}...")

            # Check memory before processing
            gc.collect()
            current_mem = get_peak_memory_mb()
            logging.info(f"  Memory before processing: {current_mem:.2f} MB")

            # Load dataset
            try:
                X, y, ds_name = load_datasets([dataset_id])
                if not X or not y:
                    logging.warning(f"Failed to load dataset {dataset_id}. Skipping.")
                    continue
                X, y = X[0], y[0]
            except Exception as e:
                logging.error(f"Error loading dataset {dataset_id}: {e}")
                continue

            dataset_properties.append({
                'dataset_id': dataset_id,
                'name': ds_name,
                'n_samples': X.shape[0],
                'n_features': X.shape[1]
            })

            # Preprocess
            X_processed, y_processed = preprocess_data(X, y)

            # Evaluate
            raw_results = run_repeated_stratified_cv(X_processed, y_processed, dataset_id, ds_name)
            all_raw_results.extend(raw_results)

            # Check memory after processing
            current_mem = get_peak_memory_mb()
            logging.info(f"  Memory after processing: {current_mem:.2f} MB")

        if not all_raw_results:
            raise RuntimeError("No results generated from smoke test.")

        # 3. Write raw evaluations
        from code.results_writer import write_raw_evaluations
        import pandas as pd
        df_raw = pd.DataFrame(all_raw_results)
        write_raw_evaluations(df_raw)
        logging.info("Raw evaluations written.")

        # 4. Run analysis
        logging.info("Running analysis...")
        stability_metrics, correlation_results, permutation_results = run_full_analysis()

        # 5. Write analysis results
        from code.results_writer import write_stability_metrics, write_correlation_results, write_permutation_results
        write_stability_metrics(stability_metrics)
        write_correlation_results(correlation_results)
        write_permutation_results(permutation_results)
        logging.info("Analysis results written.")

        # 6. Generate report
        logging.info("Generating final report...")
        report_data = run_full_report_aggregation()
        write_final_report(report_data)
        logging.info("Final report generated.")

        # 7. Record final peak memory
        final_peak = get_peak_memory_mb()
        logging.info(f"Final peak memory usage: {final_peak:.2f} MB")

        # 8. Write memory profile log
        log_file_path = RESULTS_DIR / "memory_profile.log"
        with open(log_file_path, 'w') as f:
            f.write(f"Smoke Test Memory Profile\n")
            f.write(f"=========================\n")
            f.write(f"Datasets processed: {len(selected_datasets)}\n")
            for ds in selected_datasets:
                f.write(f"  - ID: {ds['id']}, Name: {ds['name']}, N: {ds['n_samples']}\n")
            f.write(f"Peak RSS Memory: {final_peak:.2f} MB\n")
            f.write(f"Status: {'PASS' if final_peak < 6000 else 'WARNING: Exceeded 6GB limit'}\n")
            f.write(f"\nNote: Peak memory measured using tracemalloc.\n")

        logging.info(f"Memory profile log written to {log_file_path}")

    finally:
        tracemalloc.stop()
        gc.collect()

    return True

def main():
    """Entry point for the script."""
    success = run_smoke_test_with_profiling()
    if success:
        print("Smoke test with profiling completed successfully.")
        sys.exit(0)
    else:
        print("Smoke test with profiling failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()