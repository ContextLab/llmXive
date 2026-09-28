"""
Train predictive models to determine the need for dynamic execution based on structural features.

This script loads the processed features dataset, splits it into training and validation sets,
trains Logistic Regression and Random Forest models, and evaluates their performance.
All operations are CPU-only with fixed random seeds for reproducibility.
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings

# Suppress specific sklearn warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Constants
RANDOM_SEED = 42
TARGET_COLUMN = "dynamic_execution_outcome"
FEATURE_COLUMNS = [
    "dependency_depth",
    "cyclomatic_complexity",
    "lines_of_code",
    "semantic_complexity_score"
]
# Map outcome labels to binary: 1 = Need Dynamic (Fail/Timeout), 0 = Pass
# Based on FR-003 and FR-005 context: we predict "Need Dynamic Execution" (i.e., likely to fail or timeout)
# "Pass" -> 0 (Safe to skip dynamic? Or rather, outcome is known safe)
# "Fail", "Timeout", "Unparseable" -> 1 (Need dynamic/inspection)
# Note: The specific mapping logic depends on the exact definition of "Need Dynamic".
# Assuming: We want to predict if the task will NOT pass (Fail/Timeout/Unparseable).
LABEL_MAPPING = {
    "Pass": 0,
    "Fail": 1,
    "Timeout": 1,
    "Unparseable": 1
}

def load_features(csv_path: str) -> pd.DataFrame:
    """Load the features CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found at {csv_path}")
    df = pd.read_csv(path)
    return df

def prepare_train_val_split(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataframe into training and validation sets.
    Uses a fixed random seed for reproducibility.
    """
    # Ensure target column exists
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in features.")
    
    # Filter out rows where target is not mappable (e.g., empty strings) if any
    valid_mask = df[TARGET_COLUMN].isin(LABEL_MAPPING.keys())
    df_valid = df[valid_mask].copy()
    
    if len(df_valid) == 0:
        raise ValueError("No valid rows found for training after filtering.")

    train_df, val_df = train_test_split(
        df_valid, 
        test_size=test_size, 
        random_state=RANDOM_SEED, 
        stratify=df_valid[TARGET_COLUMN]
    )
    return train_df, val_df

def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """Train a Logistic Regression model."""
    model = LogisticRegression(
        random_state=RANDOM_SEED, 
        max_iter=1000, 
        solver='lbfgs',
        class_weight='balanced' # Handle potential class imbalance
    )
    model.fit(X_train, y_train)
    return model

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """Train a Random Forest model."""
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_SEED,
        class_weight='balanced',
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray, model_name: str) -> Dict[str, Any]:
    """Evaluate model performance and return metrics."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    report = classification_report(y_test, y_pred, output_dict=True)
    metrics = {
        "model_name": model_name,
        "f1_score": f1_score(y_test, y_pred),
        "accuracy": report["accuracy"],
        "precision": report["1"]["precision"],
        "recall": report["1"]["recall"],
        "fpr": 1 - report["0"]["recall"], # False Positive Rate for class 0
    }
    
    if y_proba is not None:
        try:
            metrics["roc_auc"] = roc_auc_score(y_test, y_proba)
        except ValueError:
            metrics["roc_auc"] = None # Handle case with only one class

    return metrics

def calculate_correlation_coefficient(features_df: pd.DataFrame, target_series: pd.Series) -> float:
    """
    Calculate the correlation coefficient between structural features and execution necessity.
    Returns the average absolute correlation across all numeric features.
    """
    # Select only numeric columns that are in the feature list
    numeric_features = features_df.select_dtypes(include=[np.number]).columns
    correlations = []
    
    for col in numeric_features:
        if col != TARGET_COLUMN:
            corr = features_df[col].corr(target_series)
            if not np.isnan(corr):
                correlations.append(abs(corr))
    
    return np.mean(correlations) if correlations else 0.0

def run_training_pipeline(csv_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Main pipeline: Load data, split, train models, evaluate, and save results.
    """
    print(f"Loading features from {csv_path}...")
    df = load_features(csv_path)
    
    # Prepare data
    print("Preparing train/validation split...")
    train_df, val_df = prepare_train_val_split(df)
    
    # Map labels
    train_df['label'] = train_df[TARGET_COLUMN].map(LABEL_MAPPING)
    val_df['label'] = val_df[TARGET_COLUMN].map(LABEL_MAPPING)
    
    # Prepare features and targets
    # Ensure all feature columns exist
    missing_cols = [c for c in FEATURE_COLUMNS if c not in train_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df['label'].values
    X_val = val_df[FEATURE_COLUMNS].values
    y_val = val_df['label'].values
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train models
    print("Training Logistic Regression...")
    lr_model = train_logistic_regression(X_train_scaled, y_train)
    
    print("Training Random Forest...")
    rf_model = train_random_forest(X_train_scaled, y_train)
    
    # Evaluate
    print("Evaluating models...")
    lr_metrics = evaluate_model(lr_model, X_val_scaled, y_val, "LogisticRegression")
    rf_metrics = evaluate_model(rf_model, X_val_scaled, y_val, "RandomForest")
    
    # Calculate correlation
    corr_coef = calculate_correlation_coefficient(df, df['label'])
    
    # Save artifacts
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save models and scaler
    with open(output_path / "logistic_regression.pkl", "wb") as f:
        pickle.dump(lr_model, f)
    with open(output_path / "random_forest.pkl", "wb") as f:
        pickle.dump(rf_model, f)
    with open(output_path / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    
    # Save metrics report
    report = {
        "random_seed": RANDOM_SEED,
        "train_size": len(train_df),
        "val_size": len(val_df),
        "logistic_regression": lr_metrics,
        "random_forest": rf_metrics,
        "correlation_coefficient": float(corr_coef),
        "feature_columns": FEATURE_COLUMNS,
        "label_mapping": LABEL_MAPPING
    }
    
    report_path = output_path / "model_training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Training complete. Report saved to {report_path}")
    print(f"Logistic Regression F1: {lr_metrics['f1_score']:.4f}")
    print(f"Random Forest F1: {rf_metrics['f1_score']:.4f}")
    
    return report

def main():
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    features_path = project_root / "data" / "processed" / "features.csv"
    models_dir = project_root / "models"
    
    if not features_path.exists():
        print(f"Error: Features file not found at {features_path}")
        sys.exit(1)
    
    run_training_pipeline(str(features_path), str(models_dir))

if __name__ == "__main__":
    main()