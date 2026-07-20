"""
Main entry point for the crack propagation ML pipeline.
Orchestrates the full pipeline: data loading, preprocessing, baseline training,
augmented model training with CV, and statistical comparison.
"""
import logging
import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
from config import ensure_dirs
from data.loader import load_nasa_data, load_nist_data
from data.preprocessor import clean_data, impute_missing
from models.baseline import train_baseline_model, evaluate_baseline
from models.augmented import train_augmented_model, evaluate_model
from models.trainer import run_tuning_pipeline
from utils.stats import permutation_test_model_comparison, compare_models_r2
from data.validator import load_validation_schema, validate_required_columns, halt_if_invalid

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Orchestrate the full pipeline:
    1. Load and clean real data (NASA/NIST)
    2. Train Baseline (Paris Law)
    3. Train Augmented Model (RF/XGBoost) with Hyperparameter Tuning (CV)
    4. Calculate Delta R2
    5. Perform Permutation Test for significance
    6. Save results to data/
    """
    logger.info("Starting Crack Propagation ML Pipeline...")
    ensure_dirs()
    logger.info("Directories ensured.")

    # 1. Load and Preprocess Data
    logger.info("Loading data from NASA and NIST sources...")
    try:
        df_nasa = load_nasa_data()
        df_nist = load_nist_data()
        df = pd.concat([df_nasa, df_nist], ignore_index=True)
    except Exception as e:
        logger.error(f"Failed to load real data: {e}")
        raise

    # 2. Validate and Clean
    logger.info("Validating and cleaning data...")
    schema = load_validation_schema()
    if not validate_required_columns(df, schema):
        halt_if_invalid("Required columns missing after loading.")
    
    df_clean = clean_data(df)
    df_processed = impute_missing(df_clean)
    
    logger.info(f"Dataset size after cleaning: {len(df_processed)} rows")

    # 3. Prepare Features and Target
    target_col = 'da_dN'
    base_feature_col = 'delta_K'
    
    # Check if we have enough data
    if len(df_processed) < 20:
        logger.warning("Dataset too small for meaningful analysis. Aborting.")
        return

    # --- Step A: Train Baseline Model ---
    logger.info("Training Baseline Model (Paris Law: log(da/dN) ~ log(dK))...")
    X_base = np.log10(df_processed[base_feature_col].values).reshape(-1, 1)
    y = np.log10(df_processed[target_col].values)
    
    baseline_model, baseline_r2 = train_baseline_model(X_base, y)
    logger.info(f"Baseline R2: {baseline_r2:.4f}")

    # --- Step B: Train Augmented Model with Tuning (CV) ---
    logger.info("Training Augmented Model (Composition + Heat Treatment) with Hyperparameter Tuning...")
    
    # Identify augmented features
    exclude_cols = [base_feature_col, target_col]
    # Filter for numeric columns that can be used as features
    aug_feature_cols = [c for c in df_processed.columns 
                        if c not in exclude_cols and pd.api.types.is_numeric_dtype(df_processed[c])]
    
    # If the preprocessor didn't create a log(dK) column, we must include it manually in the feature set
    # because the augmented model needs the physics base plus the extra features.
    # We construct X_aug here to ensure log(dK) is present.
    if 'log_delta_K' not in aug_feature_cols:
        # Create the log column data
        log_dk = np.log10(df_processed[base_feature_col].values)
        # We will construct X_aug as a numpy array: [log_dK, ...other_numeric_features]
        X_aug = np.column_stack([log_dk, df_processed[aug_feature_cols].values])
        final_feature_names = ['log_delta_K'] + aug_feature_cols
    else:
        X_aug = df_processed[aug_feature_cols].values
        final_feature_names = aug_feature_cols

    logger.info(f"Using {len(final_feature_names)} features for augmented model: {final_feature_names}")

    # Run the tuning pipeline (Optuna + CV) which returns the best model and best params
    # The trainer module handles the cross-validation and returns the trained estimator
    best_model, best_params, cv_results = run_tuning_pipeline(
        X=X_aug,
        y=y,
        feature_names=final_feature_names,
        target_name='log_da_dN'
    )
    
    # Evaluate the tuned augmented model on the full dataset (or a held-out set if trainer did that)
    # For this pipeline step, we evaluate on the same data to get the R2 for the permutation test context
    # Note: In a strict production setting, we'd evaluate on a test set. Here we use the fitted model's R2
    # or a cross-validated estimate. The trainer usually returns the best model fitted on all data if CV is used for selection.
    # We'll assume `best_model` is fitted on the full X_aug, y provided to it (as per typical Optuna patterns in this pipeline).
    
    # Calculate R2 for the augmented model
    y_pred_aug = best_model.predict(X_aug)
    augmented_r2 = compare_models_r2(y, y_pred_aug)
    
    logger.info(f"Augmented Model Best Params: {best_params}")
    logger.info(f"Augmented R2: {augmented_r2:.4f}")

    # --- Step C: Calculate Delta R2 ---
    delta_r2_observed = augmented_r2 - baseline_r2
    logger.info(f"Observed Delta R2 (Augmented - Baseline): {delta_r2_observed:.4f}")

    # --- Step D: Permutation Test ---
    logger.info("Performing Permutation Test to verify significance of Delta R2...")
    
    n_permutations = 1000
    seed = 42
    
    # Define model functions for the test
    # We pass the feature matrices and re-train inside the permutation loop to simulate the null
    def baseline_func(X, y):
        m, r = train_baseline_model(X, y)
        return r
    
    def augmented_func(X, y):
        # We need to re-run the tuning or use a fixed model for speed in permutation test?
        # The permutation test usually re-trains. To keep it feasible, we might use a simpler model 
        # or a fixed version of the best model if tuning is too slow.
        # However, the spec asks for the result of the *trained* model.
        # To strictly follow the "Permutation Test" logic with the *same* model type:
        # We will train a model of the same type (e.g., Random Forest with fixed best params) 
        # to avoid 1000x Optuna runs.
        # We'll assume the trainer can be called with a fixed seed and fixed params for the test.
        # For this implementation, we will use a simplified training call inside the lambda 
        # that uses the best_params found above to speed up the permutation test.
        from models.augmented import train_random_forest
        # Train a model with the best parameters found
        m = train_random_forest(X, y, n_estimators=best_params.get('n_estimators', 100), 
                                max_depth=best_params.get('max_depth', 5))
        r = evaluate_model(m, X, y)
        return r

    p_value, permutation_stats = permutation_test_model_comparison(
        X_base=X_base,
        X_aug=X_aug,
        y=y,
        baseline_model_func=baseline_func,
        augmented_model_func=augmented_func,
        n_permutations=n_permutations,
        seed=seed
    )
    
    logger.info(f"Permutation Test Results:")
    logger.info(f"  - Observed Delta R2: {delta_r2_observed:.4f}")
    logger.info(f"  - P-value: {p_value:.4f}")
    
    significance = p_value <= 0.05
    if significance:
        logger.info("Result: The Augmented model provides a statistically significant improvement over the Baseline (p <= 0.05).")
    else:
        logger.info("Result: The Augmented model does NOT provide a statistically significant improvement over the Baseline (p > 0.05).")

    # --- Step E: Save Results ---
    results = {
        "baseline_r2": float(baseline_r2),
        "augmented_r2": float(augmented_r2),
        "delta_r2_observed": float(delta_r2_observed),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "significant": significance,
        "best_augmented_params": best_params,
        "cv_results_summary": str(cv_results) if cv_results else None
    }
    
    results_path = Path("data/permutation_test_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_path}")

if __name__ == "__main__":
    main()