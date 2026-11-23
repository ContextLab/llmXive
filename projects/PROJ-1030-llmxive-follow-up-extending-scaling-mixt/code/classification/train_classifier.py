import os
import sys
import json
import logging
import pickle
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
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

def encode_labels(y: np.ndarray) -> np.ndarray:
    """
    Encode labels if necessary (e.g., string to int).
    
    Args:
        y: Array of labels
        
    Returns:
        np.ndarray: Encoded labels
    """
    # Assuming labels are already integers or can be cast to int
    return y.astype(int)

def train_model(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, model_type: str = 'random_forest') -> tuple:
    """
    Train a classifier model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        model_type: Type of model to train ('random_forest' or 'mlp')
        
    Returns:
        tuple: (trained_model, scaler)
    """
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    if model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    elif model_type == 'mlp':
        model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    model.fit(X_train_scaled, y_train)
    
    return model, scaler

def load_classifier(model_path: str):
    """
    Load a trained classifier from a pickle file.
    
    Args:
        model_path: Path to the pickle file
        
    Returns:
        object: Loaded model
    """
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def main():
    parser = argparse.ArgumentParser(description="Train a classifier on filtered data.")
    parser.add_argument("--train_path", type=str, default="data/processed/filtered_train.csv", help="Path to filtered training data")
    parser.add_argument("--test_path", type=str, default="data/processed/filtered_test.csv", help="Path to filtered test data")
    parser.add_argument("--output_path", type=str, default="data/processed/classifier.pkl", help="Path to save trained model")
    parser.add_argument("--model_type", type=str, default="random_forest", choices=["random_forest", "mlp"], help="Type of model to train")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    logging.info(f"Loading data from {args.train_path} and {args.test_path}")
    X_train, y_train, X_test, y_test, feature_names = load_filtered_data(args.train_path, args.test_path)
    
    # Encode labels
    y_train = encode_labels(y_train)
    y_test = encode_labels(y_test)
    
    # Train model
    logging.info(f"Training {args.model_type} model...")
    model, scaler = train_model(X_train, y_train, X_test, y_test, args.model_type)
    
    # Save model and scaler together
    model_data = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names
    }
    
    with open(args.output_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logging.info(f"Saved trained model to {args.output_path}")
    print(f"Model trained and saved to {args.output_path}")

if __name__ == "__main__":
    main()
