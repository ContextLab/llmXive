import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Import project utilities
from utils.config import get_models_dir, get_viz_dir, get_reports_dir, get_seed, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_and_feature_names(model_path: Path) -> Tuple[Any, List[str]]:
    """
    Load the trained Random Forest model and extract feature names.
    
    Args:
        model_path: Path to the pickled model file.
        
    Returns:
        Tuple of (model, feature_names)
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Feature names are typically stored in the training metadata or 
    # can be derived from the training data. We assume they are stored
    # in the training_metrics.json or we need to load them from the 
    # species_profiles.csv used for training.
    # For robustness, we try to load feature names from the training metadata.
    metrics_path = model_path.parent / 'training_metrics.json'
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            feature_names = metrics.get('feature_names')
            if feature_names:
                logger.info(f"Loaded feature names from {metrics_path}")
                return model, feature_names
    
    # Fallback: Try to infer from the model's feature_importances_ shape
    # and load the species_profiles.csv to get column names
    profiles_path = model_path.parent.parent / 'processed' / 'species_profiles.csv'
    if profiles_path.exists():
        df = pd.read_csv(profiles_path)
        # Exclude target and ID columns
        exclude_cols = ['species_id', 'foraging_guild']
        feature_names = [col for col in df.columns if col not in exclude_cols]
        logger.info(f"Inferred feature names from {profiles_path}")
        return model, feature_names
    
    raise ValueError("Could not determine feature names. Please ensure 'feature_names' is in training_metrics.json or 'species_profiles.csv' exists.")

def extract_feature_importance(model: Any, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract feature importance scores from the Random Forest model.
    
    Args:
        model: The trained Random Forest model.
        feature_names: List of feature names corresponding to the model's features.
        
    Returns:
        DataFrame with 'feature' and 'importance' columns.
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute.")
    
    importances = model.feature_importances_
    if len(importances) != len(feature_names):
        raise ValueError(f"Length mismatch: {len(importances)} importances vs {len(feature_names)} features.")
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    })
    
    # Sort by importance descending
    importance_df = importance_df.sort_values(by='importance', ascending=False).reset_index(drop=True)
    logger.info(f"Extracted importance for {len(importance_df)} features")
    return importance_df

def plot_feature_importance(
    importance_df: pd.DataFrame, 
    output_path: Path, 
    top_n: int = 15
) -> None:
    """
    Generate a bar chart of feature importances and save it.
    
    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns.
        output_path: Path where the plot will be saved.
        top_n: Number of top features to display.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select top N features for clarity
    plot_df = importance_df.head(top_n).copy()
    
    plt.figure(figsize=(10, 8))
    sns.barplot(
        data=plot_df, 
        x='importance', 
        y='feature', 
        palette='viridis',
        orient='h'
    )
    plt.title(f'Top {top_n} Feature Importances (Random Forest)')
    plt.xlabel('Mean Decrease Impurity')
    plt.ylabel('Feature')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved feature importance plot to {output_path}")

def save_importance_json(importance_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save raw feature importance values to a JSON file.
    
    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns.
        output_path: Path where the JSON will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of dicts for JSON serialization
    data = importance_df.to_dict(orient='records')
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved feature importance JSON to {output_path}")

def main():
    """
    Main entry point for the feature importance visualization task.
    """
    # Define paths
    models_dir = get_models_dir()
    viz_dir = get_viz_dir()
    
    model_path = models_dir / 'random_forest.pkl'
    plot_output_path = viz_dir / 'feature_importance.png'
    json_output_path = viz_dir / 'feature_importance.json'
    
    # Ensure directories exist
    ensure_directories([viz_dir])
    
    try:
        # Load model and feature names
        model, feature_names = load_model_and_feature_names(model_path)
        
        # Extract importance
        importance_df = extract_feature_importance(model, feature_names)
        
        # Plot and save
        plot_feature_importance(importance_df, plot_output_path)
        
        # Save JSON
        save_importance_json(importance_df, json_output_path)
        
        logger.info("Task T044 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T044 failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
