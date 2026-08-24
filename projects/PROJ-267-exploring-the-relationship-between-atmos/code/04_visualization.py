"""
Visualization pipeline for Atmospheric River Gravity Correlation study.
Generates time-series overlays, scatter plots, and spatial anomaly maps.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_merged_data():
    """Load the merged monthly dataset."""
    merged_path = DATA_DIR / "merged_monthly.csv"
    if not merged_path.exists():
        raise FileNotFoundError(
            f"Merged data file not found at {merged_path}. "
            "Run preprocessing pipeline first."
        )
    df = pd.read_csv(merged_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def plot_timeseries(df):
    """Generate time-series overlay plot of AR intensity and gravity anomaly."""
    logger.info("Generating time-series overlay plot...")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['ar_intensity'], label='AR Intensity (IWVT)', alpha=0.7)
    plt.plot(df['date'], df['gravity_anomaly'], label='Gravity Anomaly', alpha=0.7)
    
    plt.title('Atmospheric River Intensity vs Gravity Anomaly Over Time')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Caption as required by spec
    caption = "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."
    plt.figtext(0.5, 0.01, caption, ha='center', fontsize=9, style='italic')
    
    output_path = OUTPUT_DIR / "timeseries_overlay.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved time-series plot to {output_path}")
    return output_path

def plot_scatter(df):
    """Generate scatter plot with regression line."""
    logger.info("Generating scatter regression plot...")
    
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x='ar_intensity', y='gravity_anomaly', alpha=0.6)
    sns.regplot(data=df, x='ar_intensity', y='gravity_anomaly', scatter=False, color='red')
    
    plt.title('AR Intensity vs Gravity Anomaly')
    plt.xlabel('AR Intensity (IWVT)')
    plt.ylabel('Gravity Anomaly')
    plt.tight_layout()
    
    # Caption as required by spec
    caption = "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."
    plt.figtext(0.5, 0.01, caption, ha='center', fontsize=9, style='italic')
    
    output_path = OUTPUT_DIR / "scatter_regression.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved scatter plot to {output_path}")
    return output_path

def plot_spatial(df):
    """Generate spatial anomaly map (placeholder for full spatial data)."""
    logger.info("Generating spatial anomaly map...")
    
    # Since we have aggregated monthly data without spatial coordinates,
    # we create a representative spatial visualization based on region stats
    # In a full implementation, this would use the footprint coordinates
    
    plt.figure(figsize=(10, 8))
    # Placeholder: Show average anomaly by region if available, otherwise a simple bar chart
    if 'region' in df.columns:
        region_means = df.groupby('region')['gravity_anomaly'].mean()
        region_means.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('Average Gravity Anomaly by Region')
        plt.xlabel('Region')
        plt.ylabel('Average Anomaly')
    else:
        # Fallback: simple distribution plot
        df['gravity_anomaly'].hist(bins=20, color='skyblue', edgecolor='black')
        plt.title('Distribution of Gravity Anomalies')
        plt.xlabel('Anomaly Value')
        plt.ylabel('Frequency')
    
    plt.tight_layout()
    
    # Caption as required by spec
    caption = "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."
    plt.figtext(0.5, 0.01, caption, ha='center', fontsize=9, style='italic')
    
    output_path = OUTPUT_DIR / "spatial_anomaly_map.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved spatial map to {output_path}")
    return output_path

def main():
    """Run all visualization tasks."""
    logger.info("=== Visualization Pipeline Start ===")
    
    try:
        df = load_merged_data()
        logger.info(f"Loaded {len(df)} rows of merged data.")
        
        plot_timeseries(df)
        plot_scatter(df)
        plot_spatial(df)
        
        logger.info("=== Visualization Pipeline Complete ===")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()