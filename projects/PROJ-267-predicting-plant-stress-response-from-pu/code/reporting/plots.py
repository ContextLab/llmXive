import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from utils.logging_config import get_logger, log_warning
from utils.config import get_project_root, get_results_path

logger = get_logger(__name__)

def _validate_array_variance(arr: np.ndarray, name: str = "array") -> bool:
    """
    Validate that the input array has non-zero variance.
    
    Args:
        arr: The numpy array to validate.
        name: A descriptive name for the array (for logging).
        
    Returns:
        True if variance > 0, False otherwise.
        
    Raises:
        ValueError: If the array is empty or has zero variance.
    """
    if arr is None:
        raise ValueError(f"{name} is None.")
        
    arr = np.asarray(arr)
    
    if arr.size == 0:
        raise ValueError(f"{name} is empty (size 0). Cannot generate plot.")
        
    if np.isnan(arr).all():
        raise ValueError(f"{name} contains only NaN values. Cannot generate plot.")
        
    variance = np.var(arr)
    
    if variance == 0.0:
        msg = f"Variance of {name} is zero (all values identical: {arr[0]}). Skipping plot generation to prevent runtime errors."
        log_warning(msg)
        return False
        
    return True

def plot_scatter_predicted_vs_actual(
    predicted: np.ndarray,
    actual: np.ndarray,
    title: str = "Predicted vs Actual",
    output_path: Optional[Path] = None
) -> Optional[plt.Figure]:
    """
    Generate a scatter plot of predicted vs actual values with a regression line.
    
    Args:
        predicted: Array of predicted values.
        actual: Array of actual ground truth values.
        title: Plot title.
        output_path: Optional path to save the figure.
        
    Returns:
        The matplotlib Figure object, or None if validation fails.
    """
    try:
        # Validate inputs for non-zero variance
        if not _validate_array_variance(predicted, "predicted"):
            return None
        if not _validate_array_variance(actual, "actual"):
            return None
        
        # Calculate R²
        slope, intercept, r_value, p_value, std_err = stats.linregress(predicted, actual)
        r_squared = r_value ** 2
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x=predicted, y=actual, ax=ax, alpha=0.6, edgecolor="k")
        
        # Plot regression line
        min_val = min(predicted.min(), actual.min())
        max_val = max(predicted.max(), actual.max())
        x_line = np.linspace(min_val, max_val, 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, "r-", label=f"Regression (R²={r_squared:.4f})")
        
        # Plot 1:1 line
        ax.plot([min_val, max_val], [min_val, max_val], "g--", label="Ideal (1:1)")
        
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)
        
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Scatter plot saved to {output_path}")
        
        return fig
        
    except Exception as e:
        logger.error(f"Error generating scatter plot: {e}", exc_info=True)
        raise

def plot_cross_stress_heatmap(
    metrics_data: Dict[str, Dict[str, float]],
    metric_name: str = "R2",
    output_path: Optional[Path] = None
) -> Optional[plt.Figure]:
    """
    Generate a heatmap for cross-stress evaluation metrics.
    
    Args:
        metrics_data: Dictionary mapping (source, target) pairs to metric values.
        metric_name: The metric key to visualize (e.g., 'R2', 'RMSE').
        output_path: Optional path to save the figure.
        
    Returns:
        The matplotlib Figure object, or None if validation fails.
    """
    try:
        if not metrics_data:
            log_warning("metrics_data is empty. Skipping heatmap generation.")
            return None
        
        # Reshape data into a matrix
        sources = sorted(list(set(k[0] for k in metrics_data.keys())))
        targets = sorted(list(set(k[1] for k in metrics_data.keys())))
        
        if not sources or not targets:
            log_warning("Could not determine sources or targets for heatmap.")
            return None
        
        matrix = np.zeros((len(sources), len(targets)))
        
        for i, src in enumerate(sources):
            for j, tgt in enumerate(targets):
                val = metrics_data.get((src, tgt), {}).get(metric_name, np.nan)
                matrix[i, j] = val
        
        # Check for non-zero variance in the matrix (to avoid constant color maps)
        if not _validate_array_variance(matrix, "heatmap matrix"):
            return None

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".2f",
            cmap="viridis",
            xticklabels=targets,
            yticklabels=sources,
            ax=ax,
            cbar_kws={'label': metric_name}
        )
        
        ax.set_title(f"Cross-Stress {metric_name} Heatmap")
        ax.set_xlabel("Target Stress")
        ax.set_ylabel("Source Stress")
        
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Heatmap saved to {output_path}")
        
        return fig
        
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}", exc_info=True)
        raise

def plot_feature_importance(
    feature_names: List[str],
    importance_scores: List[float],
    top_n: int = 10,
    output_path: Optional[Path] = None
) -> Optional[plt.Figure]:
    """
    Generate a bar chart for feature importance.
    
    Args:
        feature_names: List of feature names.
        importance_scores: List of corresponding importance scores.
        top_n: Number of top features to display.
        output_path: Optional path to save the figure.
        
    Returns:
        The matplotlib Figure object, or None if validation fails.
    """
    try:
        if not feature_names or not importance_scores:
            log_warning("Feature names or importance scores are empty. Skipping plot.")
            return None
        
        if len(feature_names) != len(importance_scores):
            raise ValueError("feature_names and importance_scores must have the same length.")
        
        # Sort and slice
        combined = sorted(zip(feature_names, importance_scores), key=lambda x: x[1], reverse=True)
        top_features = combined[:top_n]
        
        names = [x[0] for x in top_features]
        scores = np.array([x[1] for x in top_features])
        
        # Validate scores variance
        if not _validate_array_variance(scores, "importance scores"):
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        # Sort for display if not already sorted by score (they are, but just in case)
        y_pos = np.arange(len(names))
        ax.barh(y_pos, scores, align='center')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.invert_yaxis()  # Labels read top-to-bottom
        ax.set_xlabel('Importance Score')
        ax.set_title(f'Top {top_n} Most Important Features')
        
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Feature importance plot saved to {output_path}")
        
        return fig
        
    except Exception as e:
        logger.error(f"Error generating feature importance plot: {e}", exc_info=True)
        raise

def generate_all_plots(
    results_dir: Optional[Path] = None,
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Orchestrates the generation of all required plots.
    
    Args:
        results_dir: Directory to save plots. Defaults to project results path.
        overwrite: Whether to overwrite existing files.
        
    Returns:
        Dictionary mapping plot types to file paths.
    """
    project_root = get_project_root()
    if results_dir is None:
        results_dir = get_results_path()
        
    plots_dir = results_dir / "figures"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    output_files = {}
    
    # 1. Scatter Plot
    try:
        # Load metrics from results
        within_stress_path = results_dir / "within_stress_metrics.json"
        if within_stress_path.exists():
            with open(within_stress_path, 'r') as f:
                within_data = json.load(f)
            
            # Extract actual/predicted if available, or construct from summary
            # Assuming the structure contains lists of predictions/actuals or we need to load the model
            # Since the specific structure of within_stress_metrics.json varies, we attempt to load
            # a paired file if it exists, or skip if data is insufficient for plotting.
            
            # Fallback: Check for a specific predictions file generated by train.py
            preds_path = results_dir / "predictions_within_stress.csv"
            if preds_path.exists():
                df = pd.read_csv(preds_path)
                if 'actual' in df.columns and 'predicted' in df.columns:
                    fig = plot_scatter_predicted_vs_actual(
                        df['predicted'].values,
                        df['actual'].values,
                        title="Within-Stress: Predicted vs Actual",
                        output_path=plots_dir / "scatter_within_stress.png"
                    )
                    if fig:
                        output_files['scatter_within_stress'] = str(plots_dir / "scatter_within_stress.png")
                else:
                    log_warning("predictions_within_stress.csv missing 'actual' or 'predicted' columns.")
            else:
                log_warning("Could not locate prediction data for scatter plot.")
        else:
            log_warning("within_stress_metrics.json not found.")
    except Exception as e:
        log_warning(f"Skipping scatter plot generation: {e}")
        
    # 2. Heatmap
    try:
        cross_stress_path = results_dir / "cross_stress_metrics.json"
        if cross_stress_path.exists():
            with open(cross_stress_path, 'r') as f:
                cross_data = json.load(f)
            
            # Flatten structure if needed. Assuming { "pairs": [ { "source": A, "target": B, "R2": val } ] }
            # Or direct dict if saved that way.
            # We adapt based on common output of T024
            
            metrics_dict = {}
            if "pairs" in cross_data:
                for pair in cross_data["pairs"]:
                    key = (pair["source"], pair["target"])
                    metrics_dict[key] = {"R2": pair.get("R2"), "RMSE": pair.get("RMSE")}
            else:
                # Assume direct dict structure
                metrics_dict = cross_data
                
            fig = plot_cross_stress_heatmap(metrics_dict, metric_name="R2", output_path=plots_dir / "heatmap_cross_stress.png")
            if fig:
                output_files['heatmap_cross_stress'] = str(plots_dir / "heatmap_cross_stress.png")
        else:
            log_warning("cross_stress_metrics.json not found.")
    except Exception as e:
        log_warning(f"Skipping heatmap generation: {e}")
        
    # 3. Feature Importance
    try:
        importance_path = results_dir / "feature_importance.json"
        if importance_path.exists():
            with open(importance_path, 'r') as f:
                imp_data = json.load(f)
            
            # Assuming structure: { "features": [...], "importance": [...] }
            if "features" in imp_data and "importance" in imp_data:
                fig = plot_feature_importance(
                    imp_data["features"],
                    imp_data["importance"],
                    top_n=15,
                    output_path=plots_dir / "bar_feature_importance.png"
                )
                if fig:
                    output_files['feature_importance'] = str(plots_dir / "bar_feature_importance.png")
            else:
                log_warning("feature_importance.json missing required keys.")
        else:
            log_warning("feature_importance.json not found.")
    except Exception as e:
        log_warning(f"Skipping feature importance plot generation: {e}")
        
    return output_files

def main():
    """Entry point for generating all plots."""
    logger.info("Starting plot generation...")
    try:
        results = generate_all_plots()
        logger.info(f"Generated {len(results)} plots: {list(results.keys())}")
    except Exception as e:
        logger.error(f"Plot generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()