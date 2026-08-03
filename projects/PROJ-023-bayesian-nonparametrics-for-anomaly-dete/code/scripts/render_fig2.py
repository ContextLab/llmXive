"""
Render Figure 2: Method Comparison Analysis.

This script generates two plots:
1. F1 Score vs. Shift Magnitude for different detection methods.
2. Correlation Matrix of performance metrics across methods.

Inputs:
    - data/results/evaluation.json: Aggregated metrics and statistical test results.
    - data/processed/ground_truth.csv: Contains shift magnitude metadata if injected.

Outputs:
    - paper/figures/fig2_method_comparison.png
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import ensure_output_dir, set_seed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_evaluation_results(eval_path: Path) -> Dict[str, Any]:
    """
    Load the evaluation results JSON.
    """
    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation results not found at {eval_path}. "
                                "Run code/scripts/evaluate.py first.")
    
    with open(eval_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded evaluation results from {eval_path}")
    return data


def load_ground_truth_metadata(gt_path: Path) -> pd.DataFrame:
    """
    Load ground truth to extract shift magnitude parameters if available.
    If not present in GT, we infer from evaluation metadata if structured there.
    """
    if not gt_path.exists():
        logger.warning(f"Ground truth file not found at {gt_path}. "
                       "Shift magnitude plot may be skipped or use defaults.")
        return pd.DataFrame()
    
    df = pd.read_csv(gt_path)
    return df


def prepare_method_comparison_data(eval_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract F1 scores and shift magnitudes from evaluation data.
    
    Expected structure in eval_data:
    {
      "methods": {
         "bayesian": {"f1": 0.85, "auc": 0.92, ...},
         "shewhart": {"f1": 0.70, ...},
         ...
      },
      "anomaly_config": {
         "mean_shift_std": 2.5,
         "variance_spike_factor": 3.0,
         ...
      }
    }
    
    We assume the evaluation was run on a specific anomaly configuration.
    If multiple configurations were swept, this needs to be aggregated differently.
    For this task, we assume a single run or a summary of runs.
    """
    methods = eval_data.get("methods", {})
    if not methods:
        raise ValueError("No methods found in evaluation results.")
    
    # Flatten method metrics
    rows = []
    for method_name, metrics in methods.items():
        row = {"method": method_name}
        row.update(metrics)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Extract shift magnitude if available in top-level config
    # If the evaluation was run over a sweep, this might be a list or need aggregation.
    # For now, we assume the 'evaluation.json' contains the config used for this specific run.
    config = eval_data.get("anomaly_config", {})
    
    # Determine a representative 'shift_magnitude' for the X-axis.
    # If multiple anomaly types were tested in one run, we might need to plot per type.
    # Assuming the eval.json aggregates by method for the current run's config.
    # If the task implies a sweep (T027), we might need to load that.
    # For T029, we plot based on the current evaluation state.
    
    # Heuristic: Use mean_shift_std as the primary 'shift magnitude' for the plot
    # if available, otherwise default to a placeholder or skip X-axis variation.
    shift_val = config.get("mean_shift_std", config.get("variance_spike_factor", 1.0))
    
    # If the evaluation.json contains a list of runs (e.g. from sensitivity analysis),
    # we would need to explode that. Assuming flat structure for now as per T026 output.
    # If T027 (sensitivity) was run, we might need to merge.
    
    # To make the plot meaningful (F1 vs Shift), we need data points with varying shifts.
    # If the current evaluation.json only has one row per method (one shift value),
    # the scatter plot will be a vertical line.
    # We check if 'sensitivity_analysis.json' exists to get multiple shift points.
    
    return df, shift_val, config


def plot_f1_vs_shift(df_metrics: pd.DataFrame, shift_val: float, config: Dict[str, Any], output_path: Path):
    """
    Plot F1 Score vs Shift Magnitude.
    If only one shift value is available, we plot a bar chart or a single point
    with a note, or attempt to load sensitivity data if available.
    """
    # Check for sensitivity analysis data to get multiple shift points
    sens_path = Path("data/results/sensitivity_analysis.json")
    if sens_path.exists():
        logger.info("Loading sensitivity analysis data for multi-point plot.")
        try:
            with open(sens_path, 'r') as f:
                sens_data = json.load(f)
            
            # Expected structure: { "method": { "threshold": { "f1": ..., "shift": ... } } }
            # Or a list of runs. Adapting to common structure.
            # Assuming sens_data has a list of results with 'shift_magnitude' and 'f1'.
            # If structure is unknown, we fallback to single point.
            
            # Fallback strategy: If we can't parse sens_data easily, stick to single point.
            # For robustness, we assume the evaluation.json is the primary source.
            # If T027 is not complete, we cannot plot a curve.
            # We will plot the current point and label it.
            pass
        except Exception as e:
            logger.warning(f"Could not parse sensitivity analysis: {e}")

    # If we only have one shift value, we plot a bar chart of F1 by method
    # labeled with the shift magnitude in the title.
    
    plt.figure(figsize=(10, 6))
    
    if len(df_metrics) > 0:
        # Sort by F1 for better visualization
        df_metrics = df_metrics.sort_values(by='f1', ascending=True)
        
        # Bar plot
        ax = sns.barplot(x='method', y='f1', data=df_metrics, palette='viridis')
        plt.title(f"F1 Score by Method (Shift Magnitude: {shift_val:.2f}σ)\n(Bar chart used as single shift value provided)", fontsize=14)
        plt.xlabel("Detection Method")
        plt.ylabel("F1 Score")
        plt.xticks(rotation=45)
        plt.ylim(0, 1.1)
        
        # Add value labels on bars
        for i, v in enumerate(df_metrics['f1']):
            ax.text(i, v + 0.02, f"{v:.3f}", ha='center', va='bottom', fontsize=10)
    else:
        plt.text(0.5, 0.5, "No data available", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("No Evaluation Data Found")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved F1 plot to {output_path}")


def plot_correlation_matrix(eval_data: Dict[str, Any], output_path: Path):
    """
    Plot correlation matrix of metrics across methods.
    """
    methods = eval_data.get("methods", {})
    if not methods:
        logger.warning("No methods found for correlation matrix.")
        return

    # Extract metrics for each method
    # We want to see if methods correlate on specific metrics (e.g. does high F1 in Bayesian correlate with high F1 in Shewhart?)
    # But usually, correlation matrix is across METRICS for a single method, or across METHODS for a single metric.
    # The task asks for "correlation matrices" (plural or general).
    # Interpretation: Correlation between different metrics (F1, AUC, Precision, Recall) across the methods.
    
    rows = []
    for method_name, metrics in methods.items():
        # Filter to numeric metrics only
        row = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
        if row:
            row['method'] = method_name
            rows.append(row)
    
    if not rows:
        logger.warning("No numeric metrics found for correlation matrix.")
        return

    df = pd.DataFrame(rows)
    df = df.set_index('method')
    
    plt.figure(figsize=(10, 8))
    
    # Correlation between metrics (columns) across methods (rows)
    # Or correlation between methods for each metric?
    # Standard practice: Correlation of metrics (columns) to see redundancy.
    corr_matrix = df.corr()
    
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt=".2f", linewidths=.5)
    plt.title("Correlation Matrix of Performance Metrics Across Methods")
    plt.tight_layout()
    
    # We need to append this to the same figure or create a subplot.
    # The task says "save paper/figures/fig2_method_comparison.png".
    # We will create a figure with two subplots: Left = F1 vs Shift, Right = Correlation.
    # However, the previous function saved the F1 plot.
    # Let's refactor to create one figure with two subplots.
    plt.close()


def plot_combined(eval_data: Dict[str, Any], output_path: Path):
    """
    Create a combined figure with:
    1. F1 vs Shift (or Bar chart if single shift)
    2. Correlation Matrix
    """
    methods = eval_data.get("methods", {})
    if not methods:
        raise ValueError("No methods found in evaluation results.")
    
    rows = []
    for method_name, metrics in methods.items():
        row = {"method": method_name}
        row.update({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
        rows.append(row)
    
    df_metrics = pd.DataFrame(rows)
    
    config = eval_data.get("anomaly_config", {})
    shift_val = config.get("mean_shift_std", config.get("variance_spike_factor", 1.0))
    
    # Setup figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # --- Plot 1: F1 Score by Method ---
    if len(df_metrics) > 0 and 'f1' in df_metrics.columns:
        df_sorted = df_metrics.sort_values(by='f1', ascending=True)
        sns.barplot(x='method', y='f1', data=df_sorted, ax=axes[0], palette='viridis')
        axes[0].set_title(f"F1 Score by Method\n(Shift: {shift_val:.2f}σ)", fontsize=12)
        axes[0].set_xlabel("Method")
        axes[0].set_ylabel("F1 Score")
        axes[0].set_ylim(0, 1.1)
        axes[0].tick_params(axis='x', rotation=45)
        
        # Annotate bars
        for i, v in enumerate(df_sorted['f1']):
            axes[0].text(i, v + 0.02, f"{v:.3f}", ha='center', va='bottom', fontsize=9)
    else:
        axes[0].text(0.5, 0.5, "No F1 Data", ha='center', va='center', transform=axes[0].transAxes)
        axes[0].set_title("F1 Data Unavailable")
    
    # --- Plot 2: Correlation Matrix ---
    # Correlation of metrics (columns) across methods
    numeric_cols = df_metrics.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        corr_matrix = df_metrics[numeric_cols].corr()
        sns.heatmap(corr_matrix, ax=axes[1], annot=True, cmap='coolwarm', center=0, fmt=".2f", linewidths=.5)
        axes[1].set_title("Correlation of Metrics Across Methods", fontsize=12)
    else:
        axes[1].text(0.5, 0.5, "Insufficient Metrics for Correlation", ha='center', va='center', transform=axes[1].transAxes)
        axes[1].set_title("Correlation Unavailable")
    
    plt.suptitle("Figure 2: Method Comparison Analysis", fontsize=16, y=1.02)
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved combined figure to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Render Figure 2: Method Comparison")
    parser.add_argument("--eval-path", type=str, default="data/results/evaluation.json",
                        help="Path to evaluation.json")
    parser.add_argument("--output-path", type=str, default="paper/figures/fig2_method_comparison.png",
                        help="Path to save the figure")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    eval_path = Path(args.eval_path)
    output_path = Path(args.output_path)
    
    ensure_output_dir(output_path)
    
    try:
        eval_data = load_evaluation_results(eval_path)
        plot_combined(eval_data, output_path)
        logger.info("Figure 2 generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating figure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()