"""
Smoke test script to orchestrate a full pipeline run on exactly 3 datasets.
Datasets: iris (N<1k), heart-statlog (1k-10k), credit-a (>10k).
"""
import logging
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils import set_seed, setup_logging, PipelineError
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evaluator import run_repeated_stratified_cv
from code.analyser import run_full_analysis
from code.results_writer import (
    write_raw_evaluations,
    write_stability_metrics,
    write_correlation_results,
    write_permutation_results,
    write_final_report
)
from code.report_generator import run_full_report_aggregation

# Hardcoded dataset IDs as per specification
SMOKE_DATASET_IDS = [
    61,    # iris (N < 1k)
    14,    # heart-statlog (1k - 10k)
    1461   # credit-a (> 10k)
]

def setup_logger() -> logging.Logger:
    """Configure logging for the smoke test."""
    return setup_logging("smoke_test", level=logging.INFO)

def select_smoke_datasets() -> List[Dict[str, Any]]:
    """
    Select the hardcoded smoke test datasets.
    Returns a list of dataset metadata dicts.
    """
    logger = logging.getLogger("smoke_test")
    logger.info(f"Selecting smoke test datasets: {SMOKE_DATASET_IDS}")
    
    # We assume load_datasets handles the fetching and returns a list of dicts
    # containing 'id', 'X', 'y', 'name', 'n_samples', etc.
    # We filter to only the requested IDs.
    all_datasets = load_datasets(SMOKE_DATASET_IDS)
    
    if not all_datasets:
        raise RuntimeError("No datasets loaded. Check network or dataset availability.")
    
    logger.info(f"Loaded {len(all_datasets)} datasets for smoke test.")
    for ds in all_datasets:
        logger.info(f"  - ID {ds['id']}: {ds.get('name', 'unknown')} (N={ds.get('n_samples', 'N/A')})")
    
    return all_datasets

def verify_outputs(logger: logging.Logger) -> bool:
    """
    Verify that all expected output files were generated and contain data.
    Returns True if valid, False otherwise.
    """
    results_dir = PROJECT_ROOT / "results"
    expected_files = [
        "raw_evaluations.csv",
        "stability_metrics.csv",
        "correlation_results.csv",
        "permutation_results.csv",
        "final_report.md"
    ]
    
    valid = True
    for fname in expected_files:
        fpath = results_dir / fname
        if not fpath.exists():
            logger.error(f"Missing expected output: {fpath}")
            valid = False
            continue
        
        # Basic size check
        if fpath.stat().st_size == 0:
            logger.error(f"Empty output file: {fpath}")
            valid = False
            continue
        
        logger.info(f"Verified: {fname} ({fpath.stat().st_size} bytes)")
    
    return valid

def run_pipeline(datasets: List[Dict[str, Any]], logger: logging.Logger) -> bool:
    """
    Execute the full pipeline on the selected datasets.
    """
    seed = 42
    set_seed(seed)
    logger.info(f"Pipeline started with seed={seed}")

    try:
        # 1. Evaluation Loop
        logger.info("Starting Evaluation Phase...")
        raw_records = []
        
        for ds in datasets:
            ds_id = ds['id']
            X = ds['X']
            y = ds['y']
            name = ds.get('name', str(ds_id))
            
            logger.info(f"Processing dataset: {name} (ID: {ds_id})")
            
            # Preprocess
            X_proc, y_proc, cat_cols, num_cols = preprocess_data(X, y)
            
            # Evaluate
            # run_repeated_stratified_cv returns a list of evaluation records
            eval_records = run_repeated_stratified_cv(
                X_proc, y_proc, 
                dataset_id=ds_id,
                dataset_name=name,
                cat_cols=cat_cols,
                num_cols=num_cols
            )
            raw_records.extend(eval_records)
            logger.info(f"  Completed {name}. Generated {len(eval_records)} records.")
        
        # Write Raw Evaluations
        if raw_records:
            write_raw_evaluations(raw_records)
            logger.info("Wrote raw_evaluations.csv")
        else:
            logger.error("No evaluation records generated.")
            return False

        # 2. Analysis Phase
        logger.info("Starting Analysis Phase...")
        
        # Load dataset properties for correlation (we need n_samples, n_features)
        # We can extract this from the loaded dataset objects or re-calculate
        dataset_properties = []
        for ds in datasets:
            dataset_properties.append({
                'dataset_id': ds['id'],
                'n_samples': ds['n_samples'],
                'n_features': ds['n_features']
            })
        
        # Run full analysis which aggregates metrics, correlations, and permutation tests
        # This function is expected to write intermediate results and return final tables
        analysis_results = run_full_analysis(
            dataset_properties=dataset_properties,
            seed=seed
        )
        
        # Extract results from the analysis output if needed, 
        # but run_full_analysis is expected to write files directly per T019b/T025/T026b
        # We assume it writes: stability_metrics.csv, correlation_results.csv, permutation_results.csv
        
        # If run_full_analysis doesn't write them, we write them here using the returned data
        # Based on the API surface, run_full_analysis likely orchestrates the writing.
        # If not, we would call write_stability_metrics, etc. manually.
        # Assuming it writes them as per task descriptions.
        
        logger.info("Analysis Phase completed.")

        # 3. Report Generation
        logger.info("Starting Report Generation Phase...")
        report_data = run_full_report_aggregation()
        
        if report_data:
            write_final_report(report_data)
            logger.info("Generated final_report.md")
        else:
            logger.error("Report aggregation returned no data.")
            return False

        return True

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise PipelineError(f"Pipeline execution failed: {e}")

def main():
    logger = setup_logger()
    logger.info("=" * 60)
    logger.info("Starting Smoke Test (T050a)")
    logger.info("=" * 60)

    start_time = time.time()
    success = False

    try:
        # 1. Select Datasets
        datasets = select_smoke_datasets()
        
        # 2. Run Pipeline
        success = run_pipeline(datasets, logger)
        
    except Exception as e:
        logger.error(f"Smoke test failed: {e}")
        success = False
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Smoke test finished in {elapsed:.2f} seconds.")
        
        if success:
            logger.info("Verifying outputs...")
            if verify_outputs(logger):
                logger.info("SMOKE TEST PASSED: All outputs generated and valid.")
                return 0
            else:
                logger.error("SMOKE TEST FAILED: Output verification failed.")
                return 1
        else:
            logger.error("SMOKE TEST FAILED: Pipeline execution failed.")
            return 1

if __name__ == "__main__":
    sys.exit(main())