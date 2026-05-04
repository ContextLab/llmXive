"""
Evaluation plots module for anomaly detection visualization.

Provides ROC and PR curve generation with configurable styling options.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ROCPlotConfig:
    """Configuration for ROC curve plots."""
    title: str = "ROC Curve"
    xlabel: str = "False Positive Rate"
    ylabel: str = "True Positive Rate"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    show_grid: bool = True
    show_diagonal: bool = True
    line_color: str = "#1f77b4"
    line_width: float = 2.0
    diagonal_color: str = "#d62728"
    diagonal_linestyle: str = "--"
    save_path: Optional[str] = None

@dataclass
class PRPlotConfig:
    """Configuration for Precision-Recall curve plots."""
    title: str = "Precision-Recall Curve"
    xlabel: str = "Recall"
    ylabel: str = "Precision"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    show_grid: bool = True
    line_color: str = "#2ca02c"
    line_width: float = 2.0
    save_path: Optional[str] = None
    auc_display: bool = True
    auc_position: Tuple[float, float] = (0.05, 0.05)
    auc_fontsize: int = 12

@dataclass
class EvaluationPlotConfig:
    """Configuration for combined evaluation plots."""
    roc_config: Optional[ROCPlotConfig] = None
    pr_config: Optional[PRPlotConfig] = None
    save_directory: str = "paper/figures"
    prefix: str = "evaluation"
    timestamp: bool = True

def compute_pr_curve_points(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold_range: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Precision-Recall curve points.

    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_scores: Anomaly scores (higher = more anomalous)
        threshold_range: Array of thresholds to evaluate (optional)

    Returns:
        Tuple of (precision, recall, thresholds) arrays
    """
    if threshold_range is None:
        thresholds = np.sort(np.unique(y_scores))
    else:
        thresholds = threshold_range

    precision = []
    recall = []

    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)

        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        precision.append(prec)
        recall.append(rec)

    return np.array(precision), np.array(recall), thresholds

def compute_roc_curve_points(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    threshold_range: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ROC curve points.

    Args:
        y_true: Ground truth binary labels (0 or 1)
        y_scores: Anomaly scores (higher = more anomalous)
        threshold_range: Array of thresholds to evaluate (optional)

    Returns:
        Tuple of (fpr, tpr, thresholds) arrays
    """
    if threshold_range is None:
        thresholds = np.sort(np.unique(y_scores))
    else:
        thresholds = threshold_range

    fpr = []
    tpr = []

    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)

        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))

        fpr_val = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        tpr_val = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        fpr.append(fpr_val)
        tpr.append(tpr_val)

    return np.array(fpr), np.array(tpr), thresholds

def compute_auc(precision: np.ndarray, recall: np.ndarray) -> float:
    """
    Compute Area Under the Precision-Recall Curve (AUPRC).

    Args:
        precision: Precision values
        recall: Recall values

    Returns:
        AUC value
    """
    sorted_indices = np.argsort(recall)
    recall_sorted = recall[sorted_indices]
    precision_sorted = precision[sorted_indices]

    auc = np.trapz(precision_sorted, recall_sorted)
    return float(auc)

def generate_pr_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    config: Optional[PRPlotConfig] = None
) -> plt.Figure:
    """
    Generate a Precision-Recall curve plot.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores
        config: Plot configuration (optional)

    Returns:
        matplotlib Figure object
    """
    if config is None:
        config = PRPlotConfig()

    precision, recall, thresholds = compute_pr_curve_points(y_true, y_scores)
    auc_value = compute_auc(precision, recall)

    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    sns.set_style("whitegrid" if config.show_grid else "white")

    ax.plot(recall, precision, color=config.line_color,
            linewidth=config.line_width, label=f'PR Curve (AUC={auc_value:.3f})')
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(config.show_grid)

    if config.auc_display:
        ax.text(config.auc_position[0], config.auc_position[1],
                f'AUC = {auc_value:.3f}', transform=ax.transAxes,
                fontsize=config.auc_fontsize, verticalalignment='bottom')

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    return fig

def save_pr_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_path: str,
    config: Optional[PRPlotConfig] = None
) -> Path:
    """
    Generate and save a Precision-Recall curve plot.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores
        output_path: Path to save the PNG file
        config: Plot configuration (optional)

    Returns:
        Path object of saved file
    """
    if config is None:
        config = PRPlotConfig()

    if config.save_path is None:
        config.save_path = output_path

    fig = generate_pr_curve(y_true, y_scores, config)

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path_obj, dpi=config.dpi, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"PR curve saved to {output_path}")
    return output_path_obj

def generate_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    config: Optional[ROCPlotConfig] = None
) -> plt.Figure:
    """
    Generate a ROC curve plot.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores
        config: Plot configuration (optional)

    Returns:
        matplotlib Figure object
    """
    if config is None:
        config = ROCPlotConfig()

    fpr, tpr, thresholds = compute_roc_curve_points(y_true, y_scores)
    auc_value = compute_auc(tpr, fpr)

    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    sns.set_style("whitegrid" if config.show_grid else "white")

    ax.plot(fpr, tpr, color=config.line_color,
            linewidth=config.line_width, label=f'ROC Curve (AUC={auc_value:.3f})')
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(config.show_grid)

    if config.show_diagonal:
        ax.plot([0, 1], [0, 1], color=config.diagonal_color,
                linestyle=config.diagonal_linestyle, linewidth=1.0)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])

    return fig

def save_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_path: str,
    config: Optional[ROCPlotConfig] = None
) -> Path:
    """
    Generate and save a ROC curve plot.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores
        output_path: Path to save the PNG file
        config: Plot configuration (optional)

    Returns:
        Path object of saved file
    """
    if config is None:
        config = ROCPlotConfig()

    if config.save_path is None:
        config.save_path = output_path

    fig = generate_roc_curve(y_true, y_scores, config)

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path_obj, dpi=config.dpi, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"ROC curve saved to {output_path}")
    return output_path_obj

def generate_evaluation_plots(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    config: Optional[EvaluationPlotConfig] = None
) -> Dict[str, Path]:
    """
    Generate both ROC and PR curve plots and save them.

    Args:
        y_true: Ground truth binary labels
        y_scores: Anomaly scores
        config: Plot configuration (optional)

    Returns:
        Dictionary mapping plot type to saved file path
    """
    if config is None:
        config = EvaluationPlotConfig()

    output_paths = {}
    save_dir = Path(config.save_directory)
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if config.timestamp else ""
    prefix = config.prefix

    if config.pr_config is not None:
        pr_path = save_dir / f"{prefix}_pr_curve_{timestamp}.png"
        output_paths['pr'] = save_pr_curve(y_true, y_scores, str(pr_path), config.pr_config)

    if config.roc_config is not None:
        roc_path = save_dir / f"{prefix}_roc_curve_{timestamp}.png"
        output_paths['roc'] = save_roc_curve(y_true, y_scores, str(roc_path), config.roc_config)

    logger.info(f"Generated {len(output_paths)} evaluation plots")
    return output_paths

def main():
    """Main entry point for testing PR curve generation."""
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 50

    y_true = np.zeros(n_samples, dtype=int)
    y_true[:n_anomalies] = 1

    y_scores = np.random.random(n_samples)
    y_scores[:n_anomalies] = np.random.uniform(0.7, 1.0, n_anomalies)
    y_scores[n_anomalies:] = np.random.uniform(0.0, 0.5, n_samples - n_anomalies)

    pr_config = PRPlotConfig(
        title="Test PR Curve",
        save_path="paper/figures/test_pr_curve.png"
    )
    save_pr_curve(y_true, y_scores, str(pr_config.save_path), pr_config)

    roc_config = ROCPlotConfig(
        title="Test ROC Curve",
        save_path="paper/figures/test_roc_curve.png"
    )
    save_roc_curve(y_true, y_scores, str(roc_config.save_path), roc_config)

    logger.info("Test completed successfully")

if __name__ == "__main__":
    main()
