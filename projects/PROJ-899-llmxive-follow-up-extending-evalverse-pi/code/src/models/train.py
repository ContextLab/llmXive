"""
Training pipeline for Ridge, Lasso, and XGBoost models.
Targets human expert scores from the EvalVerse dataset.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

from src.config import get_project_root, get_processed_data_dir, get_reports_root
from src.data.config import get_processed_data_path
from src.utils import get_logger, write_json, ensure_directories

logger = get_logger(__name__)

# Constants
RANDOM_SEED = 42
TEST_SIZE = 0.2
OUTPUT_FILE = "model_training_results.json"
MODEL_DIR = "models"

def load_processed_features() -> pd.DataFrame:
    """
    Load preprocessed features and expert scores from the processed data directory.
    Expects a CSV with feature columns and a 'expert_score' column.
    """
    data_path = get_processed_data_path()
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Ensure T012 and T013 have completed successfully.")
    
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = ['expert_score']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Processed data must contain 'expert_score' column. "
                         f"Found columns: {df.columns.tolist()}")
    
    logger.info(f"Loaded {len(df)} samples from {data_path}")
    return df

def prepare_data(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Prepare data for training: split into X, y, and scale features.
    """
    X = df[feature_cols].values
    y = df['expert_score'].values

    # Handle any NaN or inf values
    if np.any(~np.isfinite(X)) or np.any(~np.isfinite(y)):
        logger.warning("Found NaN or inf values in data. Dropping those rows.")
        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[mask]
        y = y[mask]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def train_ridge(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, 
                y_test: np.ndarray, alphas: List[float] = [0.1, 1.0, 10.0]) -> Dict[str, Any]:
    """
    Train Ridge regression with multiple alpha values and select the best.
    """
    best_model = None
    best_alpha = None
    best_cv_score = -np.inf
    results = []

    for alpha in alphas:
        model = Ridge(alpha=alpha, random_state=RANDOM_SEED)
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
        mean_cv = np.mean(cv_scores)
        
        results.append({
            'model': 'Ridge',
            'alpha': alpha,
            'mean_cv_r2': mean_cv,
            'std_cv_r2': np.std(cv_scores)
        })
        
        if mean_cv > best_cv_score:
            best_cv_score = mean_cv
            best_alpha = alpha
            best_model = Ridge(alpha=alpha, random_state=RANDOM_SEED)

    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    
    test_metrics = {
        'r2': r2_score(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
    }

    return {
        'model': best_model,
        'type': 'Ridge',
        'best_alpha': best_alpha,
        'cv_results': results,
        'test_metrics': test_metrics,
        'feature_importance': dict(zip(
            [f'feature_{i}' for i in range(len(best_model.coef_))],
            best_model.coef_
        ))
    }

def train_lasso(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray,
                y_test: np.ndarray, alphas: List[float] = [0.01, 0.1, 1.0]) -> Dict[str, Any]:
    """
    Train Lasso regression with multiple alpha values and select the best.
    """
    best_model = None
    best_alpha = None
    best_cv_score = -np.inf
    results = []

    for alpha in alphas:
        model = Lasso(alpha=alpha, random_state=RANDOM_SEED, max_iter=10000)
        try:
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
            mean_cv = np.mean(cv_scores)
            
            results.append({
                'model': 'Lasso',
                'alpha': alpha,
                'mean_cv_r2': mean_cv,
                'std_cv_r2': np.std(cv_scores)
            })
            
            if mean_cv > best_cv_score:
                best_cv_score = mean_cv
                best_alpha = alpha
                best_model = Lasso(alpha=alpha, random_state=RANDOM_SEED, max_iter=10000)
        except Exception as e:
            logger.warning(f"Lasso with alpha={alpha} failed: {e}")
            continue

    if best_model is None:
        raise RuntimeError("No valid Lasso model could be trained.")

    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    
    test_metrics = {
        'r2': r2_score(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
    }

    # Count non-zero coefficients
    non_zero_count = np.sum(best_model.coef_ != 0)

    return {
        'model': best_model,
        'type': 'Lasso',
        'best_alpha': best_alpha,
        'cv_results': results,
        'test_metrics': test_metrics,
        'feature_importance': dict(zip(
            [f'feature_{i}' for i in range(len(best_model.coef_))],
            best_model.coef_
        )),
        'non_zero_features': non_zero_count
    }

def train_xgboost(X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray,
                  y_test: np.ndarray, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Train XGBoost regressor with default or custom parameters.
    """
    default_params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'random_state': RANDOM_SEED,
        'n_jobs': -1
    }
    
    if params:
        default_params.update(params)

    model = xgb.XGBRegressor(**default_params)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    y_pred = model.predict(X_test)
    
    test_metrics = {
        'r2': r2_score(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
    }

    # Get feature importance
    importance_dict = model.get_booster().get_score(importance_type='gain')
    importance_dict = {f'feature_{k.replace("f", "")}': float(v) for k, v in importance_dict.items()}

    return {
        'model': model,
        'type': 'XGBoost',
        'params': default_params,
        'test_metrics': test_metrics,
        'feature_importance': importance_dict
    }

def save_results(all_results: Dict[str, Any], output_path: str):
    """
    Save training results to a JSON file.
    """
    # Convert numpy types to Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        return obj

    serializable_results = convert_types(all_results)
    write_json(output_path, serializable_results)
    logger.info(f"Saved training results to {output_path}")

def main():
    """
    Main entry point for the training pipeline.
    """
    logger.info("Starting model training pipeline (T015)")
    
    try:
        # Load data
        df = load_processed_features()
        
        # Identify feature columns (exclude 'expert_score' and any metadata columns)
        exclude_cols = ['expert_score', 'clip_id', 'video_id', 'filename']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            raise ValueError("No feature columns found in processed data.")
        
        logger.info(f"Using {len(feature_cols)} feature columns for training")
        
        # Prepare data
        X_train, X_test, y_train, y_test, scaler = prepare_data(df, feature_cols)
        
        # Train models
        results = {
            'metadata': {
                'n_samples': len(df),
                'n_features': len(feature_cols),
                'n_train': len(y_train),
                'n_test': len(y_test),
                'feature_columns': feature_cols,
                'random_seed': RANDOM_SEED,
                'test_size': TEST_SIZE
            },
            'models': {}
        }

        # Ridge
        logger.info("Training Ridge regression...")
        ridge_results = train_ridge(X_train, X_test, y_train, y_test)
        results['models']['Ridge'] = {
            'best_alpha': ridge_results['best_alpha'],
            'cv_results': ridge_results['cv_results'],
            'test_metrics': ridge_results['test_metrics'],
            'feature_importance': ridge_results['feature_importance']
        }

        # Lasso
        logger.info("Training Lasso regression...")
        lasso_results = train_lasso(X_train, X_test, y_train, y_test)
        results['models']['Lasso'] = {
            'best_alpha': lasso_results['best_alpha'],
            'cv_results': lasso_results['cv_results'],
            'test_metrics': lasso_results['test_metrics'],
            'feature_importance': lasso_results['feature_importance'],
            'non_zero_features': lasso_results['non_zero_features']
        }

        # XGBoost
        logger.info("Training XGBoost...")
        xgb_results = train_xgboost(X_train, X_test, y_train, y_test)
        results['models']['XGBoost'] = {
            'params': xgb_results['params'],
            'test_metrics': xgb_results['test_metrics'],
            'feature_importance': xgb_results['feature_importance']
        }

        # Determine best model based on test R2
        model_scores = {
            name: data['test_metrics']['r2'] 
            for name, data in results['models'].items()
        }
        best_model_name = max(model_scores, key=model_scores.get)
        results['best_model'] = best_model_name
        results['best_model_r2'] = model_scores[best_model_name]

        logger.info(f"Best model: {best_model_name} with R2 = {model_scores[best_model_name]:.4f}")

        # Save results
        reports_dir = get_reports_root()
        ensure_directories([reports_dir])
        output_path = os.path.join(reports_dir, OUTPUT_FILE)
        save_results(results, output_path)

        logger.info("Training pipeline completed successfully")
        return results

    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
