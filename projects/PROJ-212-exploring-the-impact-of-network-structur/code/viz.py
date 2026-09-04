import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_heatmap(data: pd.DataFrame, x_col: str, y_col: str, z_col: str, output_path: str):
    """
    Generate a heatmap visualization.
    X: metric A, Y: metric B, Color: Threshold
    """
    logger.info(f"Generating heatmap for {x_col} vs {y_col} with color {z_col}")
    
    plt.figure(figsize=(10, 8))
    pivot_table = data.pivot_table(values=z_col, index=y_col, columns=x_col, aggfunc='mean')
    sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap='viridis')
    plt.title(f"Heatmap: {z_col} by {x_col} and {y_col}")
    plt.tight_layout()
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")
