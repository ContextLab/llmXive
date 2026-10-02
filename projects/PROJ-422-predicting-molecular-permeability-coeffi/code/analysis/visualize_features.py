import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

# Ensure matplotlib uses a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_importance_rf(path: Path) -> Dict[str, Any]:
    """
    Load Random Forest feature importance from JSON.
    Expects a list of dicts with 'feature' and 'importance' keys.
    """
    if not path.exists():
        raise FileNotFoundError(f"RF feature importance file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle potential list structure
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'features' in data:
        return data['features']
    else:
        # Fallback: assume direct dict mapping or list of dicts
        return data if isinstance(data, list) else [data]

def load_feature_importance_gnn(path: Path) -> Dict[str, Any]:
    """
    Load GNN feature importance from JSON.
    Expects a list of dicts with 'substructure' and 'importance' keys.
    """
    if not path.exists():
        raise FileNotFoundError(f"GNN feature importance file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'substructures' in data:
        return data['substructures']
    else:
        return data if isinstance(data, list) else [data]

def prepare_comparison_data(
    rf_data: List[Dict], 
    gnn_data: List[Dict], 
    top_n: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare dataframes for comparison charts.
    Returns (rf_df, gnn_df) sorted by importance.
    """
    # Extract and sort RF data
    rf_df = pd.DataFrame(rf_data)
    if 'feature' not in rf_df.columns or 'importance' not in rf_df.columns:
        # Try alternative keys
        if 'name' in rf_df.columns:
            rf_df['feature'] = rf_df['name']
        if 'value' in rf_df.columns:
            rf_df['importance'] = rf_df['value']
    
    rf_df = rf_df.sort_values('importance', ascending=False).head(top_n)
    
    # Extract and sort GNN data
    gnn_df = pd.DataFrame(gnn_data)
    if 'substructure' not in gnn_df.columns or 'importance' not in gnn_df.columns:
        if 'name' in gnn_df.columns:
            gnn_df['substructure'] = gnn_df['name']
        if 'value' in gnn_df.columns:
            gnn_df['importance'] = gnn_df['value']
    
    gnn_df = gnn_df.sort_values('importance', ascending=False).head(top_n)
    
    return rf_df, gnn_df

def create_comparison_bar_chart(
    rf_df: pd.DataFrame,
    gnn_df: pd.DataFrame,
    output_path: Path,
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """
    Create a side-by-side bar chart comparing top features.
    """
    plt.figure(figsize=figsize)
    
    # Plot RF features
    plt.subplot(1, 2, 1)
    if not rf_df.empty and 'feature' in rf_df.columns and 'importance' in rf_df.columns:
        plt.barh(rf_df['feature'], rf_df['importance'], color='skyblue')
        plt.xlabel('Importance (SHAP)')
        plt.title('Top Random Forest Features (SHAP)')
        plt.gca().invert_yaxis()
    else:
        plt.text(0.5, 0.5, 'No RF Data Available', ha='center', va='center', transform=plt.gca().transAxes)
    
    # Plot GNN features
    plt.subplot(1, 2, 2)
    if not gnn_df.empty and 'substructure' in gnn_df.columns and 'importance' in gnn_df.columns:
        # Truncate long names for display
        display_labels = [str(x)[:20] + '...' if len(str(x)) > 20 else str(x) for x in gnn_df['substructure']]
        plt.barh(display_labels, gnn_df['importance'], color='salmon')
        plt.xlabel('Importance (GNNExplainer)')
        plt.title('Top GNN Substructures')
        plt.gca().invert_yaxis()
    else:
        plt.text(0.5, 0.5, 'No GNN Data Available', ha='center', va='center', transform=plt.gca().transAxes)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved bar chart to {output_path}")

def create_heatmap_comparison(
    rf_df: pd.DataFrame,
    gnn_df: pd.DataFrame,
    output_path: Path,
    figsize: Tuple[int, int] = (10, 8)
) -> None:
    """
    Create a heatmap comparing normalized importance scores.
    """
    plt.figure(figsize=figsize)
    
    # Normalize data for comparison
    data_matrix = []
    labels = []
    
    if not rf_df.empty and 'feature' in rf_df.columns and 'importance' in rf_df.columns:
        rf_importance = rf_df['importance'].values
        # Normalize to 0-1
        if rf_importance.max() > 0:
            rf_importance = rf_importance / rf_importance.max()
        data_matrix.append(rf_importance)
        labels.append("RF (SHAP)")
    else:
        data_matrix.append(np.zeros(len(gnn_df)))
        labels.append("RF (SHAP)")
    
    if not gnn_df.empty and 'substructure' in gnn_df.columns and 'importance' in gnn_df.columns:
        gnn_importance = gnn_df['importance'].values
        # Normalize to 0-1
        if gnn_importance.max() > 0:
            gnn_importance = gnn_importance / gnn_importance.max()
        data_matrix.append(gnn_importance)
        labels.append("GNN (Explainer)")
    else:
        data_matrix.append(np.zeros(len(rf_df)))
        labels.append("GNN (Explainer)")
    
    # Create a combined index for x-axis (features/substructures)
    # Use the union of indices or just the max length
    max_len = max(len(rf_df) if not rf_df.empty else 0, len(gnn_df) if not gnn_df.empty else 0)
    
    # Pad arrays to same length if necessary
    padded_data = []
    for i, arr in enumerate(data_matrix):
        if len(arr) < max_len:
            padded_arr = np.zeros(max_len)
            padded_arr[:len(arr)] = arr
            padded_data.append(padded_arr)
        else:
            padded_data.append(arr)
    
    # Create x-axis labels (truncated)
    x_labels = []
    if not rf_df.empty:
        x_labels = [str(x)[:15] for x in rf_df['feature']]
    elif not gnn_df.empty:
        x_labels = [str(x)[:15] for x in gnn_df['substructure']]
    
    # Fill missing labels
    while len(x_labels) < max_len:
        x_labels.append(f"Feature {len(x_labels)}")
    
    data_array = np.array(padded_data)
    
    sns.heatmap(
        data_array,
        xticklabels=x_labels,
        yticklabels=labels,
        cmap='YlOrRd',
        annot=True,
        fmt=".2f",
        cbar_kws={'label': 'Normalized Importance'}
    )
    
    plt.xticks(rotation=45, ha='right')
    plt.title('Normalized Feature Importance Comparison')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved heatmap to {output_path}")

def main():
    """
    Main entry point to generate feature importance visualizations.
    """
    logger.info("Starting feature importance visualization generation...")
    
    # Define paths
    base_path = Path("results")
    rf_path = base_path / "feature_importance_rf.json"
    gnn_path = base_path / "feature_importance_gnn.json"
    figures_dir = base_path / "figures"
    
    # Ensure output directory exists
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading RF data from {rf_path}...")
        rf_data = load_feature_importance_rf(rf_path)
        
        logger.info(f"Loading GNN data from {gnn_path}...")
        gnn_data = load_feature_importance_gnn(gnn_path)
        
        # Prepare data
        rf_df, gnn_df = prepare_comparison_data(rf_data, gnn_data, top_n=10)
        
        # Generate bar chart
        bar_chart_path = figures_dir / "feature_importance_comparison.png"
        create_comparison_bar_chart(rf_df, gnn_df, bar_chart_path)
        
        # Generate heatmap
        heatmap_path = figures_dir / "feature_importance_heatmap.png"
        create_heatmap_comparison(rf_df, gnn_df, heatmap_path)
        
        logger.info("Visualization generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Ensure T029 and T030 have been completed to generate the input JSON files.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during visualization generation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()