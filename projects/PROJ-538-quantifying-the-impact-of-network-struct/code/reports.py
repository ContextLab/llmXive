import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from .config import Config
from .utils import get_logger, log_audit_event

logger = get_logger(__name__)

def generate_sanity_check_pdf(
    processed_dir: Path,
    output_path: Path,
    max_plots: int = 5
) -> None:
    """
    Generate a sanity check PDF containing the first N scatter plots and their
    corresponding raw data points to verify VisualizationEngine integrity.

    This task ensures that the visualization engine is not plotting NaNs or
    empty arrays, addressing reviewer concerns about data integrity.

    Args:
        processed_dir: Path to the directory containing processed data files.
        output_path: Path where the sanity check PDF will be saved.
        max_plots: Maximum number of plots to include in the PDF (default 5).
    """
    logger.info(f"Generating sanity check PDF with up to {max_plots} plots")

    # Load correlation results
    correlation_file = processed_dir / "correlation_results.json"
    if not correlation_file.exists():
        logger.error(f"Correlation results file not found: {correlation_file}")
        raise FileNotFoundError(f"Missing correlation results: {correlation_file}")

    with open(correlation_file, 'r') as f:
        correlation_data = json.load(f)

    # Extract scatter plot data (assuming structure from T033)
    # The data should contain x (metric), y (thermal conductivity), and labels
    if "scatter_data" not in correlation_data:
        logger.error("Scatter plot data not found in correlation results")
        raise ValueError("Scatter plot data missing from correlation results")

    scatter_data = correlation_data["scatter_data"]

    if not isinstance(scatter_data, list) or len(scatter_data) == 0:
        logger.error("Scatter data is empty or not a list")
        raise ValueError("Scatter data is empty or malformed")

    # Limit to max_plots
    plots_to_process = scatter_data[:max_plots]
    logger.info(f"Processing {len(plots_to_process)} plots for sanity check")

    # Create PDF with subplots
    # Use a grid layout: 2 columns, ceil(N/2) rows
    n_plots = len(plots_to_process)
    n_rows = (n_plots + 1) // 2
    n_cols = 2

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 6 * n_rows))

    # Handle case where there's only one subplot (axes is not iterable)
    if n_plots == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)

    valid_plot_count = 0

    for idx, plot_data in enumerate(plots_to_process):
        row = idx // n_cols
        col = idx % n_cols
        ax = axes[row, col]

        # Extract data points
        x_values = plot_data.get("x_values", [])
        y_values = plot_data.get("y_values", [])
        metric_name = plot_data.get("metric_name", "Unknown Metric")
        correlation_coeff = plot_data.get("correlation_coefficient", "N/A")

        # Check for NaNs or empty arrays
        if not x_values or not y_values:
            ax.text(0.5, 0.5, "ERROR: Empty Data Array",
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=12, color='red', fontweight='bold')
            ax.set_title(f"{metric_name}\nStatus: INVALID")
            continue

        x_arr = np.array(x_values)
        y_arr = np.array(y_values)

        if np.any(np.isnan(x_arr)) or np.any(np.isnan(y_arr)):
            nan_count_x = np.sum(np.isnan(x_arr))
            nan_count_y = np.sum(np.isnan(y_arr))
            ax.text(0.5, 0.5, f"ERROR: NaNs detected\nX: {nan_count_x}, Y: {nan_count_y}",
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=12, color='red', fontweight='bold')
            ax.set_title(f"{metric_name}\nStatus: CONTAINS NaNs")
            continue

        # Plot the data
        ax.scatter(x_arr, y_arr, alpha=0.7, edgecolors='w', linewidth=0.5, s=50)
        ax.set_xlabel("Metric Value")
        ax.set_ylabel("Thermal Conductivity (W/m·K)")
        ax.set_title(f"{metric_name}\nr = {correlation_coeff}")
        ax.grid(True, alpha=0.3)
        valid_plot_count += 1

        # Add data point count annotation
        ax.text(0.02, 0.98, f"N = {len(x_arr)}",
                transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Hide unused subplots
    for i in range(valid_plot_count, n_plots):
        row = i // n_cols
        col = i % n_cols
        if row < n_rows and col < n_cols:
            axes[row, col].axis('off')

    # Add overall title
    fig.suptitle(f"Visual Verification Sanity Check ({valid_plot_count}/{max_plots} Valid Plots)",
                 fontsize=16, fontweight='bold', y=1.02)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PDF
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, format='pdf', bbox_inches='tight')
    plt.close()

    logger.info(f"Sanity check PDF saved to: {output_path}")

    # Log audit event
    log_audit_event(
        event_type="sanity_check_generated",
        details={
            "output_file": str(output_path),
            "plots_generated": valid_plot_count,
            "plots_requested": max_plots
        }
    )

    return valid_plot_count

def run_report_generation_pipeline(
    config: Config
) -> Dict[str, Any]:
    """
    Run the full report generation pipeline including sanity checks.

    Args:
        config: Configuration object with paths and settings.

    Returns:
        Dictionary containing report generation results.
    """
    processed_dir = config.paths.processed_dir
    output_dir = processed_dir

    results = {
        "sanity_check_pdf": None,
        "final_report": None,
        "status": "success",
        "errors": []
    }

    try:
        # Generate sanity check PDF
        sanity_pdf_path = output_dir / "sanity_check_verification.pdf"
        valid_plots = generate_sanity_check_pdf(
            processed_dir=processed_dir,
            output_path=sanity_pdf_path,
            max_plots=5
        )
        results["sanity_check_pdf"] = str(sanity_pdf_path)
        results["valid_plots_count"] = valid_plots

        if valid_plots == 0:
            results["status"] = "warning"
            results["errors"].append("No valid plots found in sanity check")
            logger.warning("Sanity check completed but no valid plots were generated")

    except Exception as e:
        logger.error(f"Error generating sanity check PDF: {str(e)}")
        results["status"] = "error"
        results["errors"].append(f"Sanity check failed: {str(e)}")

    return results

def main():
    """Main entry point for report generation."""
    from .config import Config
    from .utils import get_logger

    logger = get_logger(__name__)
    logger.info("Starting report generation pipeline")

    config = Config()
    results = run_report_generation_pipeline(config)

    logger.info(f"Report generation completed with status: {results['status']}")
    if results.get("sanity_check_pdf"):
        logger.info(f"Sanity check PDF generated: {results['sanity_check_pdf']}")

    return results

if __name__ == "__main__":
    main()