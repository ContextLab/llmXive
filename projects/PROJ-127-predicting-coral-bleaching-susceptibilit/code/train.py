import os
import sys
import json
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

import config

def load_data(data_path: str) -> pd.DataFrame:
    """Load the unified reef-species dataset."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(path)

def spatial_split(df: pd.DataFrame, train_region: str = "Western Pacific", test_region: str = "Eastern Pacific") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data spatially based on region.
    Returns (train_df, test_df).
    """
    # Assuming 'region' column exists in the dataset
    if 'region' not in df.columns:
        raise ValueError("Dataset must contain a 'region' column for spatial splitting.")
    
    train_df = df[df['region'] == train_region].copy()
    test_df = df[df['region'] == test_region].copy()
    
    if train_df.empty:
        warnings.warn(f"No data found for training region: {train_region}")
    if test_df.empty:
        warnings.warn(f"No data found for test region: {test_region}")
        
    return train_df, test_df

def train_model(train_df: pd.DataFrame, target_col: str = "bleaching_label") -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Train an XGBoost model with hyperparameter tuning (simplified for this task).
    Returns (model, params).
    """
    if target_col not in train_df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    X = train_df.drop(columns=[target_col])
    y = train_df[target_col]
    
    # Simplified hyperparameters for the task context
    params = {
        'max_depth': 5,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'random_state': config.SEED,
        'eval_metric': 'auc'
    }
    
    model = xgb.XGBClassifier(**params)
    model.fit(X, y)
    
    return model, params

def evaluate_model(model: xgb.XGBClassifier, test_df: pd.DataFrame, target_col: str = "bleaching_label") -> Dict[str, Any]:
    """
    Evaluate the model on the test set.
    Handles the edge case where the test set has zero positive events.
    """
    if target_col not in test_df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test dataset.")
    
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]
    
    # Check for zero positive events (edge case from T024)
    positive_count = y_test.sum()
    total_count = len(y_test)
    
    metrics = {
        "test_samples": total_count,
        "positive_events": int(positive_count),
        "negative_events": int(total_count - positive_count)
    }
    
    if positive_count == 0:
        warnings.warn("Test set has zero positive events. Skipping ROC-AUC calculation.")
        metrics["ROC_AUC"] = None
        # Still generate predictions for other potential metrics if needed later
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        metrics["predictions_generated"] = True
    else:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        try:
            auc_score = roc_auc_score(y_test, y_pred_proba)
            metrics["ROC_AUC"] = float(auc_score)
        except Exception as e:
            warnings.warn(f"Failed to calculate ROC-AUC: {e}")
            metrics["ROC_AUC"] = None
    
    return metrics

def save_results(results: Dict[str, Any], output_path: str):
    """Save evaluation results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_path}")

def main():
    """Main execution flow for training and evaluation."""
    data_path = config.DATA_PROCESSED / "reef_species_unified.csv"
    output_path = config.DATA_MODELS / "results.json"
    
    print("Loading data...")
    df = load_data(str(data_path))
    
    print("Performing spatial split...")
    train_df, test_df = spatial_split(df)
    
    if train_df.empty or test_df.empty:
        print("ERROR: Spatial split resulted in empty train or test sets.")
        sys.exit(1)
    
    print("Training model...")
    model, params = train_model(train_df)
    
    print("Evaluating model...")
    eval_results = evaluate_model(model, test_df)
    
    # Combine model params and eval results
    final_results = {
        "model_params": params,
        "evaluation_metrics": eval_results
    }
    
    print("Saving results...")
    save_results(final_results, str(output_path))
    
    return final_results

if __name__ == "__main__":
    main()