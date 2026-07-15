import os
import sys
import logging
import json
import time
import pickle
import numpy as np
from pathlib import Path
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.inspection import permutation_importance
import xgboost as xgb
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/xgboost_model.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
ARTIFACTS_DIR = PROJECT_ROOT / 'artifacts'
LME_ARTIFACT_PATH = ARTIFACTS_DIR / 'lme_results.json'
XGBOOST_ARTIFACT_PATH = ARTIFACTS_DIR / 'xgboost_model.pkl'
IMPORTANCE_ARTIFACT_PATH = ARTIFACTS_DIR / 'feature_importance.json'

# Ensure directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def load_split_data():
    """Load the train/test split artifacts generated in T030."""
    train_path = DATA_DIR / 'train_split.csv'
    test_path = DATA_DIR / 'test_split.csv'
    
    if not train_path.exists() or not test_path.exists():
        logger.error(f"Split data files not found. Please run preprocessing first.")
        raise FileNotFoundError(f"Split data files not found at {train_path} or {test_path}")
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

def prepare_features(df, target_col='ductility'):
    """Prepare features and target from dataframe."""
    # Drop non-feature columns
    drop_cols = ['ductility', 'alloy_family', 'id']
    feature_cols = [c for c in df.columns if c not in drop_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in dataframe")
        
    X = df[feature_cols]
    y = df[target_col]
    
    # Handle missing values if any (simple imputation for safety)
    X = X.fillna(X.mean())
    
    return X, y, feature_cols

def tune_and_train(X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray,
                   time_budget: int = 600) -> XGBRegressor:
    """
    Tune hyperparameters and train XGBoost model.
    Uses a simple grid search with early stopping.
    """
    logger.info("Starting hyperparameter tuning...")
    
    # Define parameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1, 0.2],
        'n_estimators': [100, 200, 500],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0],
        'tree_method': ['hist']  # CPU optimized
    }

    best_model = None
    best_score = -np.inf
    best_params = None
    best_model = None
    
    start_time = time.time()
    
    # Simple grid search (limit iterations to respect time budget)
    iterations = 0
    max_iterations = 50  # Limit to avoid timeout
    
    for max_depth in param_grid['max_depth']:
        for lr in param_grid['learning_rate']:
            for n_est in param_grid['n_estimators']:
                if time.time() - start_time > time_budget or iterations >= max_iterations:
                    logger.info("Time budget reached or max iterations hit. Stopping search.")
                    break
                
                iterations += 1
                params = {
                    'max_depth': max_depth,
                    'learning_rate': lr,
                    'n_estimators': n_est,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'tree_method': 'hist',
                    'objective': 'reg:squarederror',
                    'eval_metric': 'rmse',
                    'seed': 42,
                    'verbosity': 0
                }
                
                model = xgb.XGBRegressor(**params)
                
                # Early stopping
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=20,
                    verbose=False
                )
                
                # Evaluate on validation set
                val_preds = model.predict(X_val)
                score = r2_score(y_val, val_preds)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_model = model
                    logger.info(f"New best score: {score:.4f} with params: {params}")
            
            if time.time() - start_time > time_budget or iterations >= max_iterations:
                break
        if time.time() - start_time > time_budget or iterations >= max_iterations:
            break
    
    if best_model is None:
        # Fallback to default parameters
        logger.warning("No model found during tuning, using defaults.")
        best_params = {
            'max_depth': 5,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'tree_method': 'hist',
            'objective': 'reg:squarederror',
            'seed': 42
        }
        best_model = xgb.XGBRegressor(**best_params)
        best_model.fit(X_train, y_train)
    
    logger.info(f"Tuning completed. Best R2: {best_score:.4f}")
    return best_model, best_params, best_score

def evaluate_model(model, X_test, y_test, feature_names):
    """Evaluate model on test set and compute metrics."""
    logger.info("Evaluating model on test set...")
    
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"Test Metrics - R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    if r2 < 0.60:
        logger.warning(f"R2 ({r2:.4f}) is below threshold (0.60). Model may need more data or tuning.")
    
    metrics = {
        'r2': float(r2),
        'mae': float(mae),
        'rmse': float(rmse),
        'test_size': len(y_test)
    }
    
    return metrics

def compute_permutation_importance(model, X_test, y_test, feature_names, n_repeats=10, random_state=42):
    """Compute permutation feature importance."""
    logger.info("Computing permutation feature importance...")
    
    result = permutation_importance(
        model, X_test, y_test, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1, 
        scoring='r2'
    )
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    }).sort_values(by='importance_mean', ascending=False)
    
    logger.info("Permutation importance computed.")
    logger.info(importance_df.to_string(index=False))
    
    return importance_df

def load_lme_artifact():
    """Load the LME results artifact from T027."""
    if not LME_ARTIFACT_PATH.exists():
        logger.warning(f"LME artifact not found at {LME_ARTIFACT_PATH}. Skipping comparison.")
        return None
    
    with open(LME_ARTIFACT_PATH, 'r') as f:
        lme_data = json.load(f)
    
    logger.info(f"Loaded LME artifact: {LME_ARTIFACT_PATH}")
    return lme_data

def compare_with_lme(xgb_importance_df, lme_results):
    """Compare top 3 XGBoost features with top 3 LME coefficients."""
    logger.info("Comparing XGBoost and LME feature importance...")
    
    if lme_results is None:
        logger.warning("LME results not available for comparison.")
        return None
    
    # Extract top 3 XGBoost features
    top_3_xgb = xgb_importance_df.head(3)['feature'].tolist()
    
    # Extract top 3 LME features (assuming 'fixed_effects' key with coefficients)
    # Structure depends on T027 output format
    fixed_effects = lme_results.get('fixed_effects', {})
    if isinstance(fixed_effects, dict):
        # Sort by absolute coefficient value
        sorted_effects = sorted(fixed_effects.items(), key=lambda x: abs(x[1]), reverse=True)
        top_3_lme = [item[0] for item in sorted_effects[:3]]
    elif isinstance(fixed_effects, list):
        # If it's a list of dicts, try to find coefficient column
        # Assuming structure: [{'feature': 'name', 'coef': value}, ...]
        if len(fixed_effects) > 0 and 'feature' in fixed_effects[0] and 'coef' in fixed_effects[0]:
            sorted_effects = sorted(fixed_effects, key=lambda x: abs(x['coef']), reverse=True)
            top_3_lme = [item['feature'] for item in sorted_effects[:3]]
        else:
            logger.warning("Unexpected LME fixed_effects structure.")
            top_3_lme = []
    else:
        logger.warning("Unexpected LME fixed_effects type.")
        top_3_lme = []
    
    logger.info(f"Top 3 XGBoost features: {top_3_xgb}")
    logger.info(f"Top 3 LME features: {top_3_lme}")
    
    # Find intersection
    intersection = set(top_3_xgb) & set(top_3_lme)
    
    comparison_result = {
        'xgb_top_3': top_3_xgb,
        'lme_top_3': top_3_lme,
        'intersection': list(intersection),
        'match_count': len(intersection)
    }
    
    if len(intersection) == 0:
        logger.warning("No common features between top 3 XGBoost and LME. Feature sets may be disjoint.")
    else:
        logger.info(f"Found {len(intersection)} common features: {intersection}")
    
    return comparison_result

def save_artifacts(model, params, metrics, importance_df, comparison_result, X_train, X_test):
    """Save all model artifacts."""
    logger.info("Saving artifacts...")
    
    # 1. Save trained model
    with open(XGBOOST_ARTIFACT_PATH, 'wb') as f:
        pickle.dump({
            'model': model,
            'params': params,
            'metrics': metrics,
            'feature_names': X_train.columns.tolist()
        }, f)
    logger.info(f"Model saved to {XGBOOST_ARTIFACT_PATH}")
    
    # 2. Save feature importance
    importance_dict = importance_df.to_dict(orient='records')
    with open(IMPORTANCE_ARTIFACT_PATH, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    logger.info(f"Feature importance saved to {IMPORTANCE_ARTIFACT_PATH}")
    
    # 3. Save comparison result
    comparison_path = ARTIFACTS_DIR / 'lme_xgb_comparison.json'
    if comparison_result:
        with open(comparison_path, 'w') as f:
            json.dump(comparison_result, f, indent=2)
        logger.info(f"Comparison result saved to {comparison_path}")
    else:
        logger.warning("No comparison result to save.")

def main():
    """Main execution function for T033."""
    logger.info("Starting T033: Feature Importance and LME Comparison")
    
    try:
        # 1. Load split data
        train_df, val_df, test_df = load_split_data()
        
        # 2. Prepare features
        X_train, y_train, feature_cols_train = prepare_features(train_df)
        X_test, y_test, feature_cols_test = prepare_features(test_df)
        
        # Ensure feature columns match
        if set(feature_cols_train) != set(feature_cols_test):
            logger.warning("Feature columns mismatch between train and test. Aligning...")
            common_cols = list(set(feature_cols_train) & set(feature_cols_test))
            X_train = X_train[common_cols]
            X_test = X_test[common_cols]
            feature_cols_train = common_cols
            feature_cols_test = common_cols
        
        # 3. Split into train/val for tuning (simple 80/20 split of training data)
        # Using a fixed split for tuning since we already have a test set
        from sklearn.model_selection import train_test_split
        X_train_tune, X_val, y_train_tune, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        
        # 4. Tune and train
        model, best_params, best_val_score = tune_and_train(
            X_train_tune, y_train_tune, X_val, y_val
        )
        
        # 5. Evaluate on test set
        metrics = evaluate_model(model, X_test, y_test, feature_cols_test)
        
        # 6. Compute permutation importance
        importance_df = compute_permutation_importance(
            model, X_test, y_test, feature_cols_test
        )
        
        # 7. Load LME results and compare
        lme_results = load_lme_artifact()
        comparison_result = compare_with_lme(importance_df, lme_results)
        
        # 8. Save artifacts
        save_artifacts(
            model, best_params, metrics, importance_df, 
            comparison_result, X_train, X_test
        )
        
        logger.info("T033 completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error during T033 execution: {str(e)}", exc_info=True)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)