import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any
from config import load_config, ensure_directories

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the cleaned and processed dataset from disk.
    
    Args:
        config: Configuration dictionary containing paths.
        
    Returns:
        DataFrame containing the processed analysis data.
        
    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    data_path = Path(config['paths']['processed_data'])
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def plot_scatter_with_regression(
    df: pd.DataFrame,
    x_col: str = 'news_exposure_freq',
    y_col: str = 'anxiety_score',
    output_path: Optional[Path] = None,
    title: str = 'News Exposure vs Anxiety Score',
    figsize: tuple = (10, 8)
) -> None:
    """
    Generate a scatter plot with a regression line and 95% confidence interval.
    
    This function visualizes the relationship between the primary predictor
    (news_exposure_freq) and the outcome (anxiety_score), including the fitted
    regression line and its confidence interval.
    
    Args:
        df: DataFrame containing the data to plot.
        x_col: Name of the predictor column.
        y_col: Name of the outcome column.
        output_path: Path to save the plot. If None, the plot is not saved.
        title: Title for the plot.
        figsize: Tuple specifying (width, height) of the figure.
        
    Raises:
        KeyError: If the specified columns are not found in the DataFrame.
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError(f"Columns {x_col} or {y_col} not found in DataFrame")
    
    # Remove NaN values for plotting
    plot_df = df[[x_col, y_col]].dropna()
    
    if len(plot_df) == 0:
        logger.warning("No valid data points to plot after removing NaNs.")
        return

    # Set style
    sns.set(style="whitegrid")
    
    plt.figure(figsize=figsize)
    
    # Create the scatter plot with regression line and 95% CI
    # Using regplot which automatically calculates and plots the regression line
    # and the 95% confidence interval around it.
    sns.regplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        scatter_kws={'alpha': 0.6, 's': 80, 'edgecolor': 'w'},
        line_kws={'color': 'red', 'lw': 2},
        ci=95
    )
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
    plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
    
    # Add a grid for better readability
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Tight layout to prevent label clipping
    plt.tight_layout()
    
    if output_path:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        logger.warning("No output path provided; plot will not be saved.")
    
    plt.close()

def main():
    """
    Main entry point for the visualization script.
    Loads processed data, generates the scatter plot with regression line,
    and saves it to the specified output path.
    """
    logger.info("Starting visualization script...")
    
    # Load configuration
    config = load_config()
    
    # Ensure output directories exist
    ensure_directories(config)
    
    # Define output path for the plot
    output_dir = Path(config['paths']['outputs'])
    output_path = output_dir / 'plot.png'
    
    try:
        # Load processed data
        df = load_processed_data(config)
        
        # Generate and save the plot
        plot_scatter_with_regression(
            df=df,
            x_col='news_exposure_freq',
            y_col='anxiety_score',
            output_path=output_path,
            title='Association between News Exposure Frequency and Anxiety Score',
            figsize=(10, 8)
        )
        
        logger.info("Visualization script completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during visualization: {e}")
        raise

if __name__ == "__main__":
    main()
