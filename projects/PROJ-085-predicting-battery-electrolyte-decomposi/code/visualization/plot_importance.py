import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Import from project modules
from config import get_project_root, get_validation_dir, get_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_importance_data() -> pd.DataFrame:
    """
    Load feature importance data from the model run artifacts.
    Expects data/processed/model_run.json containing 'importance' data.
    """
    project_root = get_project_root()
    model_run_path = project_root / "data" / "processed" / "model_run.json"
    
    if not model_run_path.exists():
        raise FileNotFoundError(f"Model run artifacts not found at {model_run_path}. "
                                "Please ensure T026 (save_model_run_artifacts) has been executed.")
    
    with open(model_run_path, 'r') as f:
        data = json.load(f)
    
    if 'importance' not in data:
        raise KeyError("Model run artifacts do not contain 'importance' key. "
                       "Ensure T026 saved the importance data correctly.")
    
    # Convert to DataFrame
    # Expected structure: {'low_potential': [{feature, importance}, ...], 'high_potential': [...]}
    df_rows = []
    
    for bin_name, features in data['importance'].items():
        for feat in features:
            df_rows.append({
                'bin': bin_name,
                'feature': feat['feature'],
                'importance': feat['importance']
            })
    
    df = pd.DataFrame(df_rows)
    return df

def get_top_features(df: pd.DataFrame, n_top: int = 10) -> pd.DataFrame:
    """
    Get the top N features by importance for each bin.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    
    # Sort by bin and importance descending
    df_sorted = df.sort_values(by=['bin', 'importance'], ascending=[True, False])
    
    # Get top N per bin
    top_features = df_sorted.groupby('bin', group_keys=False).head(n_top)
    
    return top_features

def create_heatmap(df: pd.DataFrame, output_path: Path, n_top: int = 15) -> None:
    """
    Create a heatmap of top feature importances per bin.
    
    Args:
        df: DataFrame with columns ['bin', 'feature', 'importance']
        output_path: Path where the plot will be saved
        n_top: Number of top features to include per bin
    """
    if df.empty:
        raise ValueError("Cannot create heatmap from empty DataFrame.")
    
    # Get top features
    top_df = get_top_features(df, n_top=n_top)
    
    # Pivot for heatmap
    # Rows: features, Columns: bins, Values: importance
    pivot_df = top_df.pivot(index='feature', columns='bin', values='importance')
    
    # Ensure consistent ordering if possible (optional, but good for readability)
    # Sort by mean importance across bins for display
    pivot_df = pivot_df.reindex(pivot_df.mean(axis=1).sort_values(ascending=True).index)
    
    # Set up the matplotlib figure
    plt.figure(figsize=(12, 10))
    
    # Create heatmap
    sns.heatmap(pivot_df, annot=True, fmt=".4f", cmap="YlGnBu", linewidths=.5, 
                cbar_kws={'label': 'Permutation Importance'})
    
    plt.title('Top Feature Importance by Potential Bin\n(Low: 0-2V, High: 4V)')
    plt.xlabel('Potential Bin')
    plt.ylabel('Feature')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")

def run_visualization_pipeline() -> Path:
    """
    Main pipeline to generate the feature importance heatmap.
    
    Returns:
        Path to the saved heatmap file.
    """
    project_root = get_project_root()
    validation_dir = get_validation_dir()
    output_path = validation_dir / "feature_importance_heatmap.png"
    
    logger.info("Starting feature importance visualization pipeline...")
    
    try:
        # Load data
        df = load_importance_data()
        logger.info(f"Loaded importance data for {len(df)} feature-bin combinations.")
        
        # Create heatmap
        create_heatmap(df, output_path, n_top=15)
        
        logger.info("Visualization pipeline completed successfully.")
        return output_path
        
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_visualization_pipeline()
