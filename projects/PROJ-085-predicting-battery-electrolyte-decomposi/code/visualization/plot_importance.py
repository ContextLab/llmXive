import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from config import get_project_root, get_validation_dir, get_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_importance_data(importance_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load feature importance data from the model run JSON file.
    Expects a structure like:
    {
      "bins": {
        "low_potential": {"feature_importance": {...}},
        "high_potential": {"feature_importance": {...}}
      }
    }
    """
    if importance_path is None:
        processed_dir = get_processed_dir()
        importance_path = str(processed_dir / "model_run.json")

    if not os.path.exists(importance_path):
        raise FileNotFoundError(f"Importance data file not found: {importance_path}")

    with open(importance_path, 'r') as f:
        data = json.load(f)

    bins_data = data.get("bins", {})
    
    rows = []
    for bin_name, bin_info in bins_data.items():
        importance_dict = bin_info.get("feature_importance", {})
        for feature, importance in importance_dict.items():
            rows.append({
                "bin": bin_name,
                "feature": feature,
                "importance": importance
            })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No feature importance data found in the model run file.")
    
    return df

def get_top_features(df: pd.DataFrame, n_top: int = 10) -> pd.DataFrame:
    """
    Get the top N features by importance for each bin.
    """
    top_features = []
    for bin_name in df["bin"].unique():
        bin_df = df[df["bin"] == bin_name].nlargest(n_top, "importance")
        top_features.append(bin_df)
    
    if not top_features:
        return pd.DataFrame(columns=["bin", "feature", "importance"])
    
    return pd.concat(top_features, ignore_index=True)

def create_heatmap(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Create a heatmap of top features per bin and save to file.
    """
    if df.empty:
        raise ValueError("Cannot create heatmap from empty dataframe.")

    # Pivot the data to have bins as rows and features as columns
    pivot_df = df.pivot_table(index="feature", columns="bin", values="importance", aggfunc='first')
    
    # Sort by mean importance to make the heatmap more readable
    pivot_df = pivot_df.loc[pivot_df.mean(axis=1).sort_values(ascending=False).index]

    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot_df, annot=True, fmt=".3f", cmap="YlGnBu", linewidths=.5)
    plt.title("Feature Importance Heatmap by Potential Bin")
    plt.ylabel("Feature")
    plt.xlabel("Potential Bin")
    
    if output_path is None:
        validation_dir = get_validation_dir()
        output_path = str(validation_dir / "feature_importance_heatmap.png")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def run_visualization_pipeline(importance_path: Optional[str] = None, output_path: Optional[str] = None, n_top: int = 10) -> None:
    """
    Run the full pipeline to load importance data, filter top features, and create heatmap.
    """
    logger.info("Starting feature importance visualization pipeline...")
    
    try:
        importance_df = load_importance_data(importance_path)
        logger.info(f"Loaded {len(importance_df)} importance records.")
        
        top_df = get_top_features(importance_df, n_top=n_top)
        logger.info(f"Selected top {n_top} features per bin.")
        
        create_heatmap(top_df, output_path)
        
        logger.info("Feature importance visualization pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_visualization_pipeline()
