import argparse
import json
import logging
import sys
import os
from pathlib import Path
import pickle

# Import from existing project modules
from train import setup_logging as train_setup_logging, load_features as train_load_features, prepare_data as train_prepare_data, train_and_evaluate as train_run_training, run_cross_validation as train_run_cv, save_results as train_save_results
from evaluate import setup_logging as eval_setup_logging, load_features as eval_load_features, load_model as eval_load_model, calculate_metrics as eval_calc_metrics, calculate_baseline_mae as eval_calc_baseline, perform_permutation_test as eval_perm_test, evaluate_model as eval_run_eval, save_results as eval_save_results
from null_baseline import calculate_mean_baseline_metrics as nb_calc_baseline, load_rf_results as nb_load_rf, compare_and_save_results as nb_compare_save

def ensure_directories(results_dir: Path):
    """Ensure required output directories exist."""
    results_dir.mkdir(parents=True, exist_ok=True)
    # Ensure parent data/processed exists if we need to read features (though path is absolute usually)
    results_dir.parent.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Integrate training, evaluation, and null baseline comparison.")
    parser.add_argument("--features-path", type=str, default="data/processed/features.json",
                        help="Path to the processed features JSON file.")
    parser.add_argument("--results-dir", type=str, default="results",
                        help="Directory to save model and results artifacts.")
    parser.add_argument("--n-estimators", type=int, default=100,
                        help="Number of estimators for Random Forest.")
    parser.add_argument("--n-permutations", type=int, default=1000,
                        help="Number of permutations for the permutation test.")
    parser.add_argument("--n-splits", type=int, default=5,
                        help="Number of folds for cross-validation.")
    parser.add_argument("--random-state", type=int, default=42,
                        help="Random state for reproducibility.")
    parser.add_argument("--test-size", type=float, default=0.2,
                        help="Test size for train/test split.")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = train_setup_logging("integrate_train_eval")
    logger.info(f"Starting integration pipeline for task T031.")
    logger.info(f"Features path: {args.features_path}")
    logger.info(f"Results directory: {args.results_dir}")

    results_path = Path(args.results_dir)
    ensure_directories(results_path)

    # 1. Load Features
    logger.info("Loading features from JSON...")
    try:
        features = train_load_features(args.features_path)
    except FileNotFoundError:
        logger.error(f"Features file not found at {args.features_path}. Please run T025 first.")
        sys.exit(1)
    
    if not features:
        logger.error("Features list is empty. Cannot proceed with training.")
        sys.exit(1)

    # 2. Train Model
    logger.info("Training Random Forest model...")
    # Prepare data (X, y)
    # Assuming features is a list of dicts. We need to extract X and y.
    # The train module's prepare_data likely handles this or we do it here.
    # Based on typical flow:
    X, y = [], []
    feature_keys = None
    target_key = "fidelity_loss"
    
    for row in features:
        # Infer feature keys from the first row if not set
        if feature_keys is None:
            # Exclude sample_id and target from features
            feature_keys = [k for k in row.keys() if k not in ["sample_id", target_key]]
        
        X.append([row[k] for k in feature_keys])
        y.append(row[target_key])

    # Train
    model, metrics = train_run_training(
        X, y, 
        n_estimators=args.n_estimators, 
        test_size=args.test_size, 
        random_state=args.random_state,
        n_jobs=2 # CPU only
    )
    logger.info(f"Initial training metrics: {metrics}")

    # Save model
    model_path = results_path / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # 3. Run Cross-Validation
    logger.info("Running cross-validation...")
    cv_metrics = train_run_cv(
        X, y,
        n_estimators=args.n_estimators,
        n_splits=args.n_splits,
        random_state=args.random_state
    )
    logger.info(f"CV Metrics: Mean R2={cv_metrics['mean_r2']:.4f}, Std={cv_metrics['std_r2']:.4f}")

    # 4. Run Permutation Test
    logger.info("Running permutation test...")
    # Re-load model if needed, or use the trained one. 
    # evaluate.py's perform_permutation_test likely takes X, y, and model.
    perm_results = eval_perm_test(
        X, y, model, 
        n_permutations=args.n_permutations, 
        random_state=args.random_state
    )
    logger.info(f"Permutation Test p-value: {perm_results['p_value']:.4f}")

    # 5. Null Baseline Comparison
    logger.info("Calculating null baseline (mean predictor)...")
    baseline_metrics = nb_calc_baseline(y)
    logger.info(f"Null Baseline MAE: {baseline_metrics['mae']:.4f}, R2: {baseline_metrics['r2']:.4f}")

    # 6. Compile and Save Final Results
    logger.info("Compiling final results...")
    final_results = {
        "model_metrics": {
            "r2": metrics.get("r2", cv_metrics.get("mean_r2")),
            "mae": metrics.get("mae"),
            "cv_mean_r2": cv_metrics.get("mean_r2"),
            "cv_std_r2": cv_metrics.get("std_r2"),
            "permutation_p_value": perm_results.get("p_value")
        },
        "null_baseline": {
            "mae": baseline_metrics.get("mae"),
            "r2": baseline_metrics.get("r2")
        },
        "comparison": {
            "improvement_over_null": metrics.get("mae", 0) - baseline_metrics.get("mae", 0),
            "significant": perm_results.get("p_value", 1.0) < 0.05
        },
        "config": {
            "n_estimators": args.n_estimators,
            "n_permutations": args.n_permutations,
            "n_splits": args.n_splits,
            "random_state": args.random_state,
            "test_size": args.test_size
        }
    }

    output_file = results_path / "results.json"
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Final results saved to {output_file}")
    logger.info("Integration pipeline completed successfully.")

if __name__ == "__main__":
    main()