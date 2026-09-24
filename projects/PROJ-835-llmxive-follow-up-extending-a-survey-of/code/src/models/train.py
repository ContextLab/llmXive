import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.covariance import LedoitWolf

# Import project utilities from existing API surface
from src.utils.config import set_random_seed, get_path, ensure_dir, load_state, save_state
from src.utils.logging_config import get_logger, get_module_logger
from src.utils.stats import compute_benign_statistics, calculate_mahalanobis_distance

# Setup logging
logger = get_module_logger(__name__)

def load_embeddings(parquet_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load embeddings and labels from a Parquet file.
    
    Args:
        parquet_path: Path to the embeddings parquet file.
        
    Returns:
        Tuple of (embeddings_array, labels_array)
    """
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Embeddings file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    # Assuming the dataframe has 'embedding' (list/array) and 'label' columns
    # If 'embedding' is stored as a string representation of a list, we need to parse it
    if isinstance(df['embedding'].iloc[0], str):
        df['embedding'] = df['embedding'].apply(lambda x: np.fromstring(x.strip('[]'), sep=' '))
    
    embeddings = np.vstack(df['embedding'].values)
    labels = df['label'].values.astype(int)
    
    logger.info(f"Loaded {len(labels)} samples with embedding dimension {embeddings.shape[1]}")
    return embeddings, labels

def perform_stratified_split(
    embeddings: np.ndarray, 
    labels: np.ndarray, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform a stratified train/test split.
    
    Args:
        embeddings: Array of shape (n_samples, n_features)
        labels: Array of shape (n_samples,)
        test_size: Proportion of samples for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    
    logger.info(f"Split complete: Train={len(y_train)}, Test={len(y_test)}")
    logger.info(f"Train class distribution: {np.bincount(y_train)}")
    logger.info(f"Test class distribution: {np.bincount(y_test)}")
    
    return X_train, X_test, y_train, y_test

def train_logistic_regression(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    random_state: int = 42,
    max_iter: int = 1000
) -> LogisticRegression:
    """
    Train a Logistic Regression classifier on CPU.
    
    Args:
        X_train: Training features
        y_train: Training labels
        random_state: Random seed
        max_iter: Maximum iterations for solver convergence
        
    Returns:
        Trained LogisticRegression model
    """
    logger.info("Training Logistic Regression model (CPU-only)...")
    
    model = LogisticRegression(
        random_state=random_state, 
        max_iter=max_iter,
        solver='lbfgs',
        n_jobs=-1  # Use all CPU cores
    )
    
    model.fit(X_train, y_train)
    
    logger.info(f"Model training complete. Coefficients shape: {model.coef_.shape}")
    logger.info(f"Intercept: {model.intercept_}")
    
    return model

def evaluate_model(
    model: LogisticRegression, 
    X_test: np.ndarray, 
    y_test: np.ndarray
) -> Dict[str, Any]:
    """
    Evaluate the trained model on the test set.
    
    Args:
        model: Trained LogisticRegression model
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary containing evaluation metrics
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    
    metrics = {
        "accuracy": report['accuracy'],
        "precision": report['1']['precision'],
        "recall": report['1']['recall'],
        "f1_score": report['1']['f1-score'],
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }
    
    logger.info(f"Test Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Test F1-Score: {metrics['f1_score']:.4f}")
    
    return metrics, y_pred, y_prob

def calculate_benign_statistics_and_anomaly_scores(
    X_train: np.ndarray, 
    y_train: np.ndarray,
    X_all: np.ndarray,
    y_all: np.ndarray
) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """
    Calculate benign centroid and covariance from training set,
    then compute Mahalanobis distance for ALL samples.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_all: All features (train + test) for anomaly scoring
        y_all: All labels
        
    Returns:
        Tuple of (benign_stats dict, anomaly_scores array)
    """
    # Filter benign samples from training set ONLY
    benign_mask = (y_train == 0)
    X_train_benign = X_train[benign_mask]
    
    if len(X_train_benign) == 0:
        raise ValueError("No benign samples found in training set for covariance estimation")
    
    logger.info(f"Computing statistics from {len(X_train_benign)} benign training samples...")
    
    benign_stats = compute_benign_statistics(X_train_benign)
    
    # Calculate Mahalanobis distance for ALL samples
    anomaly_scores = calculate_mahalanobis_distance(
        X_all, 
        benign_stats['mean'], 
        benign_stats['covariance']
    )
    
    logger.info(f"Computed anomaly scores for {len(anomaly_scores)} samples")
    logger.info(f"Anomaly score range: [{anomaly_scores.min():.4f}, {anomaly_scores.max():.4f}]")
    
    return benign_stats, anomaly_scores

def save_model_artifact(
    model: LogisticRegression, 
    metrics: Dict[str, Any], 
    benign_stats: Dict[str, np.ndarray],
    output_dir: str,
    filename: str = "model_artifact.json"
) -> str:
    """
    Save model coefficients, metrics, and benign statistics to a JSON file.
    
    Args:
        model: Trained LogisticRegression model
        metrics: Evaluation metrics dictionary
        benign_stats: Benign centroid and covariance statistics
        output_dir: Directory to save the artifact
        filename: Name of the output file
        
    Returns:
        Path to the saved artifact
    """
    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, filename)
    
    artifact = {
        "model_type": "LogisticRegression",
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_.tolist(),
        "metrics": metrics,
        "benign_statistics": {
            "mean": benign_stats['mean'].tolist(),
            "covariance": benign_stats['covariance'].tolist(),
            "n_samples": int(benign_stats['n_samples'])
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    
    logger.info(f"Model artifact saved to: {output_path}")
    return output_path

def save_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    anomaly_scores: np.ndarray,
    output_dir: str,
    filename: str = "predictions.csv"
) -> str:
    """
    Save predictions and probabilities to a CSV file.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_prob: Predicted probabilities (for positive class)
        anomaly_scores: Mahalanobis anomaly scores
        output_dir: Directory to save the CSV
        filename: Name of the output file
        
    Returns:
        Path to the saved CSV
    """
    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, filename)
    
    # Create DataFrame
    df = pd.DataFrame({
        "true_label": y_true,
        "predicted_label": y_pred,
        "predicted_prob_jailbreak": y_prob[:, 1],  # Probability of class 1
        "anomaly_score": anomaly_scores
    })
    
    df.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to: {output_path}")
    logger.info(f"Total predictions: {len(df)}")
    
    return output_path

def save_anomaly_scores(
    y_true: np.ndarray,
    anomaly_scores: np.ndarray,
    output_dir: str,
    filename: str = "anomaly_scores.parquet"
) -> str:
    """
    Save anomaly scores to a Parquet file.
    
    Args:
        y_true: True labels
        anomaly_scores: Mahalanobis anomaly scores
        output_dir: Directory to save the Parquet
        filename: Name of the output file
        
    Returns:
        Path to the saved Parquet
    """
    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, filename)
    
    df = pd.DataFrame({
        "label": y_true,
        "anomaly_score": anomaly_scores
    })
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Anomaly scores saved to: {output_path}")
    
    return output_path

def main():
    """
    Main entry point for the training pipeline.
    """
    parser = argparse.ArgumentParser(description="Train and evaluate jailbreak classifier")
    parser.add_argument("--embeddings_path", type=str, default="data/embeddings.parquet",
                        help="Path to embeddings parquet file")
    parser.add_argument("--output_dir", type=str, default="results",
                        help="Directory to save model artifacts and predictions")
    parser.add_argument("--test_size", type=float, default=0.2,
                        help="Proportion of data for testing")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed
    set_random_seed(args.seed)
    
    # Ensure output directories exist
    ensure_dir(args.output_dir)
    
    try:
        # 1. Load embeddings
        logger.info(f"Loading embeddings from {args.embeddings_path}...")
        embeddings, labels = load_embeddings(args.embeddings_path)
        
        # 2. Perform stratified split
        X_train, X_test, y_train, y_test = perform_stratified_split(
            embeddings, labels, test_size=args.test_size, random_state=args.seed
        )
        
        # 3. Train model
        model = train_logistic_regression(X_train, y_train, random_state=args.seed)
        
        # 4. Evaluate model
        metrics, y_pred_test, y_prob_test = evaluate_model(model, X_test, y_test)
        
        # 5. Calculate benign statistics and anomaly scores for ALL samples
        # Combine train and test for unified anomaly scoring
        X_all = np.vstack([X_train, X_test])
        y_all = np.concatenate([y_train, y_test])
        
        benign_stats, anomaly_scores_all = calculate_benign_statistics_and_anomaly_scores(
            X_train, y_train, X_all, y_all
        )
        
        # 6. Save model artifact
        model_path = save_model_artifact(
            model, metrics, benign_stats, args.output_dir, "model_artifact.json"
        )
        
        # 7. Save predictions (for test set only, but include anomaly scores for all)
        # Align anomaly scores with test set
        n_train = len(y_train)
        y_pred_test_full = y_pred_test
        y_prob_test_full = y_prob_test
        anomaly_scores_test = anomaly_scores_all[n_train:]
        
        predictions_path = save_predictions(
            y_test, y_pred_test_full, y_prob_test_full, anomaly_scores_test,
            args.output_dir, "predictions.csv"
        )
        
        # 8. Save anomaly scores for all samples
        anomaly_scores_path = save_anomaly_scores(
            y_all, anomaly_scores_all, args.output_dir, "anomaly_scores.parquet"
        )
        
        logger.info("Training pipeline completed successfully.")
        logger.info(f"Model artifact: {model_path}")
        logger.info(f"Predictions: {predictions_path}")
        logger.info(f"Anomaly scores: {anomaly_scores_path}")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
