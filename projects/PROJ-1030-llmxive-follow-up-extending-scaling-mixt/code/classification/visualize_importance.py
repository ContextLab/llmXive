import os
import sys
import json
import logging
import argparse
import numpy as np
import pickle
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path

def load_filtered_data_for_importance(train_path: str, test_path: str) -> tuple:
    """
    Load filtered training and test data for feature importance analysis.
    
    Args:
        train_path: Path to filtered training CSV
        test_path: Path to filtered test CSV
        
    Returns:
        tuple: (X_train, y_train, X_test, y_test, feature_names)
    """
    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)
    
    # Assuming 'label' column is the target and others are features
    feature_cols = [col for col in df_train.columns if col != 'label']
    
    X_train = df_train[feature_cols].values
    y_train = df_train['label'].values
    X_test = df_test[feature_cols].values
    y_test = df_test['label'].values
    feature_names = feature_cols
    
    return X_train, y_train, X_test, y_test, feature_names

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

def load_shap_values(json_path: str) -> dict:
    """
    Load SHAP values from a JSON file.
    
    Args:
        json_path: Path to SHAP JSON file
        
    Returns:
        dict: SHAP data
    """
    with open(json_path, 'r') as f:
        return json.load(f)

def generate_importance_plot(shap_data: dict, feature_names: list, output_path: str):
    """
    Generate a bar plot of mean absolute SHAP values.
    
    Args:
        shap_data: Dictionary containing SHAP values
        feature_names: List of feature names
        output_path: Path to save the plot
    """
    mean_abs_shap = np.array(shap_data["mean_abs_shap"])
    indices = np.argsort(mean_abs_shap)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(mean_abs_shap)), mean_abs_shap[indices], tick_label=[feature_names[i] for i in indices])
    plt.xlabel('Feature')
    plt.ylabel('Mean |SHAP Value|')
    plt.title('Feature Importance (Mean Absolute SHAP)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def generate_beeswarm_plot(shap_values: np.ndarray, feature_names: list, output_path: str):
    """
    Generate a beeswarm plot of SHAP values.
    
    Args:
        shap_values: SHAP values array
        feature_names: List of feature names
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, labels=feature_names, show=False)
    plt.savefig(output_path)
    plt.close()

def save_metrics_json(metrics: dict, output_path: str):
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing metrics
        output_path: Path to save the JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

def run_visualization_pipeline(shap_json_path: str, model_path: str, train_path: str, test_path: str, output_dir: str):
    """
    Run the full visualization pipeline.
    
    Args:
        shap_json_path: Path to SHAP JSON file
        model_path: Path to model pickle file
        train_path: Path to filtered training CSV
        test_path: Path to filtered test CSV
        output_dir: Directory to save outputs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    logging.info("Loading data...")
    X_train, y_train, X_test, y_test, feature_names = load_filtered_data_for_importance(train_path, test_path)
    
    # Load SHAP data
    logging.info("Loading SHAP data...")
    shap_data = load_shap_values(shap_json_path)
    
    # Generate importance plot
    logging.info("Generating importance plot...")
    importance_plot_path = os.path.join(output_dir, "importance_plot.png")
    generate_importance_plot(shap_data["shap_values"], feature_names, importance_plot_path)
    
    # Generate beeswarm plot
    logging.info("Generating beeswarm plot...")
    beeswarm_plot_path = os.path.join(output_dir, "beeswarm_plot.png")
    generate_beeswarm_plot(np.array(shap_data["shap_values"]["shap_values"]), feature_names, beeswarm_plot_path)
    
    # Save metrics
    logging.info("Saving metrics...")
    metrics_path = os.path.join(output_dir, "metrics.json")
    save_metrics_json(shap_data, metrics_path)

def main():
    parser = argparse.ArgumentParser(description="Visualize feature importance.")
    parser.add_argument("--shap_json_path", type=str, default="data/processed/feature_importance.json", help="Path to SHAP JSON file")
    parser.add_argument("--model_path", type=str, default="data/processed/classifier.pkl", help="Path to model pickle file")
    parser.add_argument("--train_path", type=str, default="data/processed/filtered_train.csv", help="Path to filtered training CSV")
    parser.add_argument("--test_path", type=str, default="data/processed/filtered_test.csv", help="Path to filtered test CSV")
    parser.add_argument("--output_dir", type=str, default="data/processed/figures", help="Directory to save outputs")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run visualization pipeline
    run_visualization_pipeline(args.shap_json_path, args.model_path, args.train_path, args.test_path, args.output_dir)
    
    print(f"Visualization complete. Outputs saved to {args.output_dir}")

if __name__ == "__main__":
    main()
