"""
Train predictive models on structural features to determine the need for dynamic execution.
Implements Logistic Regression and Random Forest models (CPU-only).
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings

# Suppress specific warnings for cleaner output during training
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
FEATURES_FILE = PROCESSED_DIR / "features.csv"

# Random seed for reproducibility
RANDOM_SEED = 42

def load_features() -> pd.DataFrame:
    """Load the features dataset generated in previous steps."""
    if not FEATURES_FILE.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_FILE}. "
                                "Please run feature extraction tasks (T019-T024) first.")
    
    df = pd.read_csv(FEATURES_FILE)
    
    # Ensure required columns exist
    required_cols = ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 
                     'semantic_complexity_score', 'dynamic_execution_outcome']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features file: {missing_cols}")
    
    # Handle 'Unparseable' tasks if present (they should have been filtered or marked)
    # For training, we typically exclude unparseable tasks or handle them specifically.
    # Assuming 'dynamic_execution_outcome' contains 'Pass', 'Fail', 'Timeout', 'Unparseable'
    # We will filter out 'Unparseable' for model training as they lack structural metrics.
    parseable_mask = df['dynamic_execution_outcome'] != 'Unparseable'
    df = df[parseable_mask].reset_index(drop=True)
    
    if df.empty:
        raise ValueError("No parseable tasks found in features dataset for training.")
    
    return df

def prepare_train_val_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into training and validation sets with fixed random seed.
    Target variable: 'need_dynamic' derived from 'dynamic_execution_outcome'.
    """
    # Define target: 1 if outcome is 'Fail' or 'Timeout' (needs dynamic check), 0 if 'Pass'
    # This aligns with the goal: predict if static analysis is insufficient (i.e., dynamic needed)
    # If the outcome is 'Fail' or 'Timeout', we assume dynamic execution was necessary to catch it.
    # If 'Pass', static might have been sufficient (or it passed anyway).
    # We map: Pass -> 0 (No dynamic needed), Fail/Timeout -> 1 (Dynamic needed)
    
    def map_target(outcome: str) -> int:
        if outcome in ['Fail', 'Timeout']:
            return 1
        elif outcome == 'Pass':
            return 0
        else:
            # Should be filtered out already, but just in case
            return -1

    df['need_dynamic'] = df['dynamic_execution_outcome'].apply(map_target)
    
    # Remove any rows where mapping failed (should be none after filtering)
    df = df[df['need_dynamic'] != -1].reset_index(drop=True)
    
    if len(df) < 2:
        raise ValueError("Insufficient data for train/val split.")

    # Features to use for training
    feature_cols = ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 'semantic_complexity_score']
    # Ensure no NaNs in features
    df = df.dropna(subset=feature_cols)
    
    X = df[feature_cols].values
    y = df['need_dynamic'].values
    
    # Split with fixed seed
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y if len(np.unique(y)) > 1 else None
    )
    
    return X_train, X_val, y_train, y_val

def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """Train a Logistic Regression model (CPU-only)."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train model with fixed seed
    model = LogisticRegression(
        random_state=RANDOM_SEED, 
        max_iter=1000, 
        solver='lbfgs',
        class_weight='balanced' # Handle potential class imbalance
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_val_scaled)
    report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)
    
    metrics = {
        'model_type': 'LogisticRegression',
        'val_f1': report['weighted avg']['f1-score'],
        'val_accuracy': report['accuracy'],
        'coef': model.coef_.tolist(),
        'intercept': model.intercept_.tolist(),
        'feature_names': ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 'semantic_complexity_score']
    }
    
    return model, metrics

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> Tuple[Any, Dict[str, float]]:
    """Train a Random Forest model (CPU-only)."""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train model with fixed seed
    model = RandomForestClassifier(
        n_estimators=100, 
        random_state=RANDOM_SEED, 
        n_jobs=1, # CPU only, single job for reproducibility in this context
        class_weight='balanced'
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_val_scaled)
    report = classification_report(y_val, y_pred, output_dict, zero_division=0)
    
    metrics = {
        'model_type': 'RandomForest',
        'val_f1': report['weighted avg']['f1-score'],
        'val_accuracy': report['accuracy'],
        'feature_importances': model.feature_importances_.tolist(),
        'feature_names': ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 'semantic_complexity_score']
    }
    
    return model, metrics

def evaluate_model(model: Any, X_val: np.ndarray, y_val: np.ndarray, model_type: str) -> Dict[str, Any]:
    """Perform detailed evaluation including confusion matrix."""
    y_pred = model.predict(X_val)
    cm = confusion_matrix(y_val, y_pred)
    report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)
    
    # Calculate False Negative Rate (FNR)
    # FNR = FN / (FN + TP)
    # In our binary classification: 1 = Fail/Timeout (Need Dynamic), 0 = Pass
    # False Negative: Predicted 0 (Pass) but actual was 1 (Fail/Timeout) -> Critical for safety
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return {
        'model_type': model_type,
        'confusion_matrix': {'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)},
        'false_negative_rate': float(fnr),
        'classification_report': report
    }

def calculate_correlation_coefficient(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, float]:
    """Calculate Pearson correlation between each feature and the target."""
    correlations = {}
    for col in feature_cols:
        if col in df.columns and target_col in df.columns:
            corr = df[col].corr(df[target_col])
            correlations[col] = float(corr) if not np.isnan(corr) else 0.0
    return correlations

def run_training_pipeline():
    """Main execution pipeline for model training."""
    print(f"Loading features from {FEATURES_FILE}...")
    df = load_features()
    print(f"Loaded {len(df)} parseable tasks.")
    
    print("Preparing train/validation split...")
    X_train, X_val, y_train, y_val = prepare_train_val_split(df)
    print(f"Training set size: {len(y_train)}, Validation set size: {len(y_val)}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    results = {
        'random_seed': RANDOM_SEED,
        'dataset_size': len(df),
        'train_size': len(y_train),
        'val_size': len(y_val),
        'models': {}
    }
    
    # Train Logistic Regression
    print("\nTraining Logistic Regression...")
    lr_model, lr_metrics = train_logistic_regression(X_train, y_train, X_val, y_val)
    lr_eval = evaluate_model(lr_model, X_val_scaled, y_val, 'LogisticRegression')
    results['models']['LogisticRegression'] = {**lr_metrics, **lr_eval}
    print(f"LR F1: {lr_metrics['val_f1']:.4f}, FNR: {lr_eval['false_negative_rate']:.4f}")
    
    # Train Random Forest
    print("\nTraining Random Forest...")
    rf_model, rf_metrics = train_random_forest(X_train, y_train, X_val, y_val)
    rf_eval = evaluate_model(rf_model, X_val_scaled, y_val, 'RandomForest')
    results['models']['RandomForest'] = {**rf_metrics, **rf_eval}
    print(f"RF F1: {rf_metrics['val_f1']:.4f}, FNR: {rf_eval['false_negative_rate']:.4f}")
    
    # Calculate correlations
    feature_cols = ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 'semantic_complexity_score']
    df['need_dynamic'] = df['dynamic_execution_outcome'].apply(lambda x: 1 if x in ['Fail', 'Timeout'] else 0)
    correlations = calculate_correlation_coefficient(df, feature_cols, 'need_dynamic')
    results['feature_correlations'] = correlations
    print("\nFeature Correlations:", correlations)
    
    # Save results
    results_file = PROCESSED_DIR / "model_training_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nTraining results saved to {results_file}")
    
    # Save best model (Random Forest usually performs better on this type of data)
    # We will save the RF model and the scaler
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "decision_boundary.pkl"
    
    model_artifact = {
        'model': rf_model,
        'scaler': scaler,
        'model_type': 'RandomForest',
        'best_f1': rf_metrics['val_f1'],
        'fnr': rf_eval['false_negative_rate']
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_artifact, f)
    print(f"Best model saved to {model_path}")
    
    return results

def main():
    """Entry point for the script."""
    try:
        run_training_pipeline()
        print("\nTraining pipeline completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
