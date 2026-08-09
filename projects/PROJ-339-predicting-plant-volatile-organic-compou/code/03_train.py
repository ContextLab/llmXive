import os
import sys
import json
import pickle
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# Ensure project root is in path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config
from utils.validation import generate_validation_report

def load_processed_data(config):
    """Load the merged dataset from the processed data directory."""
    input_path = Path(config['paths']['processed_data']) / "merged_dataset.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {input_path}. Run T017 first.")
    return pd.read_csv(input_path)

def prepare_features_targets(df, config):
    """Separate features (X) and target (y) based on configuration."""
    target_col = config['model']['target_column']
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    # Drop non-numeric columns and the target for features
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c != target_col]
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    return X, y, feature_cols

def run_nested_cv(X, y, config):
    """
    Perform Nested k-Fold Cross-Validation.
    Inner loop: Hyperparameter tuning via GridSearchCV.
    Outer loop: Evaluation of the tuned model.
    Returns the best estimator (fitted on full data for saving) and metrics history.
    """
    # Configuration
    outer_folds = config['model']['outer_folds']
    inner_folds = config['model']['inner_folds']
    param_grid = config['model']['param_grid']
    random_state = config['model']['random_state']
    
    # Base model
    base_model = RandomForestRegressor(random_state=random_state, n_jobs=-1)
    
    # Imputation and Scaling pipeline to prevent leakage
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('regressor', base_model)
    ])
    
    # Outer CV
    outer_kf = KFold(n_splits=outer_folds, shuffle=True, random_state=random_state)
    
    outer_scores = []
    best_models_per_fold = []
    
    print(f"Starting Nested CV with {outer_folds} outer folds and {inner_folds} inner folds...")
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_kf.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Inner CV for hyperparameter tuning
        inner_kf = KFold(n_splits=inner_folds, shuffle=True, random_state=random_state)
        
        grid_search = GridSearchCV(
            pipeline,
            param_grid,
            cv=inner_kf,
            scoring='r2',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        
        # Evaluate best model on outer test set
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        outer_scores.append({'r2': r2, 'rmse': rmse})
        best_models_per_fold.append(best_model)
        
        print(f"Outer Fold {fold_idx + 1}/{outer_folds}: R²={r2:.4f}, RMSE={rmse:.4f}")
    
    # Calculate mean metrics
    mean_r2 = np.mean([s['r2'] for s in outer_scores])
    mean_rmse = np.mean([s['rmse'] for s in outer_scores])
    
    # Train final model on the ENTIRE dataset using the best parameters found
    # This is the model we will save for inference
    final_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(
            **grid_search.best_params_, 
            random_state=random_state, 
            n_jobs=-1
        ))
    ])
    final_pipeline.fit(X, y)
    
    return final_pipeline, {
        'mean_r2': float(mean_r2),
        'mean_rmse': float(mean_rmse),
        'fold_scores': outer_scores,
        'best_params': grid_search.best_params_
    }

def save_model(model, config):
    """Save the trained model artifact to the specified path."""
    output_dir = Path(config['paths']['models'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "random_forest.pkl"
    
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {output_path}")
    return output_path

def save_metrics(metrics, config):
    """Save model metrics to the results directory."""
    output_dir = Path(config['paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "model_metrics.json"
    
    # Add disclaimer
    metrics['disclaimer'] = "Findings are associational due to observational data."
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics saved to {output_path}")
    return output_path

def main():
    """Main entry point for the training pipeline."""
    config = get_config()
    
    try:
        # 1. Load Data
        print("Loading processed data...")
        df = load_processed_data(config)
        
        # 2. Prepare Features and Targets
        print("Preparing features and targets...")
        X, y, feature_names = prepare_features_targets(df, config)
        
        # 3. Run Nested CV and Train Final Model
        print("Running Nested Cross-Validation...")
        final_model, metrics = run_nested_cv(X, y, config)
        
        # 4. Save Model Artifact (T024)
        model_path = save_model(final_model, config)
        
        # 5. Save Metrics
        metrics_path = save_metrics(metrics, config)
        
        print("Training pipeline completed successfully.")
        return {
            'model_path': str(model_path),
            'metrics_path': str(metrics_path)
        }
        
    except Exception as e:
        print(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()