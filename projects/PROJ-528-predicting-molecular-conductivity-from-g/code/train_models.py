"""
Train Random Forest and Gradient Boosting regressors on log-transformed target.
Implements FR-003.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_predict

from code.config import SEED, DATA_PATH, TARGET_VAR
from code.logging_config import setup_logging
from code.scaffold_split import scaffold_split
from code.data_loader import load_and_validate_target, apply_log_transformation
from code.descriptors import compute_descriptors_batch

# Setup logging
logger = setup_logging()

def load_processed_data() -> pd.DataFrame:
    """Load the processed descriptors and target data."""
    descriptor_path = os.path.join(DATA_PATH, "processed", "descriptors.csv")
    if not os.path.exists(descriptor_path):
        raise FileNotFoundError(f"Descriptor file not found at {descriptor_path}. "
                                "Run the descriptor pipeline first.")
    
    df = pd.read_csv(descriptor_path)
    
    # Filter valid molecules
    if 'status' in df.columns:
        df = df[df['status'] == 'valid'].copy()
    
    # Load target variable
    target_df = load_and_validate_target(DATA_PATH)
    
    # Merge descriptors with target
    # Assuming 'smiles' is the key in both
    if 'smiles' not in df.columns or 'smiles' not in target_df.columns:
        raise ValueError("Both descriptor and target data must have 'smiles' column")
    
    merged_df = pd.merge(df, target_df, on='smiles', how='inner')
    
    if merged_df.empty:
        raise ValueError("No matching molecules found between descriptors and target data")
    
    return merged_df

def prepare_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare feature matrix X, target y, and indices for splitting.
    Excludes SMILES and status columns.
    """
    # Identify feature columns (exclude SMILES, status, and target)
    exclude_cols = ['smiles', 'status', TARGET_VAR]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found after excluding metadata and target")
    
    X = df[feature_cols].values
    y = df[TARGET_VAR].values
    smiles_list = df['smiles'].values
    
    # Apply log transformation to target
    y_log = apply_log_transformation(y)
    
    return X, y_log, smiles_list, feature_cols

def train_and_evaluate(
    X: np.ndarray,
    y: np.ndarray,
    smiles: np.ndarray,
    feature_names: list,
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models using scaffold split.
    Returns metrics and model artifacts.
    """
    logger.info(f"Starting model training with {len(X)} samples")
    
    # Perform scaffold split
    # We need to map smiles to indices for the split function
    smiles_to_idx = {smi: i for i, smi in enumerate(smiles)}
    
    # The scaffold_split function expects a DataFrame with 'smiles' column
    # We'll create a temporary DataFrame for splitting
    split_df = pd.DataFrame({'smiles': smiles})
    
    try:
        train_idx, test_idx = scaffold_split(split_df, seed=seed)
    except Exception as e:
        logger.error(f"Scaffold split failed: {e}")
        # Fallback to random split if scaffold split fails
        logger.warning("Falling back to random split due to scaffold split failure")
        np.random.seed(seed)
        indices = np.arange(len(smiles))
        np.random.shuffle(indices)
        split_point = int(0.8 * len(indices))
        train_idx = indices[:split_point]
        test_idx = indices[split_point:]
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Initialize models
    rf_model = RandomForestRegressor(
        n_estimators=100,
        random_state=seed,
        n_jobs=-1,
        max_depth=10
    )
    
    gb_model = GradientBoostingRegressor(
        n_estimators=100,
        random_state=seed,
        max_depth=5,
        learning_rate=0.1
    )
    
    # Train models
    logger.info("Training Random Forest...")
    rf_model.fit(X_train, y_train)
    
    logger.info("Training Gradient Boosting...")
    gb_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_rf = rf_model.predict(X_test)
    y_pred_gb = gb_model.predict(X_test)
    
    # Calculate metrics
    rf_r2 = r2_score(y_test, y_pred_rf)
    gb_r2 = r2_score(y_test, y_pred_gb)
    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    gb_mae = mean_absolute_error(y_test, y_pred_gb)
    
    logger.info(f"Random Forest - R²: {rf_r2:.4f}, MAE: {rf_mae:.4f}")
    logger.info(f"Gradient Boosting - R²: {gb_r2:.4f}, MAE: {gb_mae:.4f}")
    
    # Cross-validation scores (on training set)
    logger.info("Performing 5-fold cross-validation on training set...")
    rf_cv_pred = cross_val_predict(rf_model, X_train, y_train, cv=5)
    gb_cv_pred = cross_val_predict(gb_model, X_train, y_train, cv=5)
    
    rf_cv_r2 = r2_score(y_train, rf_cv_pred)
    gb_cv_r2 = r2_score(y_train, gb_cv_pred)
    
    # Feature importances
    rf_importance = dict(zip(feature_names, rf_model.feature_importances_.tolist()))
    gb_importance = dict(zip(feature_names, gb_model.feature_importances_.tolist()))
    
    results = {
        'rf_r2': float(rf_r2),
        'rf_mae': float(rf_mae),
        'rf_cv_r2': float(rf_cv_r2),
        'gb_r2': float(gb_r2),
        'gb_mae': float(gb_mae),
        'gb_cv_r2': float(gb_cv_r2),
        'train_size': int(len(X_train)),
        'test_size': int(len(X_test)),
        'seed': seed,
        'target_var': TARGET_VAR,
        'feature_importance_rf': rf_importance,
        'feature_importance_gb': gb_importance
    }
    
    # Save model artifacts (just the predictions and metrics for now)
    # In a real scenario, we'd pickle the models, but for this task we focus on metrics
    predictions_df = pd.DataFrame({
        'smiles': smiles[test_idx],
        'actual': y_test,
        'pred_rf': y_pred_rf,
        'pred_gb': y_pred_gb
    })
    
    output_dir = os.path.join(DATA_PATH, "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    predictions_path = os.path.join(output_dir, "model_predictions.csv")
    predictions_df.to_csv(predictions_path, index=False)
    logger.info(f"Saved predictions to {predictions_path}")
    
    return results

def main():
    """Main entry point for model training."""
    logger.info("Starting model training pipeline (T029)")
    
    try:
        # Load data
        df = load_processed_data()
        logger.info(f"Loaded {len(df)} molecules")
        
        # Prepare features and target
        X, y, smiles, feature_names = prepare_features_and_target(df)
        logger.info(f"Prepared {X.shape[1]} features for {X.shape[0]} samples")
        
        # Train and evaluate models
        results = train_and_evaluate(X, y, smiles, feature_names)
        
        # Save results
        output_dir = os.path.join(DATA_PATH, "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        results_path = os.path.join(output_dir, "model_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved model results to {results_path}")
        logger.info("Model training completed successfully")
        
        return results
        
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
