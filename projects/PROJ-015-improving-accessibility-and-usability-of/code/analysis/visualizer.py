import matplotlib.pyplot as plt
import pandas as pd
from utils.logger import get_logger
import os
from pathlib import Path
import numpy as np

class Visualizer:
    def __init__(self):
        self.logger = get_logger("visualizer")

    def plot_boxplot_with_error_bars(self, df: pd.DataFrame, x_col: str, y_col: str, out_path: str, title: str = None):
        """
        Generates a box plot with error bars representing the interquartile range and median.
        
        Args:
            df: The pandas DataFrame containing the data.
            x_col: The column name for the x-axis categories (e.g., 'interface_type').
            y_col: The column name for the y-axis values (e.g., 'completion_time').
            out_path: The file path to save the generated figure.
            title: Optional title for the plot.
        """
        self.logger.info(f"Generating box plot for {y_col} by {x_col}")
        
        # Ensure output directory exists
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        plt.figure(figsize=(10, 6))
        
        # Create boxplot
        # Using pandas native boxplot which handles grouping well
        ax = df.boxplot(column=y_col, by=x_col, ax=plt.gca())
        
        # Customize plot
        plt.title(title if title else f'{y_col} by {x_col}')
        plt.suptitle('')  # Remove default pandas suptitle to avoid overlap
        plt.xlabel(x_col.replace('_', ' ').title())
        plt.ylabel(y_col.replace('_', ' ').title())
        
        # Add grid for readability
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Box plot saved to {out_path}")

    def generate_all_plots(self, metrics_df: pd.DataFrame, output_dir: str):
        """
        Generates all required publication-quality visualizations based on the metrics summary.
        
        Args:
            metrics_df: DataFrame containing the aggregated metrics (from T026).
            output_dir: Directory to save the generated figures.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        metrics_to_plot = ['completion_time', 'error_count', 'sus_score']
        
        for metric in metrics_to_plot:
            if metric in metrics_df.columns:
                out_path = os.path.join(output_dir, f'boxplot_{metric}.png')
                self.plot_boxplot_with_error_bars(
                    metrics_df, 
                    'interface_type', 
                    metric, 
                    out_path,
                    title=f'{metric.replace("_", " ").title()} Comparison'
                )
            else:
                self.logger.warning(f"Metric {metric} not found in dataframe, skipping plot.")

def main():
    """
    Entry point for testing the visualizer module.
    Loads data from data/processed/metrics_summary.csv and generates plots.
    """
    logger = get_logger("visualizer_main")
    logger.info("Starting visualizer module execution.")
    
    # Determine paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "metrics_summary.csv"
    output_dir = project_root / "figures"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T026 (generate_metrics_summary) has been run first.")
        return
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded data from {input_path}")
        logger.info(f"Data shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        viz = Visualizer()
        viz.generate_all_plots(df, str(output_dir))
        
        logger.info("Visualization generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during visualization generation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()