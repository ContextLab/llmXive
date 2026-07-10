"""
T036 Implementation: Save final visualization to disk.

This module loads the generated plot from the visualization pipeline
and saves it as a PNG file to the project's data/processed directory.
"""
import logging
import sys
from pathlib import Path

# Ensure project root is in path for imports if running directly
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import CONFIG
from code.viz.plot_results import run_visualization_pipeline

logger = logging.getLogger(__name__)

def save_visualization(output_path: str = None) -> Path:
    """
    Runs the visualization pipeline and saves the resulting figure to disk.

    Args:
        output_path: Optional override for the output path. Defaults to
                     CONFIG.OUTPUT_PLOT_PATH if not provided.

    Returns:
        Path: The absolute path to the saved PNG file.

    Raises:
        FileNotFoundError: If the plot file is not generated.
        RuntimeError: If the visualization pipeline fails.
    """
    if output_path is None:
        output_path = CONFIG.OUTPUT_PLOT_PATH

    output_file = Path(output_path)
    
    # Ensure the directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting visualization pipeline to save to {output_file}")

    try:
        # Run the existing visualization pipeline which generates the figure
        # and returns the matplotlib figure object (or None if it handles save internally).
        # Based on T035, run_visualization_pipeline generates the plot.
        fig = run_visualization_pipeline()

        if fig is None:
            # If the pipeline doesn't return the figure, we might need to access current
            # figure or the pipeline might have already saved it.
            # Let's assume the pipeline creates the figure but T036 is responsible for saving.
            import matplotlib.pyplot as plt
            fig = plt.gcf()
            if fig is None:
                raise RuntimeError("Visualization pipeline did not produce a figure.")

        # Save the figure
        fig.savefig(
            output_file,
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )

        if not output_file.exists():
            raise FileNotFoundError(f"Failed to create file at {output_file}")

        logger.info(f"Visualization successfully saved to {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Error saving visualization: {e}", exc_info=True)
        raise

def main():
    """Entry point for T036 execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        save_visualization()
        print(f"SUCCESS: Visualization saved to {CONFIG.OUTPUT_PLOT_PATH}")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()