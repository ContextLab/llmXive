"""
03_model_training.py

Implements the training of baseline models (Logistic Regression, Random Forest, Gradient Boosting)
on preprocessed datasets for fairness metric analysis.

This script adheres to the following constraints:
- Uses stratified train/test split with random_state=42.
- Trains models on CPU only.
- Saves models to data/processed/models/ with metadata.
- Includes FR-008 disclaimer in output.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import joblib

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROCESSED_DATA_DIR / "models"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"

# Constants
RANDOM_STATE = 42
TEST_SIZE = 0.2
FR_008_DISCLAIMER = "Findings are associational only; no causal claims are made."

# Model definitions
MODEL_CONFIGS = {
    "logistic_regression": {
        "class": LogisticRegression,
        "params": {"random_state": RANDOM_STATE, "max_iter": 1000, "solver": "lbfgs"}
    },
    "random_forest": {
        "class": RandomForestClassifier,
        "params": {"random_state": RANDOM_STATE, "n_estimators": 100, "n_jobs": 1} # CPU only
    },
    "gradient_boosting": {
        "class": GradientBoostingClassifier,
        "params": {"random_state": RANDOM_STATE, "n_estimators": 100}
    }
}

def log_header(message: str) -> None:
    """Prints a formatted log header with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def log_disclaimer() -> None:
    """Logs the FR-008 disclaimer."""
    print(f"\n--- {FR_008_DISCLAIMER} ---\n")

def load_processed_datasets() -> List[Dict[str, Any]]:
    """
    Loads all preprocessed CSV files from data/processed/.
    Returns a list of dicts containing 'df', 'dataset_id', 'path'.
    """
    datasets = []
    if not PROCESSED_DATA_DIR.exists():
        log_header(f"ERROR: Processed data directory not found: {PROCESSED_DATA_DIR}")
        return datasets

    for csv_file in PROCESSED_DATA_DIR.glob("*.csv"):
        # Skip the metrics file if it exists there (though it should be in analysis)
        if "metrics" in csv_file.name or "correlations" in csv_file.name:
            continue

        try:
            df = pd.read_csv(csv_file)
            # Derive dataset_id from filename (remove .csv)
            dataset_id = csv_file.stem
            
            # Verify required columns exist
            required_cols = ['protected_attr', 'outcome']
            if not all(col in df.columns for col in required_cols):
                log_header(f"WARNING: Skipping {csv_file.name} - missing required columns. Found: {list(df.columns)}")
                continue

            # Identify feature columns (exclude protected_attr, outcome, and any index-like columns)
            feature_cols = [c for c in df.columns if c not in ['protected_attr', 'outcome']]
            
            if len(feature_cols) == 0:
                log_header(f"WARNING: Skipping {csv_file.name} - no feature columns found.")
                continue

            datasets.append({
                "dataset_id": dataset_id,
                "df": df,
                "path": csv_file,
                "feature_cols": feature_cols,
                "protected_col": 'protected_attr',
                "outcome_col": 'outcome'
            })
        except Exception as e:
            log_header(f"ERROR: Failed to load {csv_file.name}: {e}")
    
    return datasets

def train_model(model_name: str, X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[Any, float]:
    """
    Trains a specific model and returns the trained object and test accuracy.
    """
    config = MODEL_CONFIGS[model_name]
    model = config["class"](**config["params"])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

def save_model(model: Any, model_id: str, model_type: str, dataset_id: str, accuracy: float) -> str:
    """
    Saves the model to disk and returns the file path.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"{model_id}.pkl"
    filepath = MODELS_DIR / filename
    
    # Save the model
    joblib.dump(model, filepath)
    
    # Create metadata
    metadata = {
        "model_id": model_id,
        "model_type": model_type,
        "dataset_id": dataset_id,
        "accuracy": accuracy,
        "random_state": RANDOM_STATE,
        "saved_at": datetime.now().isoformat(),
        "disclaimer": FR_008_DISCLAIMER
    }
    
    meta_path = filepath.with_suffix('.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Compute checksum of the model file
    checksum = hashlib.sha256(filepath.read_bytes()).hexdigest()
    
    log_header(f"Saved {model_type} for {dataset_id} -> {filename} (Accuracy: {accuracy:.4f}, SHA256: {checksum[:16]}...)")
    
    return str(filepath), checksum, str(meta_path)

def main():
    log_header("Starting Model Training Pipeline (T025)")
    log_disclaimer()

    # 1. Load processed datasets
    log_header("Loading preprocessed datasets...")
    datasets = load_processed_datasets()
    
    if not datasets:
        log_header("ERROR: No valid processed datasets found. Please run 02_preprocessing.py first.")
        sys.exit(1)
    
    log_header(f"Found {len(datasets)} datasets to process.")

    # 2. Train models
    all_results = []
    
    for ds in datasets:
        df = ds["df"]
        dataset_id = ds["dataset_id"]
        feature_cols = ds["feature_cols"]
        outcome_col = ds["outcome_col"]
        
        log_header(f"Processing dataset: {dataset_id} (Features: {len(feature_cols)})")
        
        X = df[feature_cols]
        y = df[outcome_col]
        
        # Ensure binary outcome for classification (handle potential multi-class by taking top 2 if needed, 
        # but spec implies binary outcomes. If not, we might need to binarize here or fail. 
        # Assuming binary based on T016 preprocessing step).
        if y.nunique() != 2:
            # Attempt to binarize if it's not binary but has 2 distinct values that might be strings?
            # Or fail if truly multi-class.
            # For safety, if >2 unique values, we might need to select a specific binary split or fail.
            # Given T016 ensures binary outcomes, we proceed. If not, this is a data issue.
            log_header(f"WARNING: Outcome for {dataset_id} has {y.nunique()} unique values. Proceeding anyway (sklearn will handle if binary, else error).")
        
        # Stratified split
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, 
                test_size=TEST_SIZE, 
                stratify=y, 
                random_state=RANDOM_STATE
            )
        except ValueError as e:
            # Fallback if stratify fails (e.g., class imbalance too high or only 1 class in split)
            log_header(f"WARNING: Stratified split failed for {dataset_id}: {e}. Falling back to random split.")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, 
                test_size=TEST_SIZE, 
                random_state=RANDOM_STATE
            )

        for model_name in MODEL_CONFIGS.keys():
            try:
                model, acc = train_model(model_name, X_train, y_train, X_test, y_test)
                model_id = f"{dataset_id}_{model_name}"
                path, checksum, meta_path = save_model(model, model_id, model_name, dataset_id, acc)
                
                all_results.append({
                    "model_id": model_id,
                    "dataset_id": dataset_id,
                    "model_type": model_name,
                    "path": path,
                    "checksum": checksum,
                    "meta_path": meta_path,
                    "accuracy": acc
                })
            except Exception as e:
                log_header(f"ERROR: Failed to train {model_name} on {dataset_id}: {e}")
    
    # 3. Update state file (optional but good practice per T017 style)
    # We are updating the artifact_hashes in the project state file
    log_header("Updating project state with new model checksums...")
    try:
        import yaml
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                state = yaml.safe_load(f) or {}
            if 'artifact_hashes' not in state:
                state['artifact_hashes'] = {}
            
            for res in all_results:
                # Store checksum under model_id
                state['artifact_hashes'][res['model_id']] = {
                    'checksum': res['checksum'],
                    'type': 'model',
                    'path': res['path']
                }
            
            with open(STATE_FILE, 'w') as f:
                yaml.dump(state, f, default_flow_style=False)
            log_header("State file updated successfully.")
        else:
            log_header(f"WARNING: State file not found at {STATE_FILE}. Skipping update.")
    except Exception as e:
        log_header(f"ERROR: Failed to update state file: {e}")

    log_header("Model Training Pipeline completed.")
    log_header(f"Total models trained: {len(all_results)}")
    log_disclaimer()

if __name__ == "__main__":
    main()