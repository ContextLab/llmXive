import os
import sys
import json
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import roc_auc_score, classification_report
import xgboost as xgb

import config
from features import compute_lagged_features, compute_interaction_features, check_definitional_circularity, calculate_vif, filter_high_vif

def load_data() -> pd.DataFrame:
    """Load the unified dataset from data/processed/reef_species_unified.csv."""
    input_path = Path(config.DATA_PROCESSED) / "reef_species_unified.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {input_path}. Run ingestion first.")
    df = pd.read_csv(input_path)
    
    # Ensure date column is datetime if it exists
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Drop rows with missing target if any
    if 'bleaching_label' in df.columns:
        df = df.dropna(subset=['bleaching_label'])
    
    return df

def spatial_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data spatially: Western Pacific (Train) vs Eastern Pacific (Test).
    Uses longitude as a proxy for geographic split.
    """
    # Define split threshold (approximate date line / 180 meridian logic for Pacific)
    # Western Pacific: Longitude < -150 (or > 150 depending on convention, assuming -180 to 180)
    # Let's assume standard -180 to 180:
    # West Pacific: 100E to 180 (100 to 180)
    # East Pacific: 180 to 80W (-180 to -80)
    # A simple split point often used in these datasets is around 150W (-150) or 160E.
    # Let's use a clear split: Train = Longitude > -150 (West/Indian), Test = Longitude <= -150 (East Pacific)
    # Adjust based on actual data distribution if needed, but this is a robust heuristic.
    
    train_mask = df['longitude'] > -150
    test_mask = ~train_mask

    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()

    print(f"Spatial Split: Train (West) rows: {len(train_df)}, Test (East) rows: {len(test_df)}")
    
    if len(train_df) == 0 or len(test_df) == 0:
        raise ValueError("Spatial split resulted in an empty set. Check longitude values.")
    
    return train_df, test_df

def train_model(train_df: pd.DataFrame) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Train XGBoost model with 5-fold CV for hyperparameter tuning.
    """
    # Define features and target
    # Assuming 'bleaching_label' is the target
    target_col = 'bleaching_label'
    
    # Select features: drop non-feature columns
    feature_cols = [c for c in train_df.columns if c not in [target_col, 'date', 'reef_id', 'species_id']]
    
    X = train_df[feature_cols].fillna(0)
    y = train_df[target_col]

    # Define parameter grid
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.05, 0.1, 0.2],
        'n_estimators': [100, 200, 500],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    base_model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=config.RANDOM_SEED,
        use_label_encoder=False
    )

    # Grid Search with 5-fold CV
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=5,
        scoring='roc_auc',
        n_jobs=-1,
        verbose=1
    )

    print("Starting Hyperparameter Tuning...")
    grid_search.fit(X, y)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    print(f"Best CV Score: {grid_search.best_score_:.4f}")
    print(f"Best Params: {best_params}")

    return best_model, best_params

def evaluate_model(model: xgb.XGBClassifier, test_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluate model on the test set.
    Handles edge case: zero positive events in test set.
    """
    target_col = 'bleaching_label'
    feature_cols = [c for c in test_df.columns if c not in [target_col, 'date', 'reef_id', 'species_id']]
    
    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df[target_col]

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(classification_report(y_test, y_pred, output_dict=True)['accuracy']),
        "precision": float(classification_report(y_test, y_pred, output_dict=True)['precision']),
        "recall": float(classification_report(y_test, y_pred, output_dict=True)['recall']),
        "f1": float(classification_report(y_test, y_pred, output_dict=True)['f1-score'])
    }

    # Edge Case: Zero Positive Events
    n_positives = int(y_test.sum())
    
    if n_positives == 0:
        warnings.warn("TEST SET EDGE CASE: Zero positive events found in the test set. Skipping ROC-AUC calculation.")
        metrics["roc_auc"] = None
    else:
        # Calculate ROC-AUC only if there are both positive and negative samples
        n_negatives = int(len(y_test) - n_positives)
        if n_positives > 0 and n_negatives > 0:
            try:
                auc_score = roc_auc_score(y_test, y_prob)
                metrics["roc_auc"] = float(auc_score)
            except ValueError as e:
                warnings.warn(f"Could not calculate ROC-AUC: {e}")
                metrics["roc_auc"] = None
        else:
            # Should be covered by n_positives == 0 check, but safe guard for all negatives
            warnings.warn("TEST SET EDGE CASE: No positive events in test set. Skipping ROC-AUC.")
            metrics["roc_auc"] = None

    return metrics

def save_results(metrics: Dict[str, Any], best_params: Dict[str, Any], output_path: Path):
    """Save evaluation results and best parameters to JSON."""
    results = {
        "best_params": best_params,
        "metrics": metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_path}")

def main():
    """Main execution function for the training pipeline."""
    print("Starting Training Pipeline (T024 Edge Case Handling)...")
    
    # Load Data
    df = load_data()
    
    # Spatial Split
    train_df, test_df = spatial_split(df)
    
    # Train Model
    model, best_params = train_model(train_df)
    
    # Evaluate Model (includes T024 logic)
    metrics = evaluate_model(model, test_df)
    
    # Save Results
    output_path = Path(config.RESULTS_DIR) / "results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_results(metrics, best_params, output_path)
    
    print("Training Pipeline Complete.")
    return metrics

if __name__ == "__main__":
    main()