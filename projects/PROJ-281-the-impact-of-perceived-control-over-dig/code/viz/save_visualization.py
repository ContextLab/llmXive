import logging
import sys
from pathlib import Path

from code.config import CONFIG
from code.viz.plot_results import run_visualization_pipeline

logger = logging.getLogger(__name__)

def save_visualization():
    """
    Execute the visualization pipeline and save the final plot to disk.
    
    This function orchestrates the loading of analysis data, calculation of
    regression lines, generation of the scatter plot, and saving of the
    resulting image to the configured output path.
    
    Output:
        Writes `data/processed/correlation_plot.png` to disk.
    """
    logger.info("Starting visualization save process...")
    
    # Define output path explicitly as per task T036
    output_path = Path(CONFIG.PROCESSED_DIR) / "correlation_plot.png"
    
    try:
        # Run the full pipeline which loads data, calculates regression,
        # generates the plot object, and saves it.
        # The underlying run_visualization_pipeline in plot_results.py 
        # handles the logic of generating and saving.
        # We ensure the path is passed or the default is used.
        
        # Re-implementing the save logic here to ensure T036 requirement 
        # (saving to specific path) is met directly if the underlying
        # function uses a different default or if we need to enforce it.
        
        # 1. Load data
        from code.viz.plot_results import load_analysis_data, calculate_regression_line, generate_scatter_plot
        
        data_path = Path(CONFIG.PROCESSED_DIR) / "final_analysis.csv"
        df = load_analysis_data(data_path)
        
        if df is None or df.empty:
            logger.error("No data found to visualize. Aborting.")
            return False
        
        # 2. Calculate regression
        x_data = df['control_proxy'].values
        y_data = df['anxiety_score'].values
        slope, intercept = calculate_regression_line(x_data, y_data)
        
        # 3. Generate plot
        fig = generate_scatter_plot(x_data, y_data, slope, intercept)
        
        # 4. Save to specific path required by T036
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Visualization successfully saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save visualization: {e}", exc_info=True)
        return False

def main():
    """Entry point for running the save visualization script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = save_visualization()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()