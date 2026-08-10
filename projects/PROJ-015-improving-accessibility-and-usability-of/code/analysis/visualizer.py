import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Optional
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

def plot_completion_time(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a box-plot visualization for Completion Time.
    
    Args:
        df: Cleaned dataframe with columns 'interface_type' and 'completion_time'.
        output_path: Path to save the figure.
    """
    logger.info(f"Generating completion time visualization: {output_path}")
    
    if df.empty:
        logger.error("Input dataframe is empty. Cannot generate plot.")
        raise ValueError("Input dataframe is empty.")
    
    if 'completion_time' not in df.columns or 'interface_type' not in df.columns:
        raise ValueError("DataFrame must contain 'completion_time' and 'interface_type' columns.")

    plt.figure(figsize=(10, 6))
    # Ensure interface_type is treated as categorical for grouping
    df_plot = df.copy()
    df_plot['interface_type'] = pd.Categorical(df_plot['interface_type'])
    
    ax = df_plot.boxplot(column='completion_time', by='interface_type', grid=False)
    plt.title('Completion Time by Interface Type', fontsize=14)
    plt.suptitle('')  # Remove default title added by pandas boxplot
    plt.xlabel('Interface Type', fontsize=12)
    plt.ylabel('Completion Time (seconds)', fontsize=12)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved completion time plot to {output_path}")

def plot_error_count(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a box-plot visualization for Error Count.
    
    Args:
        df: Cleaned dataframe with columns 'interface_type' and 'error_count'.
        output_path: Path to save the figure.
    """
    logger.info(f"Generating error count visualization: {output_path}")
    
    if df.empty:
        logger.error("Input dataframe is empty. Cannot generate plot.")
        raise ValueError("Input dataframe is empty.")
    
    if 'error_count' not in df.columns or 'interface_type' not in df.columns:
        raise ValueError("DataFrame must contain 'error_count' and 'interface_type' columns.")

    plt.figure(figsize=(10, 6))
    df_plot = df.copy()
    df_plot['interface_type'] = pd.Categorical(df_plot['interface_type'])
    
    ax = df_plot.boxplot(column='error_count', by='interface_type', grid=False)
    plt.title('Error Count by Interface Type', fontsize=14)
    plt.suptitle('')
    plt.xlabel('Interface Type', fontsize=12)
    plt.ylabel('Error Count', fontsize=12)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved error count plot to {output_path}")

def plot_sus_score(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a box-plot visualization for SUS (System Usability Scale) Score.
    
    Args:
        df: Cleaned dataframe with columns 'interface_type' and 'sus_score'.
        output_path: Path to save the figure.
    """
    logger.info(f"Generating SUS score visualization: {output_path}")
    
    if df.empty:
        logger.error("Input dataframe is empty. Cannot generate plot.")
        raise ValueError("Input dataframe is empty.")
    
    if 'sus_score' not in df.columns or 'interface_type' not in df.columns:
        raise ValueError("DataFrame must contain 'sus_score' and 'interface_type' columns.")

    plt.figure(figsize=(10, 6))
    df_plot = df.copy()
    df_plot['interface_type'] = pd.Categorical(df_plot['interface_type'])
    
    # Create boxplot grouped by interface_type
    ax = df_plot.boxplot(column='sus_score', by='interface_type', grid=False)
    
    plt.title('System Usability Scale (SUS) Score by Interface Type', fontsize=14)
    plt.suptitle('')  # Remove default pandas title
    plt.xlabel('Interface Type', fontsize=12)
    plt.ylabel('SUS Score (0-100)', fontsize=12)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved SUS score plot to {output_path}")

def main() -> None:
    """
    CLI entry point to generate visualizations from cleaned data.
    Expects cleaned_sessions.csv in data/processed/ and outputs to figures/.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualization plots from cleaned data.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_sessions.csv",
        help="Path to the cleaned sessions CSV file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="figures",
        help="Directory to save output figures."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Data loaded. Shape: {df.shape}")
    
    # Ensure required columns exist
    required_cols = ['interface_type', 'completion_time', 'error_count', 'sus_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Generate plots
    plot_completion_time(df, str(output_dir / "completion_time.png"))
    plot_error_count(df, str(output_dir / "error_count.png"))
    plot_sus_score(df, str(output_dir / "sus_score.png"))
    
    logger.info("All visualizations generated successfully.")

if __name__ == "__main__":
    main()
