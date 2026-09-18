"""
Evaluate trained static models on the test set.

This script loads the trained static models (Decision Tree/Logistic Regression)
from data/intermediate/models/seeds/ and evaluates them on the test split
of the merged dataset. It computes precision, recall, F1-score, and accuracy
for each seed and saves the results to data/intermediate/static_eval_scores.json.

Input:
    - data/intermediate/merged_dataset.csv (from T014)
    - data/intermediate/models/seeds/*.pkl (from T019)

Output:
    - data/intermediate/static_eval_scores.json
"""

import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_merged_dataset(filepath: str) -> pd.DataFrame:
    """Load the merged dataset from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Merged dataset not found at {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded merged dataset with {len(df)} rows and {len(df.columns)} columns")
    return df


def load_model(model_path: str):
    """Load a trained model from pickle file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}: {type(model).__name__}")
    return model


def evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a single model on test data.
    
    Returns a dictionary with precision, recall, F1, and accuracy.
    """
    y_pred = model.predict(X_test)
    
    # Handle edge case: if all predictions are the same class, some metrics may fail
    try:
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        accuracy = accuracy_score(y_test, y_pred)
    except Exception as e:
        logger.warning(f"Error computing metrics: {e}. Returning zeros.")
        precision = 0.0
        recall = 0.0
        f1 = 0.0
        accuracy = 0.0
    
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "accuracy": float(accuracy)
    }


def prepare_features_and_labels(df: pd.DataFrame, feature_cols: List[str], label_col: str = "rtpurbo_label"):
    """
    Prepare feature matrix and labels from the merged dataset.
    
    Splits into train/test sets using stratified sampling.
    """
    # Drop rows with missing values in feature columns or label
    df_clean = df.dropna(subset=feature_cols + [label_col])
    
    X = df_clean[feature_cols].values
    y = df_clean[label_col].values.astype(int)
    
    # Stratified split: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    logger.info(f"Class distribution in test: {np.bincount(y_test)}")
    
    return X_test, y_test


def find_model_files(seeds_dir: str) -> List[str]:
    """Find all model files in the seeds directory."""
    if not os.path.exists(seeds_dir):
        raise FileNotFoundError(f"Seeds directory not found at {seeds_dir}")
    
    model_files = []
    for filename in os.listdir(seeds_dir):
        if filename.endswith('.pkl'):
            model_files.append(os.path.join(seeds_dir, filename))
    
    model_files.sort()
    logger.info(f"Found {len(model_files)} model files in {seeds_dir}")
    return model_files


def main(args):
    """Main evaluation pipeline."""
    # Paths
    merged_dataset_path = args.merged_dataset
    seeds_dir = args.seeds_dir
    output_path = args.output_path
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load merged dataset
    logger.info(f"Loading merged dataset from {merged_dataset_path}")
    df = load_merged_dataset(merged_dataset_path)
    
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ['doc_id', 'token_id', 'position', 'rtpurbo_label']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    logger.info(f"Using {len(feature_cols)} feature columns: {feature_cols[:5]}...")
    
    # Prepare test data
    logger.info("Preparing test data...")
    X_test, y_test = prepare_features_and_labels(df, feature_cols)
    
    # Find all model files
    model_files = find_model_files(seeds_dir)
    if not model_files:
        raise ValueError(f"No model files found in {seeds_dir}")
    
    # Evaluate each model
    results = []
    for model_path in model_files:
        seed_name = os.path.basename(model_path).replace('.pkl', '')
        logger.info(f"Evaluating model: {seed_name}")
        
        try:
            model = load_model(model_path)
            metrics = evaluate_model(model, X_test, y_test)
            metrics["seed"] = seed_name
            metrics["model_file"] = os.path.basename(model_path)
            results.append(metrics)
            logger.info(f"  Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}, F1: {metrics['f1']:.4f}")
        except Exception as e:
            logger.error(f"Error evaluating {model_path}: {e}")
            results.append({
                "seed": seed_name,
                "model_file": os.path.basename(model_path),
                "precision": None,
                "recall": None,
                "f1": None,
                "accuracy": None,
                "error": str(e)
            })
    
    # Save results
    output_data = {
        "num_models_evaluated": len(results),
        "test_set_size": len(y_test),
        "evaluations": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Evaluation complete. Results saved to {output_path}")
    return output_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate static models on test set")
    parser.add_argument(
        "--merged_dataset",
        type=str,
        default="data/intermediate/merged_dataset.csv",
        help="Path to merged dataset CSV"
    )
    parser.add_argument(
        "--seeds_dir",
        type=str,
        default="data/intermediate/models/seeds",
        help="Directory containing trained model files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/intermediate/static_eval_scores.json",
        help="Output path for evaluation scores JSON"
    )
    
    args = parser.parse_args()
    main(args)