"""
Plot generation utilities for anomaly detection evaluation.

This module provides functions to generate and save ROC curves,
Precision-Recall curves, and other evaluation visualizations.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score

# Configure matplotlib for non-interactive backend
plt.switch_backend('Agg')

# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("notebook")

@dataclass
class ROCPlotConfig:
    """Configuration for ROC curve plots."""
    title: str = "ROC Curve - Anomaly Detection"
    xlabel: str = "False Positive Rate"
    ylabel: str = "True Positive Rate"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    save_format: str = "png"
    color: str = "#1f77b4"
    linewidth: int = 2
    grid: bool = True
    show_auc: bool = True
    show_diagonal: bool = True
    legend_position: str = "lower right"
    
@dataclass
class PRPlotConfig:
    """Configuration for Precision-Recall curve plots."""
    title: str = "Precision-Recall Curve - Anomaly Detection"
    xlabel: str = "Recall"
    ylabel: str = "Precision"
    figsize: Tuple[int, int] = (10, 8)
    dpi: int = 150
    save_format: str = "png"
    color: str = "#ff7f0e"
    linewidth: int = 2
    grid: bool = True
    show_ap: bool = True
    legend_position: str = "lower left"
    
@dataclass
class EvaluationPlotConfig:
    """Configuration for combined evaluation plots."""
    output_dir: Path = field(default_factory=lambda: Path("paper/figures"))
    roc_config: Optional[ROCPlotConfig] = None
    pr_config: Optional[PRPlotConfig] = None
    dpi: int = 150
    
def generate_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    config: Optional[ROCPlotConfig] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Generate ROC curve data from true labels and anomaly scores.
    
    Args:
        y_true: Binary array of true labels (1 = anomaly, 0 = normal)
        y_scores: Array of anomaly scores (higher = more anomalous)
        config: Optional ROCPlotConfig for customization
    
    Returns:
        Tuple of (fpr, tpr, thresholds, auc_score)
    """
    if config is None:
        config = ROCPlotConfig()
    
    # Validate inputs
    if len(y_true) != len(y_scores):
        raise ValueError(f"y_true and y_scores must have same length: "
                       f"{len(y_true)} vs {len(y_scores)}")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")
    
    # Compute ROC curve
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    
    return fpr, tpr, thresholds, roc_auc

def save_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_path: Path,
    config: Optional[ROCPlotConfig] = None
) -> Path:
    """
    Generate and save ROC curve as PNG file.
    
    Args:
        y_true: Binary array of true labels (1 = anomaly, 0 = normal)
        y_scores: Array of anomaly scores (higher = more anomalous)
        output_path: Path to save the PNG file
        config: Optional ROCPlotConfig for customization
    
    Returns:
        Path to the saved PNG file
    """
    if config is None:
        config = ROCPlotConfig()
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate ROC curve data
    fpr, tpr, thresholds, roc_auc = generate_roc_curve(y_true, y_scores, config)
    
    # Create figure
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Plot ROC curve
    ax.plot(
        fpr, tpr,
        color=config.color,
        lw=config.linewidth,
        label=f'ROC curve (AUC = {roc_auc:.4f})'
    )
    
    # Plot diagonal line (random classifier)
    if config.show_diagonal:
        ax.plot(
            [0, 1], [0, 1],
            color='gray',
            lw=1,
            linestyle='--',
            label='Random Classifier'
        )
    
    # Configure plot
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14, fontweight='bold')
    
    if config.grid:
        ax.grid(True, alpha=0.3)
    
    # Add legend
    ax.legend(loc=config.legend_position, fontsize=10)
    
    # Save figure
    fig.savefig(
        output_path,
        format=config.save_format,
        dpi=config.dpi,
        bbox_inches='tight',
        facecolor='white'
    )
    plt.close(fig)
    
    return output_path

def generate_pr_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    config: Optional[PRPlotConfig] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Generate Precision-Recall curve data from true labels and anomaly scores.
    
    Args:
        y_true: Binary array of true labels (1 = anomaly, 0 = normal)
        y_scores: Array of anomaly scores (higher = more anomalous)
        config: Optional PRPlotConfig for customization
    
    Returns:
        Tuple of (precision, recall, thresholds, average_precision)
    """
    if config is None:
        config = PRPlotConfig()
    
    # Validate inputs
    if len(y_true) != len(y_scores):
        raise ValueError(f"y_true and y_scores must have same length: "
                       f"{len(y_true)} vs {len(y_scores)}")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")
    
    # Compute PR curve
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    ap = average_precision_score(y_true, y_scores)
    
    return precision, recall, thresholds, ap

def save_pr_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_path: Path,
    config: Optional[PRPlotConfig] = None
) -> Path:
    """
    Generate and save Precision-Recall curve as PNG file.
    
    Args:
        y_true: Binary array of true labels (1 = anomaly, 0 = normal)
        y_scores: Array of anomaly scores (higher = more anomalous)
        output_path: Path to save the PNG file
        config: Optional PRPlotConfig for customization
    
    Returns:
        Path to the saved PNG file
    """
    if config is None:
        config = PRPlotConfig()
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate PR curve data
    precision, recall, thresholds, ap = generate_pr_curve(y_true, y_scores, config)
    
    # Create figure
    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    
    # Plot PR curve
    ax.plot(
        recall, precision,
        color=config.color,
        lw=config.linewidth,
        label=f'PR curve (AP = {ap:.4f})'
    )
    
    # Configure plot
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel(config.xlabel, fontsize=12)
    ax.set_ylabel(config.ylabel, fontsize=12)
    ax.set_title(config.title, fontsize=14, fontweight='bold')
    
    if config.grid:
        ax.grid(True, alpha=0.3)
    
    # Add legend
    ax.legend(loc=config.legend_position, fontsize=10)
    
    # Save figure
    fig.savefig(
        output_path,
        format=config.save_format,
        dpi=config.dpi,
        bbox_inches='tight',
        facecolor='white'
    )
    plt.close(fig)
    
    return output_path

def generate_evaluation_plots(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    output_dir: Path,
    model_name: str = "DPGMM",
    config: Optional[EvaluationPlotConfig] = None
) -> Dict[str, Path]:
    """
    Generate both ROC and PR curves for evaluation.
    
    Args:
        y_true: Binary array of true labels (1 = anomaly, 0 = normal)
        y_scores: Array of anomaly scores (higher = more anomalous)
        output_dir: Directory to save the PNG files
        model_name: Name of the model for plot titles
        config: Optional EvaluationPlotConfig for customization
    
    Returns:
        Dictionary mapping plot type to saved file path
    """
    if config is None:
        config = EvaluationPlotConfig()
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set defaults if configs not provided
    if config.roc_config is None:
        roc_config = ROCPlotConfig(
            title=f"ROC Curve - {model_name}",
            color="#1f77b4"
        )
    else:
        roc_config = config.roc_config
        roc_config.title = f"ROC Curve - {model_name}"
    
    if config.pr_config is None:
        pr_config = PRPlotConfig(
            title=f"Precision-Recall Curve - {model_name}",
            color="#ff7f0e"
        )
    else:
        pr_config = config.pr_config
        pr_config.title = f"Precision-Recall Curve - {model_name}"
    
    # Generate ROC curve
    roc_path = output_dir / f"{model_name}_roc_curve.png"
    save_roc_curve(y_true, y_scores, roc_path, roc_config)
    
    # Generate PR curve
    pr_path = output_dir / f"{model_name}_pr_curve.png"
    save_pr_curve(y_true, y_scores, pr_path, pr_config)
    
    return {
        "roc": roc_path,
        "pr": pr_path
    }

def main():
    """
    Main function to demonstrate ROC curve generation.
    Creates synthetic data and saves ROC/PR curves to paper/figures/.
    """
    # Import here to avoid circular dependencies
    from pathlib import Path
    import numpy as np
    
    # Create output directory
    output_dir = Path("paper/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic evaluation data
    np.random.seed(42)
    n_samples = 1000
    n_anomalies = 100  # 10% anomaly rate
    
    # Create ground truth labels
    y_true = np.zeros(n_samples, dtype=int)
    anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
    y_true[anomaly_indices] = 1
    
    # Create anomaly scores (higher for anomalies)
    y_scores = np.random.random(n_samples)
    y_scores[anomaly_indices] = np.random.uniform(0.7, 1.0, n_anomalies)
    y_scores[y_true == 0] = np.random.uniform(0.0, 0.5, n_samples - n_anomalies)
    
    # Generate and save plots
    print("Generating ROC and PR curves...")
    paths = generate_evaluation_plots(
        y_true=y_true,
        y_scores=y_scores,
        output_dir=output_dir,
        model_name="DPGMM"
    )
    
    print(f"ROC curve saved to: {paths['roc']}")
    print(f"PR curve saved to: {paths['pr']}")
    
    # Verify files exist
    for plot_type, path in paths.items():
        if path.exists():
            print(f"✓ {plot_type.upper()} plot created successfully ({path.stat().st_size} bytes)")
        else:
            print(f"✗ {plot_type.upper()} plot creation failed")
    
    return paths

if __name__ == "__main__":
    main()
