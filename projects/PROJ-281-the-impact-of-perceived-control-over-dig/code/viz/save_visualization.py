import logging
import sys
from pathlib import Path

from code.config import CONFIG
from code.viz.plot_results import run_visualization_pipeline

logger = logging.getLogger(__name__)


def save_visualization():
    """
    Executes the visualization pipeline and saves the final plot to disk.

    This function:
    1. Loads the merged analysis data from `data/processed/final_analysis.csv`.
    2. Calculates the regression line based on the data.
    3. Generates a scatter plot with the regression line overlaid.
    4. Saves the plot as `data/processed/correlation_plot.png`.

    Returns:
        Path: The path to the saved PNG file.

    Raises:
        FileNotFoundError: If the input data file does not exist.
        RuntimeError: If the plot generation fails.
    """
    logger.info("Starting visualization save process...")

    # Define output path explicitly as per task T036
    output_path = CONFIG.PROCESSED_DATA_DIR / "correlation_plot.png"

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Run the visualization pipeline which generates the figure
        fig = run_visualization_pipeline()

        if fig is None:
            raise RuntimeError("Visualization pipeline returned None; no figure generated.")

        # Save the figure to disk
        fig.savefig(
            output_path,
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )

        logger.info(f"Visualization successfully saved to: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to save visualization: {e}", exc_info=True)
        raise


def main():
    """Entry point for command-line execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        save_visualization()
        logger.info("Pipeline stage T036 completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline stage T036 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()