"""
03_model_training.py

Implements the model training pipeline for User Story 2.
- Loads processed datasets from data/processed/
- Performs stratified train/test split (random_state=42)
- Trains Logistic Regression, Random Forest, and Gradient Boosting models
- Saves trained models and metadata to data/processed/models/
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import joblib

# Add parent directory to path to allow imports from utils and other code modules
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import log_disclaimer
from data_model import Model, DatasetCharacteristic

# Constants
RANDOM_STATE = 42
MODEL_TYPES = [
    ("LogisticRegression", LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)),
    ("RandomForest", RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=100)),
    ("GradientBoosting", GradientBoostingClassifier(random_state=RANDOM_STATE, n_estimators=100)),
]
OUTPUT_DIR = Path("data/processed/models")
METADATA_FILE = OUTPUT_DIR / "model_metadata.json"

def log_header():
    """Print a formatted header to console."""
    print("\n" + "="*80)
    print("MODEL TRAINING PIPELINE")
    print("="*80 + "\n")

def get_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_datasets() -> Dict[str, pd.DataFrame]:
    """
    Load all processed datasets from data/processed/.
    Returns a dictionary mapping dataset_id to DataFrame.
    """
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {processed_dir}")

    datasets = {}
    for csv_file in processed_dir.glob("*.csv"):
        # Skip the models directory if it's scanned as a glob pattern
        if "models" in str(csv_file):
            continue

        dataset_id = csv_file.stem
        try:
            df = pd.read_csv(csv_file)
            # Basic validation: check for required columns
            required_cols = ['protected_attribute', 'outcome', 'prediction_target']
            # Note: prediction_target might be named differently based on preprocessing
            # We assume the outcome column is the target for now, or we look for 'outcome'
            if 'outcome' not in df.columns:
                print(f"Warning: Dataset {dataset_id} missing 'outcome' column. Skipping.")
                continue
            
            datasets[dataset_id] = df
            print(f"Loaded dataset: {dataset_id} ({len(df)} rows)")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")

    if not datasets:
        raise RuntimeError("No valid processed datasets found in data/processed/")

    return datasets

def train_model(
    model_type: str,
    model_obj,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    dataset_id: str
) -> Tuple[Any, float]:
    """
    Train a single model and return the trained model and accuracy.
    """
    model_obj.fit(X_train, y_train)
    y_pred = model_obj.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model_obj, accuracy

def save_model_and_metadata(
    model: Any,
    model_id: str,
    model_type: str,
    dataset_id: str,
    accuracy: float,
    input_file_checksum: str,
    metadata: Dict[str, Any]
):
    """
    Save the trained model and update the metadata file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = OUTPUT_DIR / f"{model_id}.joblib"
    joblib.dump(model, model_path)
    
    # Create metadata entry
    entry = {
        "model_id": model_id,
        "model_type": model_type,
        "dataset_id": dataset_id,
        "accuracy": accuracy,
        "input_file_checksum": input_file_checksum,
        "trained_at": datetime.now().isoformat(),
        "random_state": RANDOM_STATE,
        "metadata": metadata
    }

    # Load existing metadata or create new
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            all_metadata = json.load(f)
    else:
        all_metadata = []

    all_metadata.append(entry)

    with open(METADATA_FILE, 'w') as f:
        json.dump(all_metadata, f, indent=2)

    print(f"Saved model: {model_id} (Accuracy: {accuracy:.4f})")

def main():
    """
    Main execution flow for model training.
    """
    log_header()
    log_disclaimer()
    
    print("Loading processed datasets...")
    datasets = load_processed_datasets()
    
    print(f"Found {len(datasets)} datasets. Starting training loop...")
    
    total_models = 0
    for dataset_id, df in datasets.items():
        print(f"\n--- Processing Dataset: {dataset_id} ---")
        
        # Identify features and target
        # We assume all columns except 'protected_attribute' and 'outcome' are features
        # Or we use specific columns if defined in data_model
        exclude_cols = ['protected_attribute', 'outcome']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        if not feature_cols:
            print(f"Warning: No feature columns found in {dataset_id}. Skipping.")
            continue
        
        X = df[feature_cols]
        y = df['outcome']
        
        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
        )
        
        print(f"Split: {len(X_train)} train, {len(X_test)} test")
        
        # Calculate input file checksum for traceability
        input_file_path = Path("data/processed") / f"{dataset_id}.csv"
        input_checksum = get_file_checksum(input_file_path)
        
        metadata = {
            "n_train": len(X_train),
            "n_test": len(X_test),
            "n_features": len(feature_cols),
            "feature_columns": feature_cols
        }
        
        for model_type, model_obj in MODEL_TYPES:
            model_id = f"{dataset_id}_{model_type}"
            try:
                trained_model, accuracy = train_model(
                    model_type, model_obj, X_train, y_train, X_test, y_test, dataset_id
                )
                save_model_and_metadata(
                    trained_model, model_id, model_type, dataset_id, accuracy, input_checksum, metadata
                )
                total_models += 1
            except Exception as e:
                print(f"Error training {model_type} on {dataset_id}: {e}")
    
    print("\n" + "="*80)
    print(f"Training Complete. Total models saved: {total_models}")
    print(f"Metadata file: {METADATA_FILE}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()