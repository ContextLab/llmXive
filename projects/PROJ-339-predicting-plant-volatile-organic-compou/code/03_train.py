"""
Training pipeline for VOC prediction (US2).
Implements Random Forest with Nested k-Fold Cross-Validation.
"""
import os
import sys
import json
import pickle
import warnings
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, GridSearchCV, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Project root
ROOT = Path(__file__).resolve().parent.parent

def load_processed_data():
    """Load the merged and validated dataset."""
    path = ROOT / "data" / "processed" / "merged_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}")
    return pd.read_csv(path)

def prepare_features_targets(df):
    """
    Separate features (X) and target (y).
    Assumes 'target_voc' is the target column.
    """
    if 'target_voc' not in df.columns:
        raise ValueError("Dataset missing 'target_voc' column.")
    
    y = df['target_voc']
    X = df.drop(columns=['target_voc'])
    return X, y

def run_nested_cv(X, y, n_outer_folds=5, n_inner_folds=3, random_state=42):
    """
    Perform Nested k-Fold Cross-Validation.
    
    Outer loop: Evaluation
    Inner loop: Hyperparameter tuning
    
    Returns:
      outer_scores_r2: List of R2 scores from outer loop
      best_params: Best params found in inner loops (aggregated)
      final_model: The best model retrained on full data
    """
    warnings.filterwarnings('ignore')
    
    # Hyperparameter grid
    param_grid = {
        'regressor__n_estimators': [50, 100],
        'regressor__max_depth': [None, 10, 20],
        'regressor__min_samples_split': [2, 5]
    }
    
    # Base pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(random_state=random_state))
    ])
    
    outer_kf = KFold(n_splits=n_outer_folds, shuffle=True, random_state=random_state)
    inner_kf = KFold(n_splits=n_inner_folds, shuffle=True, random_state=random_state)
    
    outer_r2_scores = []
    all_best_params = []
    
    for train_idx, test_idx in outer_kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Inner loop: Grid Search
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=inner_kf, 
            scoring='r2', 
            n_jobs=-1
        )
        grid_search.fit(X_train, y_train)
        
        best_params = grid_search.best_params_
        all_best_params.append(best_params)
        
        # Evaluate on outer test set
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        outer_r2_scores.append(r2)
    
    # Retrain on full data with average best params
    # Simple heuristic: pick the most common n_estimators and max_depth
    # or just use the first one found if consistent. 
    # For robustness, we'll just retrain with the first found best params 
    # (in a real scenario, we might aggregate or use a consensus).
    # Here we assume parameters are stable or just pick the best from the last fold 
    # which is acceptable for this pipeline scope.
    final_params = all_best_params[-1]
    
    final_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(
            **{k: v for k, v in final_params.items() if k.startswith('regressor_')},
            random_state=random_state
        ))
    ])
    # Adjust keys for the pipeline
    final_pipeline.set_params(**final_params)
    
    final_pipeline.fit(X, y)
    
    return outer_r2_scores, final_params, final_pipeline

def save_model(model, path):
    """Save the trained model to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def save_metrics(r2_scores, rmse_scores, final_params, path):
    """
    Save model metrics to JSON.
    Includes the associational disclaimer as required by T025.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_rmse = float(np.mean(rmse_scores))
    std_rmse = float(np.std(rmse_scores))
    
    # T025: Inject associational disclaimer
    disclaimer_text = (
        "Findings are associational due to observational data. "
        "Correlations identified do not imply causation."
    )
    
    metrics = {
        "r2_score": mean_r2,
        "r2_std": std_r2,
        "rmse": mean_rmse,
        "rmse_std": std_rmse,
        "disclaimer": disclaimer_text,
        "model_type": "Random Forest Regressor",
        "cv_folds": 5,
        "best_params": final_params,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for the training pipeline."""
    print("Loading processed data...")
    df = load_processed_data()
    
    print("Preparing features and targets...")
    X, y = prepare_features_targets(df)
    
    print("Running Nested k-Fold Cross-Validation...")
    r2_scores, best_params, model = run_nested_cv(X, y)
    
    # Calculate RMSE for the outer folds to report
    # We need to re-run predictions on outer folds to get RMSEs consistent with R2s
    # For simplicity in this script, we'll do a quick re-eval on the full data 
    # or rely on the scores we have if we stored predictions. 
    # Since we didn't store all outer predictions in the function above, 
    # let's do a quick cross_val_score for RMSE to match the R2 logic.
    
    pipeline_base = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(random_state=42))
    ])
    pipeline_base.set_params(**best_params)
    
    # We need to compute RMSE for the same folds to be consistent.
    # Re-implementing the outer loop briefly to get paired predictions
    from sklearn.model_selection import KFold
    outer_kf = KFold(n_splits=5, shuffle=True, random_state=42)
    rmse_scores = []
    
    for train_idx, test_idx in outer_kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Clone and fit
        temp_model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(random_state=42))
        ])
        temp_model.set_params(**best_params)
        temp_model.fit(X_train, y_train)
        
        preds = temp_model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        rmse_scores.append(rmse)
    
    print(f"Mean R2: {np.mean(r2_scores):.4f} (+/- {np.std(r2_scores):.4f})")
    print(f"Mean RMSE: {np.mean(rmse_scores):.4f} (+/- {np.std(rmse_scores):.4f})")
    
    # Save artifacts
    model_path = ROOT / "data" / "models" / "random_forest.pkl"
    metrics_path = ROOT / "data" / "results" / "model_metrics.json"
    
    print(f"Saving model to {model_path}...")
    save_model(model, model_path)
    
    print(f"Saving metrics to {metrics_path}...")
    save_metrics(r2_scores, rmse_scores, best_params, metrics_path)
    
    print("Training complete.")

if __name__ == "__main__":
    main()
