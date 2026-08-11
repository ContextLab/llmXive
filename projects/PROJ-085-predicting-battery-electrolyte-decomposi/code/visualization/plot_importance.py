import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_project_root, get_validation_dir, get_processed_dir
from models.evaluator import load_model_artifacts
from data.binning import load_processed_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_importance_data() -> Optional[pd.DataFrame]:
    """
    Load model artifacts and extract permutation importance for low and high potential bins.
    Returns a DataFrame with feature names and importance scores for each bin.
    """
    try:
        # Load the model artifacts which contain importance data
        artifacts_path = get_processed_dir() / "model_run.json"
        if not artifacts_path.exists():
            logger.error(f"Model artifacts not found at {artifacts_path}. Run trainer first.")
            return None

        model_data = load_model_artifacts()
        
        if 'importance' not in model_data:
            logger.error("No importance data found in model artifacts.")
            return None

        # Structure expected: {'low': {feature: score}, 'high': {feature: score}}
        importance_data = model_data.get('importance', {})
        
        if 'low' not in importance_data or 'high' not in importance_data:
            logger.error("Importance data missing 'low' or 'high' bin keys.")
            return None

        # Convert to DataFrame
        df = pd.DataFrame({
            'feature': list(importance_data['low'].keys()),
            'low_importance': list(importance_data['low'].values()),
            'high_importance': list(importance_data['high'].values())
        })
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading importance data: {e}")
        return None

def get_top_features(df: pd.DataFrame, n_top: int = 10) -> pd.DataFrame:
    """
    Select the top N features based on average importance across both bins.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df['avg_importance'] = (df['low_importance'] + df['high_importance']) / 2
    df_sorted = df.sort_values(by='avg_importance', ascending=False)
    return df_sorted.head(n_top)

def create_heatmap(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Create a heatmap visualization of top features per bin and save to file.
    """
    if df is None or df.empty:
        logger.error("No data provided for heatmap.")
        return False

    # Prepare data for heatmap: index=features, columns=bins
    heatmap_data = df.set_index('feature')[['low_importance', 'high_importance']]
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Set style
    sns.set_theme(style="white")
    plt.figure(figsize=(10, 8))
    
    # Create heatmap
    ax = sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".3f",
        cmap="YlGnBu",
        linewidths=.5,
        cbar_kws={'label': 'Permutation Importance'}
    )
    
    plt.title('Feature Importance: Low (0-2V) vs High (4V) Potential Bins', fontsize=14)
    plt.ylabel('Top Features')
    plt.xlabel('Potential Bin')
    
    # Rotate x-axis labels if needed
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")
    return True

def run_visualization_pipeline() -> bool:
    """
    Main pipeline to generate the feature importance heatmap.
    """
    logger.info("Starting feature importance visualization pipeline...")
    
    # Load data
    importance_df = load_importance_data()
    if importance_df is None:
        logger.error("Failed to load importance data. Aborting.")
        return False
    
    # Get top features
    top_df = get_top_features(importance_df, n_top=10)
    if top_df.empty:
        logger.error("No features found. Aborting.")
        return False
    
    # Define output path
    output_dir = get_validation_dir()
    output_path = output_dir / "feature_importance_heatmap.png"
    
    # Create and save heatmap
    success = create_heatmap(top_df, output_path)
    
    if success:
        logger.info("Visualization pipeline completed successfully.")
    else:
        logger.error("Visualization pipeline failed.")
        
    return success

if __name__ == "__main__":
    run_visualization_pipeline()
