import os
import sys
import json
import pickle
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GridSearchCV, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import json

# Import project utilities if available, otherwise define minimal helpers
try:
    from utils.config import get_config
    from utils.imputation import impute_missing_values
except ImportError:
    get_config = None
    impute_missing_values = None

warnings.filterwarnings('ignore')

def load_processed_data():
    """Load the merged dataset from the preprocessing stage."""
    config = get_config() if get_config else None
    if config:
        path = Path(config.get('paths', {}).get('processed_data', 'data/processed/merged_dataset.csv'))
    else:
        path = Path('data/processed/merged_dataset.csv')
    
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}. Run T017 first.")
    
    df = pd.read_csv(path)
    return df

def prepare_features_targets(df, target_col='voc_total'):
    """
    Separate features and target.
    Assumes the target column is 'voc_total' or similar.
    """
    if target_col not in df.columns:
        # Fallback: find a column that looks like a target if standard name missing
        possible_targets = [c for c in df.columns if 'voc' in c.lower() and c != 'sample_id']
        if not possible_targets:
            raise ValueError(f"Target column '{target_col}' not found and no VOC columns detected.")
        target_col = possible_targets[0]
    
    X = df.drop(columns=[target_col, 'sample_id'] if 'sample_id' in df.columns else [target_col])
    y = df[target_col]
    
    # Ensure all features are numeric
    X = X.apply(pd.to_numeric, errors='coerce')
    
    return X, y, target_col

def run_nested_cv(X, y, n_splits=5, random_state=42):
    """
    Run Nested k-Fold Cross-Validation.
    Inner loop: GridSearchCV for hyperparameter tuning.
    Outer loop: Evaluation of the tuned model.
    """
    outer_kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    param_grid = {
        'regressor__n_estimators': [100, 200],
        'regressor__max_depth': [None, 10, 20],
        'regressor__min_samples_split': [2, 5]
    }
    
    # Define the pipeline with imputation and scaling
    pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(random_state=random_state, n_jobs=-1))
    ])
    
    inner_kf = KFold(n_splits=3, shuffle=True, random_state=random_state)
    
    best_scores = []
    best_models = []
    
    print("Starting Nested Cross-Validation...")
    
    for fold, (train_idx, test_idx) in enumerate(outer_kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Inner loop: Grid Search
        grid_search = GridSearchCV(
            pipe, 
            param_grid, 
            cv=inner_kf, 
            scoring='r2', 
            n_jobs=-1,
            refit=True
        )
        
        grid_search.fit(X_train, y_train)
        
        # Evaluate on outer test set
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)
        score = r2_score(y_test, y_pred)
        
        best_scores.append(score)
        best_models.append(best_model)
        
        print(f"Fold {fold+1}/{n_splits} - Outer R²: {score:.4f}")
    
    avg_r2 = np.mean(best_scores)
    std_r2 = np.std(best_scores)
    
    # Train final model on full data using best params found
    # Note: In a strict nested CV, we report the CV score. 
    # For artifact saving, we retrain on full data with the best params found.
    final_params = grid_search.best_params_
    final_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(random_state=random_state, n_jobs=-1))
    ])
    final_pipe.set_params(**final_params)
    final_pipe.fit(X, y)
    
    return final_pipe, avg_r2, std_r2, best_models

def save_model(model, model_path):
    """
    Save the trained model artifact to the specified path.
    Implements T024.
    """
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {path}")
    return path

def save_metrics(metrics, metrics_path):
    """Save model metrics to JSON."""
    path = Path(metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics saved to {path}")

def main():
    """Main entry point for the training pipeline."""
    print("Loading processed data...")
    df = load_processed_data()
    
    print("Preparing features and targets...")
    X, y, target_col = prepare_features_targets(df)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target vector shape: {y.shape}")
    
    # Run Nested CV
    model, avg_r2, std_r2, _ = run_nested_cv(X, y)
    
    # Prepare metrics
    metrics = {
        "algorithm": "Random Forest Regressor",
        "cross_validation": {
            "type": "Nested k-Fold",
            "outer_folds": 5,
            "inner_folds": 3,
            "r2_mean": float(avg_r2),
            "r2_std": float(std_r2)
        },
        "hyperparameters": model.named_steps['regressor'].get_params()
    }
    
    # Save Metrics (T023)
    metrics_path = Path("data/results/model_metrics.json")
    save_metrics(metrics, metrics_path)
    
    # Save Model (T024)
    model_path = Path("data/models/random_forest.pkl")
    save_model(model, model_path)
    
    print("Training complete.")

if __name__ == "__main__":
    main()