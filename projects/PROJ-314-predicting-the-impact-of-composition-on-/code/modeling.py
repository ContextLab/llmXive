import pandas as pd
import numpy as np
import logging
import json
import os
import sys
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from config import get_config_value, get_project_config
from contracts.schemas import CeramicEntry, ModelResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/modeling.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_PROCESSED_PATH = Path("data/processed/step4_final.csv")
DATA_MODELS_DIR = Path("data/models")
DATA_RESULTS_DIR = Path("data/results")
BEST_MODEL_PATH = DATA_MODELS_DIR / "best_model.pkl"

def load_processed_data() -> Tuple[pd.DataFrame, List[str], str]:
    """
    Load the cleaned and processed dataset.
    Returns:
        df: The processed DataFrame.
        feature_columns: List of feature column names.
        target_column: Name of the target column.
    """
    if not DATA_PROCESSED_PATH.exists():
        raise FileNotFoundError(
            f"Processed data file not found at {DATA_PROCESSED_PATH}. "
            "Run the ingestion pipeline (T018f-clean) first."
        )

    df = pd.read_csv(DATA_PROCESSED_PATH)
    
    # Define target and features based on project spec
    target_column = 'weibull_modulus'
    
    # Exclude non-feature columns
    exclude_cols = [target_column, 'composition', 'sample_count', 
                    'is_range_flag', 'range_original', 'is_imputed']
    
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_columns:
        raise ValueError("No feature columns found in processed data.")
    
    logger.info(f"Loaded {len(df)} rows with {len(feature_columns)} features.")
    return df, feature_columns, target_column

def prepare_splits(df: pd.DataFrame, feature_columns: List[str], target_column: str, stratify_col: str = 'primary_anion_cation_group') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepare stratified train/validation/test splits.
    If N < 50, uses hold-out method instead of CV.
    """
    from sklearn.model_selection import train_test_split
    
    X = df[feature_columns]
    y = df[target_column]
    
    # Check for stratification column
    if stratify_col not in df.columns:
        logger.warning(f"Stratification column '{stratify_col}' not found. Using simple split.")
        train_X, temp_X, train_y, temp_y = train_test_split(
            X, y, test_size=0.4, random_state=42
        )
    else:
        # Stratify by group
        stratify_series = df[stratify_col]
        # Drop rows with NaN in stratify column if any
        valid_indices = stratify_series.notna()
        if not valid_indices.all():
            logger.warning(f"Dropping {valid_indices.sum() - valid_indices.sum()} rows with NaN in {stratify_col}")
            X = X[valid_indices]
            y = y[valid_indices]
            stratify_series = stratify_series[valid_indices]
        
        train_X, temp_X, train_y, temp_y = train_test_split(
            X, y, test_size=0.4, random_state=42, stratify=stratify_series
        )
    
    # Further split temp into validation and test
    if stratify_col in temp_X.index: # Re-apply stratify if possible
       # We need the stratify series for the temp set
       temp_stratify = stratify_series.loc[temp_X.index]
       val_X, test_X, val_y, test_y = train_test_split(
           temp_X, temp_y, test_size=0.5, random_state=42, stratify=temp_stratify
       )
    else:
        val_X, test_X, val_y, test_y = train_test_split(
            temp_X, temp_y, test_size=0.5, random_state=42
        )
        
    logger.info(f"Split sizes: Train={len(train_X)}, Val={len(val_X)}, Test={len(test_X)}")
    return train_X, val_X, test_X, train_y, val_y, test_y

def validate_search_space() -> Dict[str, Any]:
    """
    Defines the constrained hyperparameter search space.
    """
    # Task T027a implementation logic (reused here)
    return {
        'random_forest': {
            'n_estimators': [50, 100],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        },
        'gradient_boosting': {
            'n_estimators': [50, 100],
            'learning_rate': [0.05, 0.1],
            'max_depth': [3, 5],
            'subsample': [0.8, 1.0]
        }
    }

def train_models(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> Tuple[Any, str, Dict[str, float]]:
    """
    Train RF and GBM models using the defined search space.
    Returns the best model, its type, and validation metrics.
    """
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import GridSearchCV
    from sklearn.metrics import mean_absolute_error, r2_score

    search_space = validate_search_space()
    best_model = None
    best_type = ""
    best_score = -np.inf
    best_metrics = {}

    models = {
        'RandomForest': (RandomForestRegressor(random_state=42), search_space['random_forest']),
        'GradientBoosting': (GradientBoostingRegressor(random_state=42), search_space['gradient_boosting'])
    }

    for name, (model, params) in models.items():
        logger.info(f"Training {name}...")
        try:
            grid_search = GridSearchCV(
                model, params, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1
            )
            grid_search.fit(X_train, y_train)
            
            val_pred = grid_search.predict(X_val)
            val_mae = mean_absolute_error(y_val, val_pred)
            val_r2 = r2_score(y_val, val_pred)
            
            logger.info(f"{name} Best Params: {grid_search.best_params_}, Val MAE: {val_mae:.4f}, Val R2: {val_r2:.4f}")
            
            if -grid_search.best_score_ < best_score or best_model is None:
                # Using negative MAE from cv as the primary selection metric for consistency
                # Or we can use validation set performance. Let's use validation set MAE for final selection.
                if best_model is None or val_mae < best_metrics.get('mae', float('inf')):
                    best_model = grid_search.best_estimator_
                    best_type = name
                    best_metrics = {'mae': val_mae, 'r2': val_r2, 'params': grid_search.best_params_}
                    best_score = -val_mae # Lower MAE is better
        except Exception as e:
            logger.error(f"Error training {name}: {e}")
            continue

    if best_model is None:
        raise RuntimeError("Failed to train any model successfully.")
    
    return best_model, best_type, best_metrics

def save_best_model(model: Any, model_type: str, metrics: Dict[str, Any]) -> None:
    """
    Saves the best performing model to data/models/best_model.pkl.
    Also saves a metadata JSON alongside it.
    """
    DATA_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save the model object
    with open(BEST_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'model': model,
            'type': model_type,
            'metrics': metrics
        }, f)
    
    logger.info(f"Best model ({model_type}) saved to {BEST_MODEL_PATH}")
    
    # Save metadata for easy loading
    metadata_path = DATA_MODELS_DIR / "best_model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            'model_type': model_type,
            'metrics': metrics,
            'saved_at': str(pd.Timestamp.now())
        }, f, indent=2)
    logger.info(f"Model metadata saved to {metadata_path}")

def evaluate_models(model: Any, X_test: pd.DataFrame, y_test: pd.Series, model_type: str) -> Dict[str, float]:
    """
    Evaluate the model on the test set.
    """
    from sklearn.metrics import mean_absolute_error, r2_score
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Test MAE: {mae:.4f}, Test R2: {r2:.4f}")
    return {'mae': mae, 'r2': r2}

def run_baseline_predictor(y_train: pd.Series, y_test: pd.Series) -> float:
    """
    Simple baseline: predict mean of training set for all test samples.
    """
    mean_val = y_train.mean()
    baseline_pred = [mean_val] * len(y_test)
    from sklearn.metrics import mean_absolute_error
    mae = mean_absolute_error(y_test, baseline_pred)
    logger.info(f"Baseline (Global Mean) MAE: {mae:.4f}")
    return mae

def main():
    """
    Main entry point for T027d: Save Best Model.
    Orchestrates loading, training, and saving.
    """
    logger.info("Starting T027d: Save Best Model")
    
    try:
        # 1. Load Data
        df, feature_cols, target_col = load_processed_data()
        
        # 2. Prepare Splits
        train_X, val_X, test_X, train_y, val_y, test_y = prepare_splits(df, feature_cols, target_col)
        
        # 3. Train Models
        best_model, best_type, train_metrics = train_models(train_X, train_y, val_X, val_y)
        
        # 4. Evaluate on Test Set
        test_metrics = evaluate_models(best_model, test_X, test_y, best_type)
        
        # 5. Run Baseline for comparison
        baseline_mae = run_baseline_predictor(train_y, test_y)
        
        # 6. Save Best Model (Task T027d Core)
        final_metrics = {
            'model_type': best_type,
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'baseline_mae': baseline_mae,
            'improvement_over_baseline': f"{((baseline_mae - test_metrics['mae']) / baseline_mae) * 100:.2f}%"
        }
        
        save_best_model(best_model, best_type, final_metrics)
        
        # Save final metrics report
        DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_path = DATA_RESULTS_DIR / "model_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(final_metrics, f, indent=2)
        logger.info(f"Final metrics saved to {metrics_path}")
        
        logger.info("T027d completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"T027d failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())