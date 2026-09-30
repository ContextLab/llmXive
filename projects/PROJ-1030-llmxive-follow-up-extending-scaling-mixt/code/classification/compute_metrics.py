import os
import sys
import json
import logging
import argparse
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

def load_filtered_data(train_path: str, test_path: str = None) -> tuple:
    """
    Load filtered training and test data.
    
    Args:
        train_path: Path to filtered training CSV
        test_path: Path to filtered test CSV (optional)
        
    Returns:
        tuple: (X, y, feature_names) or (X_train, y_train, X_test, y_test, feature_names)
    """
    df = pd.read_csv(train_path)
    
    # Assume 'label' is the target column
    if 'label' not in df.columns:
        raise ValueError("Column 'label' not found in the data file.")
    
    feature_cols = [col for col in df.columns if col != 'label']
    X = df[feature_cols].values
    y = df['label'].values
    feature_names = feature_cols
    
    if test_path:
        df_test = pd.read_csv(test_path)
        if 'label' not in df_test.columns:
            raise ValueError("Column 'label' not found in the test data file.")
        X_test = df_test[feature_cols].values
        y_test = df_test['label'].values
        return X, y, X_test, y_test, feature_names
    
    return X, y, feature_names

def load_baseline_distribution(baseline_path: str) -> dict:
    """
    Load baseline distribution from a JSON file.
    
    Args:
        baseline_path: Path to baseline JSON file
        
    Returns:
        dict: Baseline distribution
    """
    with open(baseline_path, 'r') as f:
        return json.load(f)

def load_classifier(model_path: str):
    """
    Load a trained classifier from a pickle file.
    
    Args:
        model_path: Path to the pickle file
        
    Returns:
        dict: Dictionary containing model, scaler, and feature names
    """
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    return model_data

def calculate_majority_baseline(y_test: np.ndarray, baseline_dist: dict) -> float:
    """
    Calculate the F1 score of the majority class predictor on the test set.
    
    Args:
        y_test: Test labels
        baseline_dist: Baseline distribution dictionary
        
    Returns:
        float: F1 score of majority class predictor
    """
    majority_class = baseline_dist["majority_class"]
    y_pred = np.full_like(y_test, majority_class)
    return f1_score(y_test, y_pred, average='binary')

def compute_metrics(model, X_test: np.ndarray, y_test: np.ndarray, scaler: StandardScaler) -> dict:
    """
    Compute evaluation metrics for the model.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        scaler: Scaler used for training
        
    Returns:
        dict: Dictionary containing metrics
    """
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    
    metrics = {
        "f1": float(f1_score(y_test, y_pred, average='binary')),
        "precision": float(precision_score(y_test, y_pred, average='binary')),
        "recall": float(recall_score(y_test, y_pred, average='binary'))
    }
    
    return metrics

def run_metrics_evaluation(model_data: dict, X_test: np.ndarray, y_test: np.ndarray, baseline_dist: dict) -> dict:
    """
    Run full metrics evaluation including baseline comparison.
    
    Args:
        model_data: Dictionary containing model, scaler, and feature names
        X_test: Test features
        y_test: Test labels
        baseline_dist: Baseline distribution
        
    Returns:
        dict: Evaluation results
    """
    model = model_data["model"]
    scaler = model_data["scaler"]
    
    model_metrics = compute_metrics(model, X_test, y_test, scaler)
    baseline_f1 = calculate_majority_baseline(y_test, baseline_dist)
    
    evaluation_results = {
        "model_metrics": model_metrics,
        "baseline_f1": float(baseline_f1),
        "improvement_over_baseline": float(model_metrics["f1"] - baseline_f1)
    }
    
    return evaluation_results

def main():
    parser = argparse.ArgumentParser(description="Compute evaluation metrics and compare with baseline.")
    parser.add_argument("--train_path", type=str, default="data/processed/filtered_train.csv", help="Path to filtered training data")
    parser.add_argument("--test_path", type=str, default="data/processed/filtered_test.csv", help="Path to filtered test data")
    parser.add_argument("--model_path", type=str, default="data/processed/classifier.pkl", help="Path to trained model")
    parser.add_argument("--baseline_path", type=str, default="data/processed/baseline_f1.json", help="Path to baseline distribution")
    parser.add_argument("--output_path", type=str, default="data/processed/evaluation_metrics.json", help="Path to save evaluation metrics")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    logging.info(f"Loading data from {args.train_path} and {args.test_path}")
    X_train, y_train, X_test, y_test, feature_names = load_filtered_data(args.train_path, args.test_path)
    
    # Load model
    logging.info(f"Loading model from {args.model_path}")
    model_data = load_classifier(args.model_path)
    
    # Load baseline
    logging.info(f"Loading baseline from {args.baseline_path}")
    baseline_dist = load_baseline_distribution(args.baseline_path)
    
    # Run evaluation
    logging.info("Running evaluation...")
    evaluation_results = run_metrics_evaluation(model_data, X_test, y_test, baseline_dist)
    
    # Save results
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, indent=2)
    
    logging.info(f"Saved evaluation metrics to {args.output_path}")
    print(f"Evaluation metrics saved to {args.output_path}")
    print(f"Model F1: {evaluation_results['model_metrics']['f1']:.2f}, Baseline F1: {evaluation_results['baseline_f1']:.2f}")

if __name__ == "__main__":
    main()
