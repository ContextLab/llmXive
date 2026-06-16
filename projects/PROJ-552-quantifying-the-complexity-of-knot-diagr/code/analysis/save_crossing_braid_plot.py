"""
Save crossing number vs braid index scatter plot to data/plots/crossing_vs_braid.png
with resolution 1200x900 pixels (User Story 2 - T024)
"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for script execution
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
from datetime import datetime
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from analysis.exploratory import load_cleaned_knots, create_stratified_scatter_plot
from reproducibility.logs import log_operation, get_logger


def save_crossing_braid_plot(
    output_path: Path,
    width: int = 1200,
    height: int = 900,
    dpi: int = 100
) -> dict:
    """
    Generate and save crossing number vs braid index scatter plot.

    Args:
        output_path: Path to save the plot (must be .png)
        width: Plot width in pixels (default: 1200)
        height: Plot height in pixels (default: 900)
        dpi: Dots per inch (default: 100)

    Returns:
        dict with 'success', 'output_path', 'width', 'height', 'timestamp'
    """
    logger = get_logger()
    operation_name = "save_crossing_braid_plot"

    # Validate output path
    if output_path.suffix != '.png':
        raise ValueError(f"Output path must be .png file, got: {output_path.suffix}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load cleaned knot data
    logger.info(f"Loading cleaned knot data for {operation_name}")
    knots_df = load_cleaned_knots()

    if knots_df is None or len(knots_df) == 0:
        raise ValueError("No cleaned knot data available for plotting")

    # Create stratified scatter plot (alternating vs non-alternating)
    logger.info("Creating stratified scatter plot")
    fig = create_stratified_scatter_plot(knots_df)

    if fig is None:
        raise RuntimeError("Failed to create stratified scatter plot")

    # Set figure size in inches (width/dpi, height/dpi)
    fig.set_size_inches(width / dpi, height / dpi)
    fig.set_dpi(dpi)

    # Save the plot
    logger.info(f"Saving plot to {output_path} with resolution {width}x{height} pixels")
    fig.savefig(
        output_path,
        dpi=dpi,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none'
    )

    # Close figure to free memory
    plt.close(fig)

    # Log operation
    log_entry = log_operation(
        operation=operation_name,
        input_file="data/processed/knots_cleaned.csv",
        output_file=str(output_path),
        parameters={
            'width': width,
            'height': height,
            'dpi': dpi,
            'total_knots': len(knots_df)
        },
        status='success'
    )

    return {
        'success': True,
        'output_path': str(output_path),
        'width': width,
        'height': height,
        'dpi': dpi,
        'timestamp': datetime.now().isoformat(),
        'total_knots': len(knots_df)
    }


def main():
    """Main entry point for the plot saving script."""
    # Define output path
    data_plots_dir = project_root / 'data' / 'plots'
    output_path = data_plots_dir / 'crossing_vs_braid.png'

    print(f"Saving crossing vs braid index plot to: {output_path}")
    print(f"Target resolution: 1200x900 pixels")

    try:
        result = save_crossing_braid_plot(output_path, width=1200, height=900)

        if result['success']:
            print(f"✓ Successfully saved plot to {result['output_path']}")
            print(f"  Resolution: {result['width']}x{result['height']} pixels")
            print(f"  Total knots plotted: {result['total_knots']}")
            return 0
        else:
            print(f"✗ Failed to save plot")
            return 1

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
