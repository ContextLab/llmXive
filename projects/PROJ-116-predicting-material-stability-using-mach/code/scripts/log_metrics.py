"""
Standalone script to demonstrate and validate T017 logging functionality.
This script simulates the logging of dataset and training metrics to ensure
the logging infrastructure is correctly configured and produces real artifacts.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import OUTPUTS_LOGS_DIR
from utils.logging import setup_logger
from utils.logging_metrics import (
    log_dataset_metrics,
    log_training_metrics,
    log_feature_engineering_summary
)


def main():
    """
    Execute logging operations to verify T017 compliance.
    """
    # Ensure output directory exists
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Setup logger
    logger = setup_logger("T017_Validation")
    logger.info("Starting T017 logging validation...")

    # 1. Log Dataset Metrics
    # Simulating a dataset load from T012/T013
    dataset_size = 15000  # Simulated count from OQMD filter
    feature_count = 145   # Simulated Magpie features count
    log_dataset_metrics(
        logger_name="T017_Validation",
        dataset_size=dataset_size,
        feature_count=feature_count,
        source="OQMD_Filtered",
        filter_criteria="Li-rich Rock-Salt"
    )
    logger.info(f"Logged dataset metrics: {dataset_size} entries, {feature_count} features")

    # 2. Log Feature Engineering Summary
    # Simulating T013 feature engineering process
    features_added = [
        "ElementProperty_mean", "ElementProperty_std", "ElementProperty_range",
        "ElementProperty_min", "ElementProperty_max",
        "ValenceElectronConcentration", "AtomicWeight", "MeltingPoint"
    ]
    log_feature_engineering_summary(
        logger_name="T017_Validation",
        input_size=dataset_size,
        output_size=dataset_size,
        features_added=features_added,
        skipped_entries=0,
        imputed_entries=12
    )
    logger.info(f"Logged FE summary: {len(features_added)} features added, 12 imputed")

    # 3. Log Training Metrics
    # Simulating T014 baseline model training
    training_metrics = {
        "MAE": 0.1245,
        "RMSE": 0.1892,
        "R2": 0.8734,
        "Validation_MAE": 0.1310
    }
    hyperparameters = {
        "n_estimators": 200,
        "learning_rate": 0.1,
        "max_depth": 5,
        "subsample": 0.8
    }
    log_training_metrics(
        logger_name="T017_Validation",
        model_name="Baseline_GradientBoosting",
        metrics=training_metrics,
        hyperparameters=hyperparameters
    )
    logger.info(f"Logged training metrics for {training_metrics['MAE']:.4f} MAE")

    # Verify files were created
    expected_files = [
        "dataset_metrics.json",
        "fe_summary.json",
        "training_metrics.json"
    ]

    all_found = True
    for fname in expected_files:
        fpath = OUTPUTS_LOGS_DIR / fname
        if fpath.exists():
            logger.info(f"Verified artifact created: {fpath}")
        else:
            logger.error(f"MISSING artifact: {fpath}")
            all_found = False

    if all_found:
        logger.info("T017 Validation SUCCESS: All logging artifacts created.")
        return 0
    else:
        logger.error("T017 Validation FAILED: Missing artifacts.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
