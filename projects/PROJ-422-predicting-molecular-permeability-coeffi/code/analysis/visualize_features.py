import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logging import setup_logging, log_result_artifact

# Configure logging
logger = logging.getLogger(__name__)

def load_feature_importance_rf(file_path: Path) -> Dict[str, Any]:
    """Load RF feature importance from JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"RF feature importance file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def load_feature_importance_gnn(file_path: Path) -> Dict[str, Any]:
    """Load GNN feature importance from JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"GNN feature importance file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def prepare_comparison_data(
    rf_data: Dict[str, Any],
    gnn_data: Dict[str, Any],
    top_n: int = 10
) -> pd.DataFrame:
    """
    Prepare a DataFrame for comparison visualization.
    Normalizes importance scores to [0, 1] within each model for fair comparison.
    """
    # Extract RF features
    rf_features = rf_data.get('features', [])
    rf_scores = rf_data.get('scores', [])
    if not rf_features or not rf_scores:
        # Handle case where data might be structured differently
        if 'importance' in rf_data:
            rf_features = [k for k, v in sorted(rf_data['importance'].items(), key=lambda x: abs(x[1]), reverse=True)]
            rf_scores = [rf_data['importance'][k] for k in rf_features]
        else:
            raise ValueError("Could not extract RF features/scores from data")

    # Extract GNN features
    gnn_features = gnn_data.get('substructures', [])
    gnn_scores = gnn_data.get('scores', [])
    if not gnn_features or not gnn_scores:
        if 'importance' in gnn_data:
            gnn_features = [k for k, v in sorted(gnn_data['importance'].items(), key=lambda x: abs(x[1]), reverse=True)]
            gnn_scores = [gnn_data['importance'][k] for k in gnn_features]
        else:
            raise ValueError("Could not extract GNN substructures/scores from data")

    # Normalize scores to 0-1 range for comparison
    max_rf = max(abs(s) for s in rf_scores) if rf_scores else 1.0
    max_gnn = max(abs(s) for s in gnn_scores) if gnn_scores else 1.0
    
    norm_rf_scores = [abs(s) / max_rf for s in rf_scores]
    norm_gnn_scores = [abs(s) / max_gnn for s in gnn_scores]

    # Create DataFrames for top N
    df_rf = pd.DataFrame({
        'Feature': rf_features[:top_n],
        'Importance (Normalized)': norm_rf_scores[:top_n],
        'Model': 'Random Forest (SHAP)'
    })
    df_gnn = pd.DataFrame({
        'Feature': gnn_features[:top_n],
        'Importance (Normalized)': norm_gnn_scores[:top_n],
        'Model': 'GNN (GNNExplainer)'
    })

    df_combined = pd.concat([df_rf, df_gnn], ignore_index=True)
    return df_combined

def create_comparison_bar_chart(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Top 10 Predictive Features: RF vs GNN",
    figsize: Tuple[int, int] = (12, 8)
) -> None:
    """Create a horizontal bar chart comparing top features."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    # Separate data by model
    rf_data = df[df['Model'] == 'Random Forest (SHAP)']
    gnn_data = df[df['Model'] == 'GNN (GNNExplainer)']

    # Plot RF features
    ax.barh(
        rf_data['Feature'],
        rf_data['Importance (Normalized)'],
        color='#1f77b4',
        alpha=0.8,
        label='Random Forest (SHAP)'
    )

    # Offset GNN features slightly to avoid overlap if names match (rare but possible)
    # Since they are distinct feature sets usually, we can just plot them below or use a different style
    # Here we will plot them in the same chart but with different colors.
    # To make them distinct, we'll shift the y-coordinates if we were doing a scatter, 
    # but for barh, we can just plot them. However, if feature names are identical, they overlap.
    # Given the nature of SHAP (descriptors) vs GNNExplainer (substructures), names differ.
    # We will plot GNN features with a different color.
    ax.barh(
        gnn_data['Feature'],
        gnn_data['Importance (Normalized)'],
        color='#ff7f0e',
        alpha=0.8,
        label='GNN (GNNExplainer)'
    )

    ax.set_xlabel('Normalized Importance Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.invert_yaxis()  # Highest importance at top

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved comparison bar chart to {output_path}")

def create_heatmap_comparison(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Feature Importance Heatmap",
    figsize: Tuple[int, int] = (10, 8)
) -> None:
    """
    Create a heatmap showing importance scores.
    Since features are different, we create a matrix where rows are features and columns are models.
    """
    # Pivot the data to create a matrix
    # We need to align features. Since features are likely unique to each model,
    # we will create a matrix where rows are all unique features and columns are models.
    # Missing values will be 0 (feature not present in that model's top list).
    
    pivot_df = df.pivot_table(
        index='Feature',
        columns='Model',
        values='Importance (Normalized)',
        aggfunc='first'
    ).fillna(0)

    # Reorder columns
    pivot_df = pivot_df[['Random Forest (SHAP)', 'GNN (GNNExplainer)']]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".3f",
        cmap='YlOrRd',
        linewidths=0.5,
        ax=ax,
        cbar_kws={'label': 'Normalized Importance'}
    )

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved heatmap comparison to {output_path}")

def main():
    """Main entry point for generating visualizations."""
    # Setup logging
    setup_logging(task_id="T032", log_level=logging.INFO)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    results_dir = project_root / "results"
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    rf_input = results_dir / "feature_importance_rf.json"
    gnn_input = results_dir / "feature_importance_gnn.json"

    # Load data
    try:
        rf_data = load_feature_importance_rf(rf_input)
        gnn_data = load_feature_importance_gnn(gnn_input)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot generate visualizations without feature importance data. "
                     "Please ensure T029 and T030 have completed successfully.")
        sys.exit(1)

    # Prepare data
    df_comparison = prepare_comparison_data(rf_data, gnn_data, top_n=10)

    # Generate Bar Chart
    bar_chart_path = figures_dir / "feature_importance_comparison_bar.png"
    create_comparison_bar_chart(df_comparison, bar_chart_path)

    # Generate Heatmap
    heatmap_path = figures_dir / "feature_importance_comparison_heatmap.png"
    create_heatmap_comparison(df_comparison, heatmap_path)

    # Log artifacts
    log_result_artifact("feature_importance_comparison_bar.png", str(bar_chart_path))
    log_result_artifact("feature_importance_comparison_heatmap.png", str(heatmap_path))

    logger.info("Visualization generation completed successfully.")

if __name__ == "__main__":
    main()