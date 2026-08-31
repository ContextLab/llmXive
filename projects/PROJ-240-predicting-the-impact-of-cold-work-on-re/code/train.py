import json
import os
import sys
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def load_final_dataset(input_path: str) -> pd.DataFrame:
    """Load the final dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def split_data(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data into train and test sets."""
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    return train_df, test_df

def train_model(X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    return {'mae': mae, 'r2': r2}

def save_model(model: RandomForestRegressor, output_path: str):
    """Save trained model to disk."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"Saved model to {output_path}")

def save_metrics(metrics: Dict[str, Any], output_path: str):
    """Save metrics to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {output_path}")

def run_training_pipeline(input_path: str, model_output_path: str, metrics_output_path: str):
    """Run the full training pipeline."""
    print(f"Loading data from {input_path}...")
    df = load_final_dataset(input_path)
    
    # Define features and target
    # Exclude target and non-feature columns if any
    feature_cols = [col for col in df.columns if col not in ['time_to_peak']]
    target_col = 'time_to_peak'
    
    X = df[feature_cols]
    y = df[target_col]
    
    print("Splitting data...")
    train_df, test_df = split_data(df)
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    print("Training model...")
    model = train_model(X_train, y_train)
    
    print("Evaluating model on test set...")
    test_metrics = evaluate_model(model, X_test, y_test)
    
    print("Performing cross-validation...")
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=kfold, scoring='r2')
    cv_mean_r2 = float(cv_scores.mean())
    cv_std_r2 = float(cv_scores.std())
    
    # Prepare full metrics
    full_metrics = {
        'cv_mean_r2': cv_mean_r2,
        'cv_std_r2': cv_std_r2,
        'test_mae': float(test_metrics['mae']),
        'test_r2': float(test_metrics['r2'])
    }
    
    print("Saving model...")
    save_model(model, model_output_path)
    
    print("Saving metrics...")
    save_metrics(full_metrics, metrics_output_path)
    
    return full_metrics

def main():
    """Main entry point for training."""
    input_path = 'data/processed/final_dataset.csv'
    model_output_path = 'artifacts/models/kinetic_model.pkl'
    metrics_output_path = 'artifacts/reports/training_metrics.json'
    
    run_training_pipeline(input_path, model_output_path, metrics_output_path)

if __name__ == "__main__":
    main()
