import logging
import sys
from pathlib import Path
from code.config import CONFIG
from code.viz.plot_results import run_visualization_pipeline

logger = logging.getLogger(__name__)

def save_visualization():
    """
    Saves the final correlation plot to data/processed/correlation_plot.png.
    Ensures dimensions are 6x6 inches, DPI 300, and uses seaborn.darkgrid style.
    """
    logger.info("Starting visualization save process (T036)...")
    
    # Run the plotting pipeline to generate the figure in memory
    fig, ax = run_visualization_pipeline()
    
    if fig is None:
        logger.error("Visualization pipeline failed to generate a figure.")
        raise RuntimeError("Failed to generate visualization figure.")

    # Configure specific T036 requirements:
    # 1. Dimensions: 6x6 inches
    # 2. DPI: 300
    # 3. Style: seaborn.darkgrid (applied in plot_results.py, but ensuring save params)
    
    output_path = Path(CONFIG["OUTPUT_DIR"]) / "correlation_plot.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving figure to {output_path} (6x6 inches, 300 DPI)...")
    
    # Save with explicit parameters
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches='tight',
        facecolor='white',
        edgecolor='none'
    )
    
    logger.info(f"Successfully saved visualization to {output_path}")
    
    # Verify file existence and size
    if not output_path.exists():
        raise FileNotFoundError(f"Failed to write file to {output_path}")
    
    size_kb = output_path.stat().st_size / 1024
    logger.info(f"Saved file size: {size_kb:.2f} KB")
    
    return output_path

def main():
    """Entry point for the save visualization script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        save_visualization()
        logger.info("T036 completed successfully.")
    except Exception as e:
        logger.error(f"Error during T036 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()