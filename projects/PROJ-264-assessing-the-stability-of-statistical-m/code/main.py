"""
Main entry point for the stability assessment pipeline.
Orchestrates data loading, evaluation, and result writing.
"""
import logging
import sys
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils import setup_logging, set_seed
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.evaluator import run_repeated_stratified_cv
from code.results_writer import write_raw_evaluations

logger = logging.getLogger(__name__)

def main():
    """
    Execute the full pipeline:
    1. Load datasets
    2. Preprocess
    3. Run repeated stratified CV
    4. Write raw results to results/raw_evaluations.csv
    """
    setup_logging()
    set_seed(42)
    
    logger.info("Starting the stability assessment pipeline.")
    
    # 1. Load datasets
    # This returns a list of (dataset_id, X, y) tuples
    # We assume T005 has populated data/raw/ and this function loads them
    try:
        datasets = load_datasets()
        if not datasets:
            logger.error("No datasets loaded. Exiting.")
            return
        logger.info(f"Loaded {len(datasets)} datasets.")
    except Exception as e:
        logger.error(f"Failed to load datasets: {e}")
        return

    all_results = []

    # 2. Process and Evaluate each dataset
    for dataset_id, X, y in datasets:
        logger.info(f"Processing dataset ID: {dataset_id}")
        
        try:
            # Preprocess
            X_processed, y_processed, feature_names = preprocess_data(X, y)
            
            # Run Evaluation
            # run_repeated_stratified_cv returns a list of result dicts
            results = run_repeated_stratified_cv(
                dataset_id=dataset_id,
                X=X_processed,
                y=y_processed,
                models=["LogisticRegression", "RandomForest", "LinearSVM"]
            )
            
            all_results.extend(results)
            logger.info(f"Completed evaluation for dataset {dataset_id}. "
                        f"Generated {len(results)} records.")
            
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}", exc_info=True)
            continue

    # 3. Write raw results
    if all_results:
        write_raw_evaluations(all_results)
        logger.info("Pipeline completed successfully. Results written to results/raw_evaluations.csv")
    else:
        logger.warning("No results generated. Writing empty CSV.")
        write_raw_evaluations([])

if __name__ == "__main__":
    main()
