"""
Smoke test script for T050.
Executes the full pipeline on exactly 3 datasets (one from each size bin)
and verifies all expected output files are generated.
"""
import logging
import os
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import set_seed, setup_logging
from code.data_loader import load_datasets
from code.evalutor import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.report_generator import run_full_report_aggregation
from code.results_writer import write_final_report
from code.config import RESULTS_DIR, RAW_EVALUATIONS_FILE, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, PERMUTATION_RESULTS_FILE, FINAL_REPORT_FILE

# Setup logging
logger = setup_logging("smoke_test")
set_seed(42)

def select_smoke_datasets(spectrum_report_path: Path):
    """
    Selects 3 datasets from the spectrum report:
    one with N < 1k, one with 1k <= N <= 10k, one with N > 10k.
    """
    if not spectrum_report_path.exists():
        raise FileNotFoundError(f"Spectrum report not found at {spectrum_report_path}. Run T005 first.")
    
    with open(spectrum_report_path, 'r') as f:
        data = json.load(f)
    
    datasets = data.get('selected_datasets', [])
    if not datasets:
        raise ValueError("No datasets found in spectrum report.")
    
    bins = {
        'small': [],      # N < 1000
        'medium': [],     # 1000 <= N <= 10000
        'large': []       # N > 10000
    }
    
    for ds in datasets:
        n_samples = ds.get('n_samples', 0)
        if n_samples < 1000:
            bins['small'].append(ds)
        elif n_samples <= 10000:
            bins['medium'].append(ds)
        else:
            bins['large'].append(ds)
    
    selected = []
    if bins['small']:
        selected.append(bins['small'][0])
    else:
        logger.warning("No small dataset found (<1k). Skipping small bin.")
    
    if bins['medium']:
        selected.append(bins['medium'][0])
    else:
        logger.warning("No medium dataset found (1k-10k). Skipping medium bin.")
    
    if bins['large']:
        selected.append(bins['large'][0])
    else:
        logger.warning("No large dataset found (>10k). Skipping large bin.")
    
    if len(selected) < 3:
        logger.error(f"Could not select 3 datasets from spectrum. Found: {len(selected)}")
        raise RuntimeError("Insufficient datasets in spectrum to run smoke test across all bins.")
    
    return selected

def verify_outputs():
    """Verifies that all expected output files exist and are non-empty."""
    required_files = [
        RESULTS_DIR / RAW_EVALUATIONS_FILE,
        RESULTS_DIR / STABILITY_METRICS_FILE,
        RESULTS_DIR / CORRELATION_RESULTS_FILE,
        RESULTS_DIR / PERMUTATION_RESULTS_FILE,
        RESULTS_DIR / FINAL_REPORT_FILE
    ]
    
    all_valid = True
    for f_path in required_files:
        if not f_path.exists():
            logger.error(f"Missing output file: {f_path}")
            all_valid = False
        elif f_path.stat().st_size == 0:
            logger.error(f"Output file is empty: {f_path}")
            all_valid = False
        else:
            logger.info(f"Verified: {f_path} ({f_path.stat().st_size} bytes)")
    
    return all_valid

def main():
    logger.info("Starting Smoke Test (T050)...")
    
    # 1. Load Spectrum Report and Select Datasets
    spectrum_path = Path(project_root) / "data" / "spectrum_report.json"
    selected_datasets = select_smoke_datasets(spectrum_path)
    logger.info(f"Selected {len(selected_datasets)} datasets for smoke test:")
    for ds in selected_datasets:
        logger.info(f"  - ID: {ds['id']}, Name: {ds['name']}, N: {ds['n_samples']}")
    
    # 2. Run Data Loading (Subset)
    # We pass the selected dataset IDs to load_datasets to fetch only these
    # Assuming load_datasets accepts a filter or we modify it to handle specific IDs
    # For this script, we assume load_datasets can take a list of IDs or we filter the result.
    # Since T005 generates the full list, we will pass the specific IDs to the loader.
    # Note: The existing load_datasets signature might need to be adapted or we call it
    # with the specific IDs. Let's assume we pass the list of IDs to load_datasets.
    
    dataset_ids = [ds['id'] for ds in selected_datasets]
    logger.info(f"Loading datasets: {dataset_ids}")
    
    # We need to ensure load_datasets can handle a subset. 
    # If it loads all from cache, we filter afterwards. 
    # If it fetches from OpenML, we fetch specific ones.
    # Given T005 logic, it likely fetches based on the spectrum.
    # We will call load_datasets with the specific IDs to ensure we get exactly these.
    # If the existing function doesn't support this, we might need to pass the full list
    # and filter, but the task requires running on exactly 3.
    # Let's assume the loader can take a specific list of IDs.
    
    try:
        datasets = load_datasets(dataset_ids=dataset_ids)
    except TypeError:
        # Fallback if the function doesn't accept dataset_ids directly
        # This implies we might need to load all and filter, but that defeats the purpose
        # of a quick smoke test. We assume the API allows filtering.
        logger.error("load_datasets does not support filtering by ID. Cannot proceed efficiently.")
        return 1

    if not datasets:
        logger.error("No datasets loaded.")
        return 1

    # 3. Run Evaluation (Repeated CV)
    logger.info("Running Repeated Stratified CV...")
    raw_results = run_repeated_stratified_cv(datasets)
    if raw_results.empty:
        logger.error("Evaluation produced no results.")
        return 1
    
    # 4. Run Analysis (Aggregation, Correlation, Permutation)
    logger.info("Running Analysis...")
    run_full_analysis(raw_results)
    
    # 5. Generate Report
    logger.info("Generating Final Report...")
    run_full_report_aggregation()
    write_final_report()
    
    # 6. Verify Outputs
    logger.info("Verifying outputs...")
    if verify_outputs():
        logger.info("Smoke Test PASSED: All outputs generated successfully.")
        return 0
    else:
        logger.error("Smoke Test FAILED: Missing or empty output files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())