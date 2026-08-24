import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any
import json
from config import load_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the cleaned and processed dataset from data/processed/analysis_data.csv.
    
    Args:
        config: Configuration dictionary containing paths.
        
    Returns:
        pd.DataFrame: The processed dataset.
        
    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    data_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/analysis_data.csv'))
    
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found at: {data_path}")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def plot_scatter_with_regression(
    df: pd.DataFrame,
    x_col: str = 'news_exposure_freq',
    y_col: str = 'anxiety_score',
    output_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a scatter plot with regression line and 95% confidence interval.
    
    This function creates a visualization of the relationship between news exposure
    frequency and anxiety score, including a fitted regression line and confidence bands.
    
    Args:
        df: DataFrame containing the data.
        x_col: Name of the predictor variable column.
        y_col: Name of the outcome variable column.
        output_path: Path where the plot will be saved.
        config: Optional configuration dictionary for paths.
        
    Raises:
        ValueError: If required columns are missing from the DataFrame.
        FileNotFoundError: If output directory cannot be created.
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Required columns {x_col} and {y_col} must exist in DataFrame")
    
    # Filter out NaN values for plotting
    plot_df = df[[x_col, y_col]].dropna()
    
    if len(plot_df) < 2:
        logger.warning("Insufficient data points for regression plot")
        return
    
    # Set style
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # Create scatter plot with regression line and 95% CI
    sns.regplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        scatter_kws={'alpha': 0.6, 's': 60},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    # Enhance labels
    plt.title(f'Relationship between {x_col.replace("_", " ").title()} and {y_col.replace("_", " ").title()}', fontsize=14)
    plt.xlabel(x_col.replace("_", " ").title(), fontsize=12)
    plt.ylabel(y_col.replace("_", " ").title(), fontsize=12)
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save or show
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        logger.info("Plot generated but not saved (no output_path provided)")
    
    plt.close()

def main():
    """
    Main entry point for generating the visualization.
    
    This function:
    1. Loads configuration
    2. Loads processed data
    3. Generates the scatter plot with regression line
    4. Saves the plot to outputs/plot.png
    """
    # Load configuration
    config = load_config()
    
    # Ensure output directories exist
    ensure_directories(config)
    
    # Define output path
    output_path = Path(config.get('paths', {}).get('output_dir', 'outputs')) / 'plot.png'
    
    try:
        # Load data
        df = load_processed_data(config)
        
        # Generate plot
        plot_scatter_with_regression(
            df=df,
            x_col='news_exposure_freq',
            y_col='anxiety_score',
            output_path=output_path,
            config=config
        )
        
        logger.info("Visualization task completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == '__main__':
    main()
