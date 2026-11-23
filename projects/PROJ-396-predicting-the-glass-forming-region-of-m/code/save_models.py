import os
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

from model_training import main as training_main
from setup_results_models_directory import main as setup_models_main
from utils import configure_logging

def save_model_artifacts(
    models: Dict[str, Any],
    metrics: Dict[str, Any],
    output_dir: str,
    logger: logging.Logger
) -> Dict[str, str]:
    """
    Save trained model artifacts (pkl) and their corresponding metrics to disk.
    
    Args:
        models: Dictionary mapping model names (e.g., 'random_forest') to trained sklearn estimators.
        metrics: Dictionary mapping model names to their performance metrics (dicts).
        output_dir: Path to the directory where artifacts will be saved.
        logger: Logger instance for recording progress.
        
    Returns:
        Dictionary mapping model names to their saved file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_paths = {}

    for name, model in models.items():
        filename = f"{name}_model.pkl"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            saved_paths[name] = filepath
            logger.info(f"Saved model '{name}' to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save model '{name}': {e}")
            raise

    # Save a summary manifest of the saved models
    manifest_path = os.path.join(output_dir, "models_manifest.json")
    manifest_data = {
        "models": list(models.keys()),
        "metrics_summary": {k: {kk: vv for kk, vv in v.items() if kk in ['accuracy', 'auc_roc']} for k, v in metrics.items()},
        "output_directory": output_dir
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Saved model manifest to {manifest_path}")
    return saved_paths

def main():
    """
    Main entry point for saving model artifacts.
    This script assumes model_training.py has already been run or will be run
    to generate the models and metrics in memory or temporary storage.
    For this implementation, we will re-run the training logic to get the objects,
    then save them, to ensure a standalone executable script as per task requirements.
    """
    logger = configure_logging()
    logger.info("Starting model artifact saving process (T040)...")

    # Ensure the results/models directory exists
    setup_models_main()
    
    # We need to import the training logic to get the actual model objects.
    # Since model_training.py's main() prints results but doesn't return them,
    # we will call the internal training functions directly or re-implement the flow
    # to capture the objects. Given the constraint to extend existing API,
    # we assume the training script (T039) ran and we need to re-run the logic
    # to capture the objects for saving.
    
    # Re-executing the training logic to capture objects
    # Note: In a real pipeline, this would be a pipeline step, but for a standalone script:
    from model_training import (
        ensure_directories, load_validated_data, parse_composition, assign_family,
        create_cross_system_split, create_stratified_split, extract_features,
        train_model, evaluate_model, run_cross_system_validation
    )
    
    try:
        # 1. Load Data
        data_path = "data/processed/computed_descriptors.csv"
        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}. Run T029 first.")
            return

        rows = load_validated_data(data_path)
        logger.info(f"Loaded {len(rows)} samples for training.")

        # 2. Prepare Data
        families = [assign_family(parse_composition(r['composition'])) for r in rows]
        features, labels, family_list = extract_features(rows, families)
        
        if len(features) == 0:
            logger.error("No valid features extracted.")
            return

        # 3. Split Data
        train_X, train_y, test_X, test_y, train_fam, test_fam = create_cross_system_split(
            features, labels, family_list
        )
        
        # Fallback to stratified if cross-system fails (e.g. not enough families)
        if train_X is None or len(train_X) == 0:
            logger.warning("Cross-system split failed or empty. Falling back to stratified.")
            train_X, train_y, test_X, test_y, _, _ = create_stratified_split(features, labels)

        # 4. Train Models
        models = {}
        metrics = {}

        # Train Random Forest
        rf_model = train_model(train_X, train_y, model_type="random_forest")
        models['random_forest'] = rf_model
        rf_metrics = evaluate_model(rf_model, test_X, test_y)
        metrics['random_forest'] = rf_metrics
        logger.info(f"Random Forest metrics: {rf_metrics}")

        # Train Gradient Boosting
        gb_model = train_model(train_X, train_y, model_type="gradient_boosting")
        models['gradient_boosting'] = gb_model
        gb_metrics = evaluate_model(gb_model, test_X, test_y)
        metrics['gradient_boosting'] = gb_metrics
        logger.info(f"Gradient Boosting metrics: {gb_metrics}")

        # 5. Save Artifacts
        output_dir = "results/models"
        saved = save_model_artifacts(models, metrics, output_dir, logger)
        
        logger.info(f"Successfully saved {len(saved)} model artifacts to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error during model saving process: {e}")
        raise

if __name__ == "__main__":
    main()