import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

# Import shared utilities and config
from utils import setup_logging, save_json, load_json, get_env_var, ensure_dir
from config_env import configure_environment

# Configure logging
logger = setup_logging(__name__)

def load_model(model_path: str) -> tuple:
    """
    Load the trained Random Forest model and associated metadata.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}")
    
    with open(model_path, 'rb') as f:
        artifact = pickle.load(f)
    
    model = artifact['model']
    metrics = artifact.get('metrics', {})
    feature_names = artifact.get('feature_names', [])
    
    return model, metrics, feature_names

def load_training_features(data_path: str) -> tuple:
    """
    Load the training features and labels from the parquet file.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found at {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Assuming the parquet file has 'X' (features) and 'y' (labels) columns or separate columns
    # Based on T019 output structure, we expect feature columns and label columns
    # We need to identify which columns are features and which are labels.
    # Standard convention: label columns often start with 'label_' or are defined in a config.
    # For robustness, we assume the last N columns are labels if not specified, 
    # or we look for a specific schema. 
    # Given T019 generates 'train_set.parquet', let's assume a standard schema:
    # Feature columns are all numeric columns except the known label columns.
    # However, to be safe, we'll try to load the metadata if available or infer.
    # Let's assume the parquet contains all columns, and we need to separate them.
    # A common pattern is to have 'target' or 'labels' column, but for multi-label, 
    # we likely have multiple binary columns.
    
    # Heuristic: Columns with 'pathway' or 'label' in name are targets, others are features.
    # Or, we rely on the training script to have saved feature names in the model artifact.
    # Since load_model returns feature_names, we can use that to slice the dataframe.
    
    # For this implementation, we assume the parquet file has the feature columns 
    # matching the order in the model's feature_names.
    # We will select columns that exist in feature_names.
    
    available_cols = [c for c in df.columns if c in feature_names]
    if len(available_cols) != len(feature_names):
        logger.warning(f"Feature name mismatch. Expected {len(feature_names)}, found {len(available_cols)}.")
        # Fallback: use all numeric columns if names don't match exactly
        available_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    X = df[available_cols].values
    
    # Identify label columns. Assuming they are the remaining columns or named specifically.
    # Let's assume the parquet file has a 'labels' column as a list or separate columns.
    # Based on T024 (multi-label), we expect multiple target columns.
    # Let's assume the training script saved the label column names in the model artifact too.
    # If not, we infer: columns not in feature_names are labels.
    label_cols = [c for c in df.columns if c not in feature_names]
    if not label_cols:
        raise ValueError("Could not identify label columns in the training data.")
    
    y = df[label_cols].values
    
    return X, y, feature_names

def compute_shap_values(model: RandomForestClassifier, X: np.ndarray, feature_names: List[str]) -> shap.Explanation:
    """
    Compute SHAP values for the trained model.
    """
    logger.info("Computing SHAP values...")
    # Use TreeExplainer for Random Forest
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # For multi-output, shap_values is a list of arrays (one per class)
    # We return the explanation object which handles this
    # If shap_values is a list, we might need to aggregate or handle per-class
    # shap.Explanation expects a single array or a specific structure.
    # For multi-label, we often look at the mean absolute SHAP value across all labels
    # or per label.
    
    # Convert to Explanation object if needed
    # shap.Explanation(shap_values, data=X, feature_names=feature_names)
    # However, shap_values for multi-output is a list. 
    # We will compute the mean absolute SHAP value across all outputs for ranking.
    
    return shap_values

def rank_features(shap_values: Any, feature_names: List[str], num_classes: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate ranked feature importance lists for each degradation pathway.
    
    Returns a dictionary where keys are pathway names (or indices) and values
    are lists of dictionaries containing 'feature', 'importance', 'rank'.
    """
    # shap_values for multi-output is a list of arrays, one per class.
    # Each array has shape (n_samples, n_features).
    # We calculate the mean absolute SHAP value for each feature for each class.
    
    if isinstance(shap_values, list):
        # Multi-output case
        rankings = {}
        for i, sv in enumerate(shap_values):
            # Mean absolute SHAP value per feature
            mean_abs_shap = np.mean(np.abs(sv), axis=0)
            sorted_indices = np.argsort(mean_abs_shap)[::-1]
            
            pathway_name = f"pathway_{i}" # Default naming, can be improved if labels have names
            rankings[pathway_name] = []
            for rank, idx in enumerate(sorted_indices):
                rankings[pathway_name].append({
                    "feature": feature_names[idx],
                    "importance": float(mean_abs_shap[idx]),
                    "rank": rank + 1
                })
        return rankings
    else:
        # Single output case
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        sorted_indices = np.argsort(mean_abs_shap)[::-1]
        rankings = {
            "default": []
        }
        for rank, idx in enumerate(sorted_indices):
            rankings["default"].append({
                "feature": feature_names[idx],
                "importance": float(mean_abs_shap[idx]),
                "rank": rank + 1
            })
        return rankings

def generate_shap_plot(shap_values: Any, feature_names: List[str], output_path: str):
    """
    Generate a summary SHAP plot.
    """
    logger.info(f"Generating SHAP summary plot at {output_path}")
    # Ensure directory exists
    ensure_dir(output_path)
    
    # shap.summary_plot handles multi-output by plotting for each output or aggregated
    # We'll try to generate a summary plot. If shap_values is a list, shap.summary_plot
    # might need specific handling.
    try:
        if isinstance(shap_values, list):
            # For multi-output, we might plot the first one or aggregate
            # Let's try plotting the mean absolute SHAP values across all outputs
            # Create a dummy explanation object with aggregated values?
            # Or just plot the first one as a representative
            # Better: shap.summary_plot can take a list of explanations if using the new API
            # But for stability, let's aggregate mean absolute values
            mean_abs_shap = np.mean([np.abs(sv) for sv in shap_values], axis=0)
            shap.summary_plot(mean_abs_shap, feature_names=feature_names, show=False)
            plt = plt.gcf() # Get current figure
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            shap.summary_plot(shap_values, feature_names=feature_names, show=False)
            plt = plt.gcf()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
    except Exception as e:
        logger.error(f"Failed to generate SHAP plot: {e}")
        # Fallback: create a simple bar plot of mean absolute SHAP values
        import matplotlib.pyplot as plt
        if isinstance(shap_values, list):
            mean_abs_shap = np.mean([np.abs(sv) for sv in shap_values], axis=0)
        else:
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        plt.figure(figsize=(10, 6))
        plt.barh(feature_names, mean_abs_shap)
        plt.xlabel("Mean |SHAP Value|")
        plt.title("Feature Importance (Mean |SHAP|)")
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def run_explainability_pipeline(model_path: str, train_data_path: str, output_dir: str):
    """
    Run the full explainability pipeline: load model, compute SHAP, rank features, save reports.
    """
    logger.info("Starting explainability pipeline...")
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # 1. Load Model
    model, metrics, feature_names = load_model(model_path)
    logger.info(f"Model loaded. Feature names: {len(feature_names)}")
    
    # 2. Load Training Data
    X, y, _ = load_training_features(train_data_path)
    logger.info(f"Training data loaded. Shape: {X.shape}")
    
    # 3. Compute SHAP Values
    shap_values = compute_shap_values(model, X, feature_names)
    
    # 4. Rank Features
    num_classes = y.shape[1] if len(y.shape) > 1 else 1
    rankings = rank_features(shap_values, feature_names, num_classes)
    
    # 5. Save Rankings to JSON
    rankings_path = os.path.join(output_dir, "feature_rankings.json")
    save_json(rankings, rankings_path)
    logger.info(f"Feature rankings saved to {rankings_path}")
    
    # 6. Generate Plot
    plot_path = os.path.join(output_dir, "shap_summary.png")
    generate_shap_plot(shap_values, feature_names, plot_path)
    logger.info(f"SHAP plot saved to {plot_path}")
    
    return rankings

def main():
    """
    Main entry point for the explainability task.
    """
    configure_environment()
    
    # Paths
    model_path = get_env_var("MODEL_PATH", "results/artifacts/model.pkl")
    train_data_path = get_env_var("TRAIN_DATA_PATH", "data/processed/train_set.parquet")
    output_dir = get_env_var("EXPLAINABILITY_OUTPUT_DIR", "results/plots")
    
    # Ensure output dir exists
    ensure_dir(output_dir)
    
    try:
        rankings = run_explainability_pipeline(model_path, train_data_path, output_dir)
        logger.info("Explainability pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Explainability pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()