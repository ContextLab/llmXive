import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from config import load_config
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """Load the processed data for visualization."""
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Data file not found: {input_path}")
    return pd.read_csv(input_path)

def plot_scatter_with_regression(df: pd.DataFrame, output_path: Path) -> None:
    """Generate scatter plot with regression line and 95% CI."""
    logger.info("Generating scatter plot with regression line...")
    
    # Ensure numeric
    df['news_exposure_freq'] = pd.to_numeric(df['news_exposure_freq'], errors='coerce')
    df['anxiety_score'] = pd.to_numeric(df['anxiety_score'], errors='coerce')
    
    clean_df = df.dropna(subset=['news_exposure_freq', 'anxiety_score'])
    
    if len(clean_df) < 2:
        logger.error("Not enough data points for plotting.")
        return
    
    plt.figure(figsize=(10, 6))
    
    # Use seaborn regplot for regression line and CI
    sns.set_style("whitegrid")
    sns.regplot(
        data=clean_df,
        x='news_exposure_freq',
        y='anxiety_score',
        scatter_kws={'alpha': 0.6, 's': 50},
        line_kws={'color': 'red', 'lw': 2}
    )
    
    plt.title('Anxiety Score vs. News Exposure Frequency')
    plt.xlabel('News Exposure Frequency')
    plt.ylabel('Anxiety Score')
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def main() -> None:
    """Main entry point for visualization."""
    config = load_config()
    input_path = Path(config['paths']['processed_data'])
    output_path = Path(config['paths']['plot'])
    
    try:
        df = load_processed_data(input_path)
        plot_scatter_with_regression(df, output_path)
        logger.info("Visualization completed.")
    except Exception as e:
        logger.critical(f"Visualization failed: {e}")
        raise

if __name__ == "__main__":
    main()
