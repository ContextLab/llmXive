import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd

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

def compute_baseline_distribution(y: np.ndarray) -> dict:
    """
    Compute the majority class predictor baseline distribution.
    
    Args:
        y: Array of labels
        
    Returns:
        dict: Baseline distribution information
    """
    unique, counts = np.unique(y, return_counts=True)
    majority_class = unique[np.argmax(counts)]
    majority_count = np.max(counts)
    total_count = len(y)
    
    baseline_dist = {
        "majority_class": int(majority_class),
        "majority_count": int(majority_count),
        "total_count": int(total_count),
        "majority_ratio": float(majority_count / total_count)
    }
    
    return baseline_dist

def save_baseline_distribution(baseline_dist: dict, output_path: str):
    """
    Save baseline distribution to a JSON file.
    
    Args:
        baseline_dist: Dictionary containing baseline distribution
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_dist, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Compute majority class predictor baseline.")
    parser.add_argument("--train_path", type=str, default="data/processed/filtered_train.csv", help="Path to filtered training data")
    parser.add_argument("--output_path", type=str, default="data/processed/baseline_f1.json", help="Path to save baseline distribution")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    logging.info(f"Loading training data from {args.train_path}")
    X_train, y_train, _ = load_filtered_data(args.train_path)
    
    # Compute baseline
    baseline_dist = compute_baseline_distribution(y_train)
    
    # Save baseline
    save_baseline_distribution(baseline_dist, args.output_path)
    
    logging.info(f"Saved baseline distribution to {args.output_path}")
    print(f"Baseline distribution saved to {args.output_path}")
    print(f"Majority class: {baseline_dist['majority_class']}, Ratio: {baseline_dist['majority_ratio']:.2f}")

if __name__ == "__main__":
    main()
