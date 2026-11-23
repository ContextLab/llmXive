"""
T019d: Calculate Top-K Accuracy and Prediction Entropy for polymorphism handling.

This module computes:
1. Top-K Accuracy (K=5) for the Space Group classification task to handle
   polymorphism ambiguity (multiple valid space groups for a molecule).
2. Prediction Entropy for the Space Group classification to measure
   model uncertainty/ambiguity in predictions.

Output: data/results/polymorphism_metrics.json
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import from project API surface
from config import get_path_results, ensure_directory, get_path_data
from logging_config import get_logger
from exceptions import DownloadError, MemoryErrorHandled

# Import evaluation utilities if needed, or implement directly
# We assume the model and split indices are already available as per T016
from sklearn.metrics import top_k_accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import Ridge
import joblib
import pandas as pd

def load_model(model_path: str):
    """Load a trained model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    return joblib.load(model_path)

def load_split_indices(splits_path: str) -> Dict[str, List[int]]:
    """Load the train/test split indices."""
    if not os.path.exists(splits_path):
        raise FileNotFoundError(f"Split indices not found at {splits_path}")
    with open(splits_path, 'r') as f:
        return json.load(f)

def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the processed dataset."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    return pd.read_csv(dataset_path)

def extract_features_targets(df: pd.DataFrame, feature_cols: List[str], target_col: str, indices: List[int]):
    """Extract features and targets for a specific set of indices."""
    subset = df.iloc[indices]
    X = subset[feature_cols].values
    y = subset[target_col].values
    return X, y

def calculate_topk_accuracy(y_true: np.ndarray, y_pred_proba: np.ndarray, k: int = 5) -> float:
    """
    Calculate Top-K Accuracy.
    y_pred_proba must be probability estimates (output of predict_proba).
    """
    # Ensure y_true is 1D and y_pred_proba is 2D
    if len(y_true.shape) > 1 and y_true.shape[1] == 1:
        y_true = y_true.flatten()
    
    # scikit-learn's top_k_accuracy_score requires labels to be integers
    # and handles the calculation efficiently.
    try:
        score = top_k_accuracy_score(y_true, y_pred_proba, k=k, labels=None)
        return float(score)
    except Exception as e:
        logging.error(f"Error calculating top-k accuracy: {e}")
        raise

def calculate_prediction_entropy(y_pred_proba: np.ndarray) -> float:
    """
    Calculate the average prediction entropy.
    Entropy H(p) = - sum(p * log(p)) for each sample, averaged over all samples.
    Higher entropy indicates higher uncertainty/ambiguity.
    """
    # Clip probabilities to avoid log(0)
    epsilon = 1e-10
    y_pred_proba_clipped = np.clip(y_pred_proba, epsilon, 1.0 - epsilon)
    
    # Calculate entropy for each sample
    entropies = -np.sum(y_pred_proba_clipped * np.log(y_pred_proba_clipped), axis=1)
    
    # Return average entropy
    return float(np.mean(entropies))

def run_polymorphism_metrics(
    model_path: str,
    dataset_path: str,
    splits_path: str,
    output_path: str,
    k: int = 5
) -> Dict[str, Any]:
    """
    Main function to calculate Top-K Accuracy and Prediction Entropy.
    """
    logger = get_logger(__name__)
    logger.info("Starting polymorphism metrics calculation.")

    # 1. Load Data
    logger.info(f"Loading model from {model_path}")
    model = load_model(model_path)
    
    logger.info(f"Loading dataset from {dataset_path}")
    df = load_dataset(dataset_path)
    
    logger.info(f"Loading split indices from {splits_path}")
    splits = load_split_indices(splits_path)
    test_indices = splits['test']

    # 2. Identify columns
    # Assuming the dataset has a 'fingerprint' column (string representation of list) 
    # or separate columns for bits. Based on T013/T014, it's likely a CSV with 
    # fingerprint bits as columns or a single serialized column.
    # Let's assume the standard format from T013: fingerprint bits are columns 'fp_0' to 'fp_N'
    # or a single column 'fingerprint' that needs parsing.
    # Given T011/T012, let's assume the CSV has 'fingerprint' as a string or list.
    # We need to be robust. Let's look for columns starting with 'fp_' or 'bit_'.
    possible_fp_cols = [c for c in df.columns if c.startswith('fp_') or c.startswith('bit_')]
    
    if not possible_fp_cols:
        # Fallback: check if there's a 'fingerprint' column that needs parsing
        if 'fingerprint' in df.columns:
            # This might be a serialized list string. We'd need to parse it.
            # For now, let's assume the pipeline output T013 produced individual bit columns.
            # If not, we raise an error as the data format is unexpected.
            raise ValueError("Could not find fingerprint bit columns. Expected columns starting with 'fp_' or 'bit_'.")
        else:
            raise ValueError("No fingerprint columns found in dataset.")

    feature_cols = possible_fp_cols
    target_col = 'space_group' # Standard target for classification

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # 3. Extract Test Data
    logger.info(f"Extracting test data ({len(test_indices)} samples)")
    X_test, y_test = extract_features_targets(df, feature_cols, target_col, test_indices)

    # 4. Get Predictions
    logger.info("Generating predictions and probabilities")
    if isinstance(model, RandomForestClassifier):
        y_pred_proba = model.predict_proba(X_test)
    elif isinstance(model, Ridge):
        # Ridge is for regression. For polymorphism metrics (classification), 
        # we focus on the Space Group model (RF).
        logger.warning("Ridge model detected. Skipping classification metrics for this model.")
        return {"status": "skipped", "reason": "Regression model provided"}
    else:
        # Try to call predict_proba generically
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_test)
        else:
            raise TypeError(f"Model type {type(model)} does not support predict_proba.")

    # 5. Calculate Metrics
    logger.info("Calculating Top-K Accuracy")
    topk_acc = calculate_topk_accuracy(y_test, y_pred_proba, k=k)

    logger.info("Calculating Prediction Entropy")
    pred_entropy = calculate_prediction_entropy(y_pred_proba)

    # 6. Compile Results
    results = {
        "task_id": "T019d",
        "k": k,
        "metrics": {
            "top_k_accuracy": topk_acc,
            "prediction_entropy": pred_entropy
        },
        "dataset_info": {
            "total_samples": len(df),
            "test_samples": len(test_indices),
            "num_classes": len(np.unique(y_test)),
            "num_features": len(feature_cols)
        },
        "model_info": {
            "type": type(model).__name__,
            "path": model_path
        },
        "interpretation": {
            "top_k_accuracy_desc": f"Probability that the true space group is in the top {k} predictions. Higher is better.",
            "prediction_entropy_desc": "Average uncertainty of the model's predictions. Lower is better (more confident)."
        }
    }

    # 7. Save Output
    ensure_directory(output_path)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Polymorphism metrics saved to {output_path}")
    return results

def main():
    """Entry point for the script."""
    logger = get_logger(__name__)
    
    # Paths
    dataset_path = get_path_data("processed/crystal_dataset.csv")
    splits_path = get_path_data("processed/split_indices.json")
    model_path = get_path_data("models/rf_model.pkl") # Assuming RF is the primary classifier
    output_path = get_path_results("polymorphism_metrics.json")

    try:
        results = run_polymorphism_metrics(
            model_path=model_path,
            dataset_path=dataset_path,
            splits_path=splits_path,
            output_path=output_path,
            k=5
        )
        print(json.dumps(results, indent=2))
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error calculating polymorphism metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()