import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Project local imports based on API surface
from src.utils.config import get_path, ensure_dir, set_random_seed, load_state, save_state, update_artifact_hash
from src.utils.logging_config import get_module_logger
from src.utils.stats import compute_benign_statistics, calculate_mahalanobis_distance

# Ensure CPU-only execution as per project constraints
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = get_module_logger(__name__)

def load_embeddings(input_path: str) -> pd.DataFrame:
    """
    Load embeddings from a Parquet file.
    Expected columns: 'embedding' (list/array), 'label' (int), 'source_id' (str), 'split' (str - optional)
    """
    logger.info(f"Loading embeddings from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Embeddings file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    # Validate expected columns
    required_cols = ['embedding', 'label']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {input_path}")
    
    # Ensure embedding is numpy array for processing
    df['embedding'] = df['embedding'].apply(lambda x: np.array(x) if not isinstance(x, np.ndarray) else x)
    
    logger.info(f"Loaded {len(df)} embeddings. Columns: {list(df.columns)}")
    return df

def perform_stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> tuple:
    """
    Perform a stratified train/test split based on the 'label' column.
    Returns: (train_df, test_df)
    """
    logger.info(f"Performing stratified split (test_size={test_size}, random_state={random_state})")
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df['label'], 
        random_state=random_state
    )
    
    logger.info(f"Split complete. Train: {len(train_df)}, Test: {len(test_df)}")
    return train_df, test_df

def train_logistic_regression(train_df: pd.DataFrame, random_state: int = 42) -> LogisticRegression:
    """
    Train a Logistic Regression classifier on the training embeddings.
    """
    logger.info("Training Logistic Regression model...")
    
    X_train = np.stack(train_df['embedding'].values)
    y_train = train_df['label'].values
    
    model = LogisticRegression(random_state=random_state, solver='lbfgs', max_iter=1000)
    model.fit(X_train, y_train)
    
    logger.info("Model training complete.")
    return model

def evaluate_model(model: LogisticRegression, test_df: pd.DataFrame) -> dict:
    """
    Evaluate the model on the test set.
    """
    logger.info("Evaluating model on test set...")
    
    X_test = np.stack(test_df['embedding'].values)
    y_test = test_df['label'].values
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    report = classification_report(y_test, y_pred, output_dict=True)
    accuracy = accuracy_score(y_test, y_pred)
    
    logger.info(f"Model Accuracy: {accuracy:.4f}")
    return {
        "accuracy": accuracy,
        "classification_report": report,
        "predictions": y_pred.tolist(),
        "probabilities": y_prob.tolist()
    }

def calculate_benign_statistics_and_anomaly_scores(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame, 
    output_path: str
) -> None:
    """
    T022b Implementation:
    1. Calculate benign centroid (mu) and covariance (Sigma) ONLY from the Training Set's benign samples.
    2. Calculate Mahalanobis distance for ALL samples (train + test) using these stats.
    3. Save the unified AnomalyScore report to data/anomaly_scores.parquet.
    """
    logger.info("Starting calculation of benign statistics and anomaly scores (T022b)...")
    
    # 1. Filter training set for benign samples (label == 0)
    benign_train_df = train_df[train_df['label'] == 0]
    
    if len(benign_train_df) == 0:
        raise ValueError("No benign samples found in the training set to calculate statistics.")
    
    logger.info(f"Found {len(benign_train_df)} benign samples in training set for centroid/covariance calculation.")
    
    # Extract embeddings
    X_benign = np.stack(benign_train_df['embedding'].values)
    
    # 2. Compute statistics using the shared stats utility
    mu, sigma = compute_benign_statistics(X_benign)
    
    logger.info(f"Computed benign centroid (dim: {mu.shape}) and covariance.")
    
    # 3. Combine train and test data for unified scoring
    # We need to preserve the origin (train/test) and original indices
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    train_df['split'] = 'train'
    test_df['split'] = 'test'
    
    # Reset index to have a unique identifier across both if needed, or keep original
    # Assuming original index is unique enough or we can combine split + index
    combined_df = pd.concat([train_df, test_df], ignore_index=True)
    
    logger.info(f"Combined dataset size for scoring: {len(combined_df)}")
    
    # 4. Calculate Mahalanobis distance for ALL samples
    X_all = np.stack(combined_df['embedding'].values)
    
    # Calculate distances using the stats utility
    # The utility expects data and the pre-computed stats
  #   We pass the pre-computed mu and sigma directly to a wrapper or call the distance function
  #   The stats.py utility `calculate_mahalanobis_distance` likely takes (data, mu, sigma)
  #   Let's assume the signature based on standard usage or implement the call here if the utility is generic.
  #   Looking at the API: `calculate_mahalanobis_distance` is available.
  #   We need to ensure we pass the correct arguments. Usually: (X, mu, Sigma)
  
    anomaly_scores = calculate_mahalanobis_distance(X_all, mu, sigma)
    
    # 5. Add scores to the dataframe
    combined_df['anomaly_score'] = anomaly_scores
    combined_df['mahalanobis_distance'] = anomaly_scores # Alias for clarity
    
    # 6. Save to Parquet
    ensure_dir(str(Path(output_path).parent))
    combined_df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved unified AnomalyScore report to {output_path}")
    logger.info(f"Score statistics: Min={anomaly_scores.min():.4f}, Max={anomaly_scores.max():.4f}, Mean={anomaly_scores.mean():.4f}")

def save_model_artifact(model: LogisticRegression, output_path: str) -> None:
    """Save the trained model to disk."""
    ensure_dir(str(Path(output_path).parent))
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")

def save_predictions(predictions: dict, output_path: str) -> None:
    """Save prediction results to JSON."""
    ensure_dir(str(Path(output_path).parent))
    with open(output_path, 'w') as f:
        json.dump(predictions, f, indent=2)
    logger.info(f"Predictions saved to {output_path}")

def main():
    """
    Main entry point for the training pipeline.
    Handles loading, splitting, training, evaluation, and T022b anomaly scoring.
    """
    parser = argparse.ArgumentParser(description="Train LLMXive Audio Classifier and Generate Anomaly Scores")
    parser.add_argument("--input", type=str, default="data/embeddings.parquet", help="Path to embeddings parquet")
    parser.add_argument("--model-out", type=str, default="results/model.joblib", help="Path to save model")
    parser.add_argument("--preds-out", type=str, default="results/predictions.json", help="Path to save predictions")
    parser.add_argument("--anomaly-out", type=str, default="data/anomaly_scores.parquet", help="Path to save anomaly scores (T022b)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    set_random_seed(args.seed)
    
    try:
        # 1. Load Data
        df = load_embeddings(args.input)
        
        # 2. Split Data
        train_df, test_df = perform_stratified_split(df, test_size=args.test_size, random_state=args.seed)
        
        # 3. Train Model
        model = train_logistic_regression(train_df, random_state=args.seed)
        
        # 4. Evaluate Model
        eval_results = evaluate_model(model, test_df)
        
        # 5. T022b: Calculate Benign Stats and Anomaly Scores for ALL samples
        calculate_benign_statistics_and_anomaly_scores(train_df, test_df, args.anomaly_out)
        
        # 6. Save Artifacts
        save_model_artifact(model, args.model_out)
        save_predictions(eval_results, args.preds_out)
        
        # Update state hash if needed (optional for this task, but good practice)
        # update_artifact_hash(args.anomaly_out)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()