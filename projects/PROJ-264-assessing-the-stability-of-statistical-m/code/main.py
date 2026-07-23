"""
Main entry point for the stability assessment pipeline.
Orchestrates data loading, evaluation, and result writing.
"""
import logging
import sys
from pathlib import Path

from code.utils import setup_logging, set_seed
from code.data_loader import load_datasets
from code.preprocessor import preprocess_data
from code.config import DATASET_IDS, MODEL_NAMES, N_SPLITS, N_REPEATS, RANDOM_SEED, RAW_EVALUATIONS_PATH
from code.results_writer import write_raw_evaluations
from code.evaluator import run_repeated_stratified_cv_corrected

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    set_seed(RANDOM_SEED)

    logger.info("Starting Stability Assessment Pipeline")

    # Load datasets
    logger.info(f"Loading {len(DATASET_IDS)} datasets...")
    datasets = load_datasets(DATASET_IDS)

    if not datasets:
        logger.error("No datasets loaded. Exiting.")
        sys.exit(1)

    all_results = []

    # Define models
    models = [
        ("LogisticRegression", None, {}),
        ("RandomForest", None, {}),
        ("LinearSVM", None, {})
    ]

    # Process each dataset
    for dataset_info in datasets:
        dataset_id = dataset_info["id"]
        X = dataset_info["X"]
        y = dataset_info["y"]
        name = dataset_info["name"]

        logger.info(f"Processing dataset {dataset_id} ({name}) with shape {X.shape}")

        try:
            # Run evaluation
            results = run_repeated_stratified_cv_corrected(
                dataset_id=dataset_id,
                X=X,
                y=y,
                models=models,
                n_splits=N_SPLITS,
                n_repeats=N_REPEATS,
                random_seed=RANDOM_SEED
            )
            all_results.extend(results)
            logger.info(f"Completed dataset {dataset_id}. Generated {len(results)} records.")
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_id}: {e}", exc_info=True)
            continue

    if not all_results:
        logger.error("No evaluation results generated. Exiting.")
        sys.exit(1)

    # Write results
    logger.info(f"Writing {len(all_results)} results to {RAW_EVALUATIONS_PATH}...")
    write_raw_evaluations(all_results, str(RAW_EVALUATIONS_PATH))
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
