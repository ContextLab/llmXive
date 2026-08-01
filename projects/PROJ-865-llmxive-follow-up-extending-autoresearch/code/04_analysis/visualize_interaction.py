import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Import local logging utilities
try:
    from utils.logging import get_logger, log_stage_start, log_stage_end
except ImportError:
    def get_logger(name):
        return logging.getLogger(name)
    def log_stage_start(name):
        logging.info(f"Starting stage: {name}")
    def log_stage_end(name):
        logging.info(f"Finished stage: {name}")

logger = get_logger(__name__)

def load_results_csv(filepath: str) -> pd.DataFrame:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    df = pd.read_csv(path)
    required_cols = ['task_id', 'method', 'success', 'failure_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if df['success'].dtype == 'object':
        df['success'] = df['success'].map({True: 1, False: 0, 'true': 1, 'false': 0, 1: 1, 0: 0})
    return df

def calculate_interaction_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate success rates grouped by failure_type and method.
    """
    grouped = df.groupby(['failure_type', 'method'])['success'].agg(['mean', 'count', 'std']).reset_index()
    grouped.columns = ['failure_type', 'method', 'success_rate', 'count', 'std_dev']
    grouped['ci_lower'] = grouped['success_rate'] - 1.96 * (grouped['std_dev'] / np.sqrt(grouped['count']))
    grouped['ci_upper'] = grouped['success_rate'] + 1.96 * (grouped['std_dev'] / np.sqrt(grouped['count']))
    return grouped

def generate_interaction_plot(data: pd.DataFrame, output_path: str):
    """
    Generate a plot of the interaction effect between Failure Type and Method on Success Rate.
    """
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    # Use pointplot to show mean and confidence intervals
    ax = sns.pointplot(
        data=data,
        x='failure_type',
        y='success_rate',
        hue='method',
        capsize=0.2,
        palette="viridis",
        dodge=True,
        join=False # We want error bars, lines can be messy if we just want points
    )
    
    plt.title('Interaction Effect: Failure Type vs Method on Success Rate', fontsize=16)
    plt.xlabel('Failure Type', fontsize=12)
    plt.ylabel('Success Rate', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(title='Method')
    plt.ylim(0, 1.1)
    
    # Save
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Interaction plot saved to {output_path}")

def main():
    log_stage_start("visualize_interaction")
    
    input_path = "data/derived/results.csv"
    output_path = "data/derived/interaction_plot.png"
    
    try:
        df = load_results_csv(input_path)
        interaction_data = calculate_interaction_rates(df)
        generate_interaction_plot(interaction_data, output_path)
        return 0
    except Exception as e:
        logger.error(f"Error in visualize_interaction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())