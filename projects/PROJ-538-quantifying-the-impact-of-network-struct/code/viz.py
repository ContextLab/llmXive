import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import json
import logging
from .utils import get_logger, log_audit_event

# Ensure output directory exists
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class VisualizationEngine:
    """
    Handles generation of all visualization artifacts.
    Currently implements:
      - Scatter plots with regression lines (T033)
      - Correlation heatmaps (T034)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("VisualizationEngine")
        # Set high DPI for publication quality
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        sns.set_theme(style="whitegrid", context="talk")

    def generate_scatter_plot(
        self,
        x_data: List[float],
        y_data: List[float],
        x_label: str,
        y_label: str,
        title: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """Generate a scatter plot with regression line (T033)."""
        if output_path is None:
            output_path = OUTPUT_DIR / "scatter_plot.png"

        plt.figure(figsize=(10, 8))
        sns.regplot(x=x_data, y=y_data, scatter_kws={'alpha':0.6}, line_kws={'color':'red'})
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        self.logger.info(f"Scatter plot saved to {output_path}")
        log_audit_event("VISUALIZATION", "scatter_plot_generated", {"path": str(output_path)})
        return output_path

    def generate_correlation_heatmap(
        self,
        metrics_data: Dict[str, List[float]],
        conductivity_data: List[float],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Generate a correlation heatmap for all topological metrics vs thermal conductivity.
        
        Args:
            metrics_data: Dictionary mapping metric name (str) to list of values (float).
            conductivity_data: List of thermal conductivity values (float).
            output_path: Path to save the heatmap image. Defaults to data/processed/correlation_heatmap.png.
        
        Returns:
            Path to the generated image file.
        
        Verification:
            - File must exist at output_path.
            - File must be 300 DPI.
            - Grid must contain labels for all metrics and conductivity.
        """
        if output_path is None:
            output_path = OUTPUT_DIR / "correlation_heatmap.png"

        # Ensure we have data
        if not metrics_data or not conductivity_data:
            self.logger.warning("No data provided for correlation heatmap. Generating empty placeholder.")
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "No Data Available", ha='center', va='center')
            plt.axis('off')
            plt.savefig(output_path, dpi=300)
            plt.close()
            return output_path

        # Combine data into a DataFrame-like structure for correlation
        # We expect all lists to be of the same length
        n_samples = len(conductivity_data)
        if any(len(v) != n_samples for v in metrics_data.values()):
            self.logger.warning("Metric lists and conductivity data have mismatched lengths. Truncating to shortest.")
            min_len = min(len(v) for v in metrics_data.values()) + 1 # +1 for conductivity
            min_len = min(min_len, n_samples)
            conductivity_data = conductivity_data[:min_len]
            metrics_data = {k: v[:min_len] for k, v in metrics_data.items()}

        # Prepare correlation matrix data
        # Columns: Metric names + "Thermal_Conductivity"
        all_labels = list(metrics_data.keys()) + ["Thermal_Conductivity"]
        all_values = list(metrics_data.values()) + [conductivity_data]
        
        # Calculate correlation matrix
        corr_matrix = np.corrcoef(all_values)
        
        # Create the heatmap
        plt.figure(figsize=(12, 10))
        ax = sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".3f",
            cmap='coolwarm',
            square=True,
            linewidths=.5,
            xticklabels=all_labels,
            yticklabels=all_labels,
            vmin=-1, vmax=1,
            cbar_kws={'label': 'Correlation Coefficient'}
        )
        
        plt.title("Correlation Heatmap: Network Metrics vs Thermal Conductivity", pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        # Save with explicit 300 DPI
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Correlation heatmap saved to {output_path} (300 DPI)")
        log_audit_event("VISUALIZATION", "heatmap_generated", {
            "path": str(output_path),
            "metrics_count": len(metrics_data),
            "samples": n_samples
        })
        
        return output_path

def run_visualization_pipeline(
    metrics_results: Dict[str, List[float]],
    conductivity_values: List[float],
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Orchestrates the generation of all required visualizations.
    
    Args:
        metrics_results: Dict of metric_name -> list of values from MetricCalculator.
        conductivity_values: List of thermal conductivity values.
        output_dir: Optional override for output directory.
        
    Returns:
        Dictionary mapping visualization type to output Path.
    """
    engine = VisualizationEngine()
    results = {}

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Re-bind the engine's default output dir if needed, 
        # but for now we pass explicit paths to methods.
    
    # 1. Generate Heatmap (T034)
    heatmap_path = engine.generate_correlation_heatmap(
        metrics_data=metrics_results,
        conductivity_data=conductivity_values,
        output_path=(output_dir / "correlation_heatmap.png") if output_dir else None
    )
    results["heatmap"] = heatmap_path

    # 2. Generate Scatter Plots for each metric (T033)
    for metric_name, values in metrics_results.items():
        scatter_path = engine.generate_scatter_plot(
            x_data=values,
            y_data=conductivity_values,
            x_label=metric_name,
            y_label="Thermal Conductivity (W/mK)",
            title=f"{metric_name} vs Thermal Conductivity",
            output_path=(output_dir / f"scatter_{metric_name}.png") if output_dir else None
        )
        results[f"scatter_{metric_name}"] = scatter_path

    return results
