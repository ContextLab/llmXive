import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple

import matplotlib.pyplot as plt
import pandas as pd

# Ensure the matplotlib backend is non-interactive for headless environments
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

def load_outlier_indices(filepath: str) -> Dict[str, set]:
    """
    Load outlier indices from the IQR calculation output.
    Expected format: JSON with 'ai_group_outlier_indices' and 'non_ai_group_outlier_indices'.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return {
            'ai': set(data.get('ai_group_outlier_indices', [])),
            'non_ai': set(data.get('non_ai_group_outlier_indices', []))
        }
    except FileNotFoundError:
        logger.warning(f"Outlier indices file not found at {filepath}. Proceeding without outlier exclusion for visualization.")
        return {'ai': set(), 'non_ai': set()}

def prepare_boxplot_data(
    df: pd.DataFrame,
    outlier_indices: Dict[str, set]
) -> Tuple[List[float], List[float]]:
    """
    Prepare data for boxplot, excluding outliers identified by IQR.
    
    Args:
        df: DataFrame with 'turnaround_hours' and 'is_ai' columns.
        outlier_indices: Dict mapping group names to sets of row indices to exclude.
        
    Returns:
        Tuple of (ai_turnaround_times, non_ai_turnaround_times) with outliers removed.
    """
    # Filter out outliers for the visualization only
    ai_data = df[
        (df['is_ai'] == True) & (~df.index.isin(outlier_indices['ai']))
    ]['turnaround_hours'].tolist()
    
    non_ai_data = df[
        (df['is_ai'] == False) & (~df.index.isin(outlier_indices['non_ai']))
    ]['turnaround_hours'].tolist()
    
    logger.info(f"Visualization data prepared: AI={len(ai_data)} samples, Non-AI={len(non_ai_data)} samples")
    logger.info(f"Outliers excluded: AI={len(outlier_indices['ai'])}, Non-AI={len(outlier_indices['non_ai'])}")
    
    return ai_data, non_ai_data

def generate_boxplot(
    ai_data: List[float],
    non_ai_data: List[float],
    output_path: str,
    dpi: int = 300
) -> None:
    """
    Generate and save the boxplot visualization.
    
    Args:
        ai_data: List of turnaround hours for AI-assisted PRs.
        non_ai_data: List of turnaround hours for non-AI PRs.
        output_path: Path to save the image file.
        dpi: Resolution of the saved image (default 300).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create boxplot data structure
    boxplot_data = [non_ai_data, ai_data]
    labels = ['Non-AI', 'AI-Assisted']
    
    # Generate boxplot
    bp = ax.boxplot(boxplot_data, labels=labels, patch_artist=True, notch=True)
    
    # Color coding
    colors = ['#4C72B0', '#DD8452']  # Blue for Non-AI, Orange for AI
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        
    # Style adjustments
    ax.set_ylabel('Turnaround Time (hours)', fontsize=12, fontweight='bold')
    ax.set_xlabel('PR Type', fontsize=12, fontweight='bold')
    ax.set_title('Comparison of Code Review Turnaround Time: AI vs. Non-AI', fontsize=14, fontweight='bold')
    
    # Grid for readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Ensure tight layout
    plt.tight_layout()
    
    # Save with high resolution
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Boxplot saved to {output_path} with {dpi} DPI resolution")

def main():
    """
    Main entry point for the visualization script.
    Loads processed data, handles outliers, and generates the boxplot.
    """
    # Configuration
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'data' / 'processed' / 'pr_turnaround.csv'
    outlier_path = base_dir / 'data' / 'processed' / 'iqr_outliers.json'
    output_dir = base_dir / 'artifacts'
    output_path = output_dir / 'boxplot.png'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load processed data
    logger.info(f"Loading processed data from {data_path}")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error(f"Processed data file not found: {data_path}")
        logger.error("Please ensure T018b has been completed successfully.")
        raise
    
    # Validate required columns
    required_cols = ['turnaround_hours', 'is_ai']
    if not all(col in df.columns for col in required_cols):
        missing = [c for c in required_cols if c not in df.columns]
        logger.error(f"Missing required columns in data: {missing}")
        raise ValueError(f"Missing columns: {missing}")
    
    # Load outlier indices (generated by T024)
    outlier_indices = load_outlier_indices(str(outlier_path))
    
    # Prepare data excluding outliers
    ai_data, non_ai_data = prepare_boxplot_data(df, outlier_indices)
    
    # Check if we have data to plot
    if not ai_data or not non_ai_data:
        logger.error("One or both groups have no data after outlier exclusion.")
        raise ValueError("Insufficient data for visualization after outlier exclusion.")
    
    # Generate and save the boxplot
    logger.info(f"Generating boxplot...")
    generate_boxplot(ai_data, non_ai_data, str(output_path), dpi=300)
    
    # Verify output
    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        logger.info(f"Successfully generated {output_path} ({size_kb:.1f} KB)")
    else:
        logger.error("Failed to generate output file.")
        raise RuntimeError("Boxplot generation failed.")

if __name__ == '__main__':
    main()