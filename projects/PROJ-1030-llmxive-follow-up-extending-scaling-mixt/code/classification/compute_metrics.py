import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_majority_baseline(y_true: np.ndarray) -> float:
    """
    Calculate the F1-score of a majority-class predictor.
    This serves as the 'random guessing' baseline for binary classification.
    
    Args:
        y_true: Array of true labels (0 or 1)
        
    Returns:
        F1-score of the majority-class predictor
    """
    if len(y_true) == 0:
        return 0.0
        
    # Determine majority class
    majority_class = 1 if np.sum(y_true) > len(y_true) / 2 else 0
    
    # Create predictions (all majority class)
    y_pred_majority = np.full_like(y_true, majority_class)
    
    # Calculate F1-score
    return f1_score(y_true, y_pred_majority)

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_scores: np.ndarray = None) -> dict:
    """
    Compute standard classification metrics.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_scores: Predicted probabilities (optional, for AUC)
        
    Returns:
        Dictionary of metrics
    """
    metrics = {
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1': f1_score(y_true, y_pred),
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
    }
    
    if y_scores is not None:
        from sklearn.metrics import roc_auc_score
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_scores)
        except ValueError:
            # Handle case where only one class is present
            metrics['roc_auc'] = None
    
    return metrics

def run_metrics_evaluation(
    features_path: str,
    labels_path: str,
    model_path: str,
    metrics_output_path: str,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Run the full metrics evaluation pipeline.
    
    Args:
        features_path: Path to features.npy
        labels_path: Path to labels.csv
        model_path: Path to trained classifier.pkl
        metrics_output_path: Path to save metrics.json
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
    """
    logger.info(f"Loading features from {features_path}")
    features = np.load(features_path, allow_pickle=True)
    
    logger.info(f"Loading labels from {labels_path}")
    labels_df = pd.read_csv(labels_path)
    
    # Filter out null labels (as per T030 requirement)
    valid_labels = labels_df[labels_df['label'] != 'null']
    if len(valid_labels) == 0:
        raise ValueError("No valid labels found after filtering null values.")
    
    # Extract clip IDs and labels
    clip_ids = valid_labels['clip_id'].values
    y_true = valid_labels['label'].map({'valid': 1, 'invalid': 0}).values
    
    # Ensure features and labels are aligned by clip_id
    # Assuming features.npy contains a structure with clip_ids and feature vectors
    if isinstance(features, dict):
        clip_ids_features = features['clip_ids']
        X = features['features']
    else:
        # If features is just a numpy array, we assume it's already filtered
        # and in the same order as valid_labels
        X = features
        clip_ids_features = clip_ids
    
    # Create a mapping from clip_id to feature index
    clip_id_to_idx = {cid: idx for idx, cid in enumerate(clip_ids_features)}
    
    # Filter features to only include those with valid labels
    valid_indices = [clip_id_to_idx[cid] for cid in clip_ids if cid in clip_id_to_idx]
    X = X[valid_indices]
    y_true = y_true[:len(valid_indices)]
    
    logger.info(f"Dataset size: {len(X)} samples")
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_true, test_size=test_size, random_state=random_state, stratify=y_true
    )
    
    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
    
    # Load the trained model
    logger.info(f"Loading model from {model_path}")
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Get prediction probabilities if available
    y_scores = None
    if hasattr(model, 'predict_proba'):
        y_scores = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = compute_metrics(y_test, y_pred, y_scores)
    
    # Calculate majority class baseline
    baseline_f1 = calculate_majority_baseline(y_test)
    metrics['majority_baseline_f1'] = baseline_f1
    metrics['improvement_over_baseline'] = metrics['f1'] - baseline_f1
    
    # Add test set information
    metrics['test_set_size'] = len(y_test)
    metrics['test_set_positive_ratio'] = float(np.mean(y_test))
    
    # Save metrics
    logger.info(f"Saving metrics to {metrics_output_path}")
    os.makedirs(os.path.dirname(metrics_output_path), exist_ok=True)
    with open(metrics_output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Metrics evaluation completed successfully")
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Compute classification metrics")
    parser.add_argument("--features", type=str, required=True, help="Path to features.npy")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels.csv")
    parser.add_argument("--model", type=str, required=True, help="Path to trained classifier.pkl")
    parser.add_argument("--output", type=str, required=True, help="Path to save metrics.json")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set proportion")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    try:
        run_metrics_evaluation(
            features_path=args.features,
            labels_path=args.labels,
            model_path=args.model,
            metrics_output_path=args.output,
            test_size=args.test_size,
            random_state=args.random_state
        )
    except Exception as e:
        logger.error(f"Metrics evaluation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()