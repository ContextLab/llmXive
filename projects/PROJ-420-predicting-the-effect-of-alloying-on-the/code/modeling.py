from __future__ import annotations
import json
import os
import pickle
import sys
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from compositional import ilr
from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()

def load_features_and_target(data_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the cleaned dataset and separate features/target."""
    if data_path is None:
        data_path = str(config.data_processed / "alloys_clean.parquet")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run T015c first.")
    
    df = pd.read_parquet(data_path)
    
    # Features: ILR transformed compositions (Cu, Mg, Si, Zn, Mn)
    # The ILR transformation is applied in the data cleaning pipeline (T019)
    # We assume columns 'ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4' exist
    feature_cols = ['ilr_0', 'ilr_1', 'ilr_2', 'ilr_3', 'ilr_4']
    
    # Validate features exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing ILR feature columns: {missing}. Run T019 first.")
    
    X = df[feature_cols]
    y = df['poisson_ratio']
    
    return X, y

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ILR transformation to composition columns."""
    # This is a wrapper for the compositional ilr function
    # Expected input: columns 'Cu', 'Mg', 'Si', 'Zn', 'Mn'
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    # Check if all composition columns exist
    missing = [c for c in composition_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing composition columns for ILR: {missing}")
    
    # Extract composition matrix (must be positive and sum to 1)
    comp_matrix = df[composition_cols].values
    
    # Apply ILR transformation
    ilr_transformed = ilr(comp_matrix)
    
    # Add to dataframe
    for i in range(ilr_transformed.shape[1]):
        df[f'ilr_{i}'] = ilr_transformed[:, i]
    
    return df

def train_random_forest_with_cv(X: pd.DataFrame, y: pd.Series, n_estimators: int = 100, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest model."""
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    model.fit(X, y)
    return model

def run_repeated_cv(X: pd.DataFrame, y: pd.Series, n_splits: int = 5, n_repeats: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """Perform repeated k-fold cross-validation."""
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    all_scores = []
    for _ in range(n_repeats):
        scores = cross_val_score(
            RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1),
            X, y,
            cv=kfold,
            scoring='neg_mean_absolute_error',
            n_jobs=-1
        )
        all_scores.extend(-scores)  # Convert back to positive MAE
    
    mean_mae = np.mean(all_scores)
    std_mae = np.std(all_scores)
    ci_lower = mean_mae - 1.96 * std_mae
    ci_upper = mean_mae + 1.96 * std_mae
    
    return {
        'cv_mae': float(mean_mae),
        'cv_std': float(std_mae),
        'cv_ci_lower': float(ci_lower),
        'cv_ci_upper': float(ci_upper)
    }

def evaluate_model_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
    """Evaluate model on held-out test set."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    residuals = y_test - y_pred
    
    return {
        'test_mae': float(mae),
        'residuals': residuals.tolist()
    }

def save_model_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Save model metrics to JSON."""
    if output_path is None:
        output_path = str(config.results / "model_metrics.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")
    return output_path

def save_residuals(residuals: List[float], output_path: Optional[str] = None) -> str:
    """Save residuals to JSON."""
    if output_path is None:
        output_path = str(config.results / "residuals.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(residuals, f, indent=2)
    
    logger.info(f"Residuals saved to {output_path}")
    return output_path

def check_mae_threshold(cv_mae: float, threshold: float = 0.05) -> bool:
    """Check if CV MAE exceeds threshold."""
    return cv_mae > threshold

def write_methodological_flags(cv_mae: float, output_path: Optional[str] = None) -> str:
    """Write methodological flags to JSON."""
    if output_path is None:
        output_path = str(config.results / "methodological_flags.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    flags = {
        'mae_flag': check_mae_threshold(cv_mae),
        'cv_mae': cv_mae
    }
    
    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)
    
    logger.info(f"Methodological flags saved to {output_path}")
    return output_path

def load_split_indices(split_path: Optional[str] = None) -> Dict[str, List[int]]:
    """Load split indices from JSON."""
    if split_path is None:
        split_path = str(config.data_processed / "split_indices.json")
    
    if not os.path.exists(split_path):
        raise FileNotFoundError(f"Split indices not found at {split_path}. Run T020 first.")
    
    with open(split_path, 'r') as f:
        return json.load(f)

def save_model(model: RandomForestRegressor, output_path: Optional[str] = None) -> str:
    """
    Serialize the trained Random Forest model to disk.
    
    Requirement: Ensure directory `models/` exists using `os.makedirs('models', exist_ok=True)` 
    before saving.
    
    Args:
        model: The trained RandomForestRegressor instance.
        output_path: Path to save the model. Defaults to `models/rf_model.pkl`.
    
    Returns:
        str: The path where the model was saved.
    """
    if output_path is None:
        output_path = str(config.models / "rf_model.pkl")
    
    # Ensure models directory exists
    model_dir = os.path.dirname(output_path)
    os.makedirs(model_dir, exist_ok=True)
    
    # Save using joblib with specified compression
    joblib.dump(model, output_path, compress=3, protocol=3)
    
    logger.info(f"Model serialized to {output_path}")
    
    # Verification: Assert file exists and can be loaded
    if not os.path.exists(output_path):
        raise RuntimeError(f"Model file {output_path} was not created.")
    
    try:
        loaded_model = joblib.load(output_path)
        logger.info("Model verification: Successfully loaded saved model.")
    except Exception as e:
        raise RuntimeError(f"Failed to load saved model for verification: {e}")
    
    return output_path

def run_modeling_pipeline() -> Dict[str, Any]:
    """
    Run the full modeling pipeline:
    1. Load data
    2. Split data (T020)
    3. Train with CV (T021)
    4. Evaluate on test (T025)
    5. Save metrics (T023d)
    6. Save residuals (T025)
    7. Write flags (T023c)
    8. Serialize model (T024)
    """
    log_operation("run_modeling_pipeline", status="start")
    
    # 1. Load data
    X, y = load_features_and_target()
    logger.info(f"Loaded {len(X)} samples")
    
    # 2. Load split indices (produced by T020)
    indices = load_split_indices()
    train_idx = indices['train']
    val_idx = indices['val']
    test_idx = indices['test']
    
    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_val = X.iloc[val_idx]
    y_val = y.iloc[val_idx]
    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]
    
    logger.info(f"Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    
    # 3. Run Repeated CV on Train+Val (T021)
    # Note: T021 says "using ONLY the Train and Validation sets"
    X_train_val = pd.concat([X_train, X_val])
    y_train_val = pd.concat([y_train, y_val])
    
    cv_results = run_repeated_cv(X_train_val, y_train_val)
    logger.info(f"CV Results: MAE={cv_results['cv_mae']:.4f}, CI=[{cv_results['cv_ci_lower']:.4f}, {cv_results['cv_ci_upper']:.4f}]")
    
    # 4. Train final model on Train+Val for Test evaluation and Serialization
    # We train on the full Train+Val set to maximize data for the final model
    final_model = train_random_forest_with_cv(X_train_val, y_train_val)
    
    # 5. Evaluate on Test (T025)
    test_results = evaluate_model_on_test(final_model, X_test, y_test)
    logger.info(f"Test MAE: {test_results['test_mae']:.4f}")
    
    # 6. Aggregate Metrics (T023d)
    metrics = {
        'cv_mae': cv_results['cv_mae'],
        'cv_ci_lower': cv_results['cv_ci_lower'],
        'cv_ci_upper': cv_results['cv_ci_upper'],
        'test_mae': test_results['test_mae']
    }
    save_model_metrics(metrics)
    
    # 7. Save Residuals (T025)
    save_residuals(test_results['residuals'])
    
    # 8. Write Flags (T023c)
    write_methodological_flags(cv_results['cv_mae'])
    
    # 9. Serialize Model (T024)
    save_model(final_model)
    
    log_operation("run_modeling_pipeline", status="complete")
    
    return {
        'metrics': metrics,
        'test_residuals': test_results['residuals'],
        'model_path': str(config.models / "rf_model.pkl")
    }

def main():
    """CLI entry point for modeling pipeline."""
    parser = argparse.ArgumentParser(description="Run modeling pipeline")
    parser.add_argument('--data-path', type=str, default=None, help='Path to cleaned data')
    parser.add_argument('--split-path', type=str, default=None, help='Path to split indices')
    args = parser.parse_args()
    
    if args.data_path:
        config.data_processed = Path(args.data_path).parent
    
    try:
        results = run_modeling_pipeline()
        print(f"Modeling pipeline completed successfully.")
        print(f"Model saved to: {results['model_path']}")
        print(f"Metrics: {results['metrics']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
