"""
Visualization module for the Doomscrolling Anxiety study.
Generates scatter plots with regression lines and 95% confidence intervals.
"""
import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project modules
from config import load_config, ensure_directories
from model import fit_regression_model

logger = logging.getLogger(__name__)

def load_processed_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned processed dataset.
    
    Args:
        data_path: Optional path override. Defaults to config.
        
    Returns:
        DataFrame with cleaned data.
    """
    config = load_config()
    if data_path is None:
        data_path = str(config.get("paths", {}).get("processed_data", "data/processed/analysis_data.csv"))
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                              "Run the ingestion pipeline first.")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def plot_scatter_with_regression(
    df: pd.DataFrame,
    x_col: str = "news_exposure_freq",
    y_col: str = "anxiety_score",
    output_path: Optional[str] = None,
    title: str = "Doomscrolling vs Anticipatory Anxiety",
    figsize: tuple = (10, 8)
) -> Path:
    """
    Generate a scatter plot with regression line and 95% confidence interval.
    
    This implements FR-005: Visualization of the relationship between
    news exposure frequency and anxiety scores.
    
    Args:
        df: DataFrame containing the data.
        x_col: Column name for the predictor variable.
        y_col: Column name for the outcome variable.
        output_path: Optional path to save the plot. Defaults to config.
        title: Plot title.
        figsize: Figure size (width, height).
        
    Returns:
        Path object pointing to the saved plot file.
    """
    config = load_config()
    if output_path is None:
        output_dir = Path(config.get("paths", {}).get("outputs", "outputs"))
        ensure_directories(config)
        output_path = str(output_dir / "plot.png")
    else:
        ensure_directories(config)
        
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate columns exist
    required_cols = [x_col, y_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataframe: {missing}")

    # Drop rows with missing values in the relevant columns for plotting
    plot_data = df[[x_col, y_col]].dropna()
    
    if len(plot_data) < 10:
        logger.warning(f"Insufficient data points ({len(plot_data)}) for meaningful regression plot.")

    # Set style
    sns.set(style="whitegrid")
    plt.figure(figsize=figsize)

    # Create scatter plot with regression line and 95% CI
    # Seaborn's regplot automatically calculates and draws the 95% CI band
    sns.regplot(
        data=plot_data,
        x=x_col,
        y=y_col,
        scatter_kws={'alpha': 0.6, 's': 60, 'edgecolor': 'w'},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95,  # 95% confidence interval
        truncate=False
    )

    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(x_col.replace('_', ' ').title(), fontsize=12)
    plt.ylabel(y_col.replace('_', ' ').title(), fontsize=12)
    
    # Add a text box with the regression equation and R-squared if possible
    # We'll calculate a simple OLS to get the stats for the annotation
    try:
        import statsmodels.api as sm
        X = sm.add_constant(plot_data[x_col])
        y = plot_data[y_col]
        model = sm.OLS(y, X).fit()
        r_squared = model.rsquared
        slope = model.params[x_col]
        intercept = model.params['const']
        
        eq_text = f"y = {slope:.3f}x + {intercept:.3f}\n$R^2$ = {r_squared:.3f}"
        plt.text(
            0.05, 0.95, eq_text,
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        logger.info(f"Regression equation calculated: slope={slope:.3f}, R²={r_squared:.3f}")
    except Exception as e:
        logger.warning(f"Could not calculate regression stats for annotation: {e}")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved scatter plot with regression line to {output_path}")
    return output_path

def main():
    """
    Main entry point for generating the visualization.
    Loads processed data and generates the scatter plot.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()
    
    logger.info("Starting visualization generation (T028)...")
    
    try:
        # Load data
        df = load_processed_data()
        
        # Generate the plot
        output_path = plot_scatter_with_regression(
            df=df,
            x_col="news_exposure_freq",
            y_col="anxiety_score",
            title="Relationship: News Exposure Frequency vs Anticipatory Anxiety Score"
        )
        
        logger.info(f"Visualization complete. Output saved to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        raise

if __name__ == "__main__":
    main()