"""
Script to Render Figure 2: Method Comparison and Correlation Matrices.

This script generates plots comparing the performance of different anomaly
detection methods (F1-score vs. shift magnitude) and displays correlation
matrices of the results.

Author: Research Team
Date: 2026-04-29
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_evaluation_results(path: Path) -> Dict[str, Any]:
    """
    Load evaluation results from a JSON file.

    Args:
        path (Path): Path to the evaluation results JSON file.

    Returns:
        Dict[str, Any]: The loaded results dictionary.
    """
    if not path.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {path}")

    with open(path, 'r') as f:
        results = json.load(f)

    logger.info(f"Loaded evaluation results from {path}")
    return results


def load_ground_truth_metadata(path: Path) -> pd.DataFrame:
    """
    Load ground truth metadata from a CSV file.

    Args:
        path (Path): Path to the ground truth metadata CSV file.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Ground truth metadata file not found: {path}")

    df = pd.read_csv(path)
    logger.info(f"Loaded ground truth metadata from {path}")
    return df


def prepare_method_comparison_data(
    eval_results: Dict[str, Any]
) -> pd.DataFrame:
    """
    Prepare data for method comparison plots.

    Args:
        eval_results (Dict[str, Any]): The evaluation results dictionary.

    Returns:
        pd.DataFrame: DataFrame containing method comparison data.
    """
    methods_data = []

    for method, metrics in eval_results.get('methods', {}).items():
        methods_data.append({
            'method': method,
            'f1_score': metrics.get('f1_score', 0),
            'precision': metrics.get('precision', 0),
            'recall': metrics.get('recall', 0),
            'auc_roc': metrics.get('auc_roc', 0)
        })

    df = pd.DataFrame(methods_data)
    logger.info(f"Prepared data for {len(df)} methods")
    return df


def plot_f1_vs_shift(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "F1-Score vs. Shift Magnitude"
) -> None:
    """
    Plot F1-score vs. shift magnitude (or method comparison).

    Args:
        df (pd.DataFrame): DataFrame with method performance data.
        output_path (Path): Path to save the figure.
        title (str): Title of the plot.
    """
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='method', y='f1_score', palette='viridis')
    plt.xlabel('Method', fontsize=12)
    plt.ylabel('F1-Score', fontsize=12)
    plt.title(title, fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved F1-score plot to {output_path}")


def plot_correlation_matrix(
    df: pd.DataFrame,
    output_path: Path,
    title: str = "Correlation Matrix of Metrics"
) -> None:
    """
    Plot a correlation matrix of the performance metrics.

    Args:
        df (pd.DataFrame): DataFrame with performance metrics.
        output_path (Path): Path to save the figure.
        title (str): Title of the plot.
    """
    # Select numeric columns
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.empty:
        logger.warning("No numeric columns found for correlation matrix")
        return

    corr = numeric_df.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title(title, fontsize=14)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved correlation matrix plot to {output_path}")


def plot_combined(
    df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Plot a combined figure with F1-score comparison and correlation matrix.

    Args:
        df (pd.DataFrame): DataFrame with performance metrics.
        output_path (Path): Path to save the figure.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # F1-score bar plot
    sns.barplot(data=df, x='method', y='f1_score', palette='viridis', ax=axes[0])
    axes[0].set_xlabel('Method', fontsize=12)
    axes[0].set_ylabel('F1-Score', fontsize=12)
    axes[0].set_title('F1-Score Comparison', fontsize=14)
    axes[0].tick_params(axis='x', rotation=45)

    # Correlation heatmap
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f', ax=axes[1])
        axes[1].set_title('Correlation Matrix', fontsize=14)

    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved combined figure to {output_path}")


def main() -> None:
    """
    Main entry point for the Figure 2 rendering script.
    """
    parser = argparse.ArgumentParser(description="Render Figure 2: Method Comparison")
    parser.add_argument(
        "--evaluation",
        type=str,
        default="data/results/evaluation.json",
        help="Path to evaluation results JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="paper/figures/fig2_method_comparison.png",
        help="Path to save the figure"
    )
    args = parser.parse_args()

    eval_path = Path(args.evaluation)
    output_path = Path(args.output)

    try:
        # Load evaluation results
        eval_results = load_evaluation_results(eval_path)

        # Prepare data
        df = prepare_method_comparison_data(eval_results)

        # Plot combined figure
        plot_combined(df, output_path)

    except Exception as e:
        logger.error(f"Failed to render Figure 2: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()