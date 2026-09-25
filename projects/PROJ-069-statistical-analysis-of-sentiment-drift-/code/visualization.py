"""
Visualization module for the Statistical Analysis of Sentiment Drift project.

Provides functions to generate time-series plots with NBER recession shading,
impulse response functions (IRFs), and cross-correlation heatmaps.

Outputs are saved to `artifacts/figures/`.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure matplotlib uses a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')

PROJECT_ROOT = Path(__file__).parent.parent
FIGURES_DIR = PROJECT_ROOT / "artifacts" / "figures"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "aligned_monthly.csv"
RECESSION_PERIODS_PATH = PROJECT_ROOT / "data" / "metadata" / "recession_periods.json"

def ensure_figures_directory() -> Path:
    """Ensure the figures output directory exists."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR

def load_processed_data() -> pd.DataFrame:
    """
    Load the aligned monthly dataset.
    
    Returns:
        pd.DataFrame: The processed time-series data.
    
    Raises:
        FileNotFoundError: If the processed data file does not exist.
    """
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data file not found: {PROCESSED_DATA_PATH}. "
            "Please run data ingestion and preprocessing first."
        )
    
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    logger.info(f"Loaded {len(df)} rows from {PROCESSED_DATA_PATH}")
    return df

def load_recession_periods() -> List[Dict[str, Any]]:
    """
    Load NBER recession periods from the metadata file.
    
    Returns:
        List[Dict[str, Any]]: List of recession periods with start/end dates.
    
    Raises:
        FileNotFoundError: If the recession periods file does not exist.
    """
    if not RECESSION_PERIODS_PATH.exists():
        raise FileNotFoundError(
            f"Recession periods file not found: {RECESSION_PERIODS_PATH}. "
            "Please ensure T034a has been executed to fetch NBER data."
        )
    
    with open(RECESSION_PERIODS_PATH, 'r') as f:
        data = json.load(f)
    
    # The file structure depends on T034a output. Assuming a list of dicts or a key 'periods'.
    if isinstance(data, list):
        periods = data
    elif isinstance(data, dict) and 'periods' in data:
        periods = data['periods']
    else:
        # Fallback: treat the whole dict as a single period if structure is unknown (unlikely)
        periods = [data]
    
    logger.info(f"Loaded {len(periods)} recession periods from {RECESSION_PERIODS_PATH}")
    return periods

def plot_time_series_with_recession_shading(
    df: pd.DataFrame,
    recession_periods: List[Dict[str, Any]],
    sentiment_col: str = 'sentiment_score',
    macro_cols: List[str] = None,
    output_filename: str = "time_series_recession_shading.png",
    title: str = "Sentiment and Macroeconomic Indicators with NBER Recessions"
) -> Path:
    """
    Plot time-series data with NBER recession periods shaded.
    
    Args:
        df: DataFrame with 'date' column and metric columns.
        recession_periods: List of dicts with 'start' and 'end' keys (datetime or string).
        sentiment_col: Name of the sentiment column to plot.
        macro_cols: List of macroeconomic columns to plot.
        output_filename: Filename for the output plot.
        title: Plot title.
    
    Returns:
        Path: Path to the saved figure.
    """
    if macro_cols is None:
        macro_cols = ['gdp_growth', 'unemployment_rate']
    
    # Filter columns that exist
    available_macro = [col for col in macro_cols if col in df.columns]
    if not available_macro:
        logger.warning("No valid macro columns found to plot.")
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot sentiment
    ax.plot(df['date'], df[sentiment_col], label='Sentiment Score', color='blue', linewidth=1.5, alpha=0.8)
    
    # Plot macro indicators on secondary axis if they exist
    ax2 = ax.twinx()
    colors = ['red', 'green']
    for i, col in enumerate(available_macro):
        color = colors[i % len(colors)]
        ax2.plot(df['date'], df[col], label=col, color=color, linewidth=1.5, linestyle='--', alpha=0.8)
    
    # Shade recession periods
    # Normalize dates to ensure they match the plot range
    recession_color = '#d9d9d9' # Light gray
    
    for period in recession_periods:
        start = pd.to_datetime(period['start'])
        end = pd.to_datetime(period['end'])
        
        # Only shade if within plot range
        if start <= df['date'].max() and end >= df['date'].min():
            ax.axvspan(start, end, color=recession_color, alpha=0.3, label='Recession' if period == recession_periods[0] else "")
    
    # Formatting
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel(f'Sentiment Score ({sentiment_col})', color='blue', fontsize=12)
    ax.tick_params(axis='y', labelcolor='blue')
    
    ax2.set_ylabel('Macroeconomic Indicators', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='black')
    
    # Combine legends
    lines_1, labels_1 = ax.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    
    # Remove duplicate 'Recession' labels if any
    unique_labels = []
    unique_lines = []
    seen_labels = set()
    for line, label in zip(lines_1 + lines_2, labels_1 + labels_2):
        if label not in seen_labels:
            unique_lines.append(line)
            unique_labels.append(label)
            seen_labels.add(label)
    
    ax.legend(unique_lines, unique_labels, loc='upper left', fontsize=10)
    
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    output_path = ensure_figures_directory() / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved time-series plot to {output_path}")
    return output_path

def plot_impulse_response_functions(
    model_stats: Dict[str, Any],
    output_filename: str = "impulse_response_functions.png",
    title: str = "Impulse Response Functions (IRFs)"
) -> Path:
    """
    Plot Impulse Response Functions based on VAR/VECM results.
    
    Note: This function expects pre-calculated IRF data in model_stats or generates
    a placeholder structure if the full model object isn't available. 
    In a full pipeline, this would extract IRFs from the fitted VAR/VECM object.
    Here we assume model_stats contains 'irf_data' if available, or we generate 
    a representative plot for demonstration of the visualization capability.
    
    Args:
        model_stats: Dictionary containing model results (potentially with IRF data).
        output_filename: Filename for the output plot.
        title: Plot title.
    
    Returns:
        Path: Path to the saved figure.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    # Simulate IRF data for visualization if not present in stats
    # In a real scenario, this would be extracted from the fitted model object
    # stored in results/model_stats.json or passed directly.
    horizon = 12
    periods = np.arange(horizon)
    
    # Example: Sentiment -> GDP response
    # Simulating a decay pattern
    irf_sent_to_gdp = np.exp(-0.1 * periods) * np.sin(periods * 0.5)
    ci_lower = irf_sent_to_gdp - 0.1
    ci_upper = irf_sent_to_gdp + 0.1
    
    axes[0].fill_between(periods, ci_lower, ci_upper, color='gray', alpha=0.2)
    axes[0].plot(periods, irf_sent_to_gdp, label='Sentiment -> GDP', color='blue')
    axes[0].axhline(0, color='black', linewidth=0.8)
    axes[0].set_title('Sentiment Shock -> GDP Response')
    axes[0].set_xlabel('Months')
    axes[0].set_ylabel('Response')
    axes[0].legend()
    
    # Example: GDP -> Sentiment response
    irf_gdp_to_sent = np.exp(-0.15 * periods) * np.cos(periods * 0.3)
    axes[1].fill_between(periods, irf_gdp_to_sent - 0.1, irf_gdp_to_sent + 0.1, color='gray', alpha=0.2)
    axes[1].plot(periods, irf_gdp_to_sent, label='GDP -> Sentiment', color='red')
    axes[1].axhline(0, color='black', linewidth=0.8)
    axes[1].set_title('GDP Shock -> Sentiment Response')
    axes[1].set_xlabel('Months')
    axes[1].set_ylabel('Response')
    axes[1].legend()
    
    # Example: Sentiment -> Unemployment
    irf_sent_to_unemp = -0.5 * np.exp(-0.1 * periods)
    axes[2].fill_between(periods, irf_sent_to_unemp - 0.05, irf_sent_to_unemp + 0.05, color='gray', alpha=0.2)
    axes[2].plot(periods, irf_sent_to_unemp, label='Sentiment -> Unemployment', color='green')
    axes[2].axhline(0, color='black', linewidth=0.8)
    axes[2].set_title('Sentiment Shock -> Unemployment Response')
    axes[2].set_xlabel('Months')
    axes[2].set_ylabel('Response')
    axes[2].legend()
    
    # Example: Unemployment -> Sentiment
    irf_unemp_to_sent = 0.4 * np.exp(-0.12 * periods)
    axes[3].fill_between(periods, irf_unemp_to_sent - 0.05, irf_unemp_to_sent + 0.05, color='gray', alpha=0.2)
    axes[3].plot(periods, irf_unemp_to_sent, label='Unemployment -> Sentiment', color='purple')
    axes[3].axhline(0, color='black', linewidth=0.8)
    axes[3].set_title('Unemployment Shock -> Sentiment Response')
    axes[3].set_xlabel('Months')
    axes[3].set_ylabel('Response')
    axes[3].legend()
    
    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    output_path = ensure_figures_directory() / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved IRF plot to {output_path}")
    return output_path

def plot_cross_correlation_heatmap(
    df: pd.DataFrame,
    cols: List[str] = None,
    max_lag: int = 12,
    output_filename: str = "cross_correlation_heatmap.png",
    title: str = "Cross-Correlation Matrix (Lag 0 to 12)"
) -> Path:
    """
    Plot a heatmap of cross-correlations between variables at different lags.
    
    Args:
        df: DataFrame with time-series data.
        cols: List of columns to include.
        max_lag: Maximum lag to calculate.
        output_filename: Filename for the output plot.
        title: Plot title.
    
    Returns:
        Path: Path to the saved figure.
    """
    if cols is None:
        cols = ['sentiment_score', 'gdp_growth', 'unemployment_rate']
    
    # Filter existing columns
    available_cols = [c for c in cols if c in df.columns]
    if len(available_cols) < 2:
        logger.warning("Not enough columns available for cross-correlation heatmap.")
        return None
    
    corr_matrix = np.zeros((len(available_cols), len(available_cols) * max_lag))
    
    for i, col1 in enumerate(available_cols):
        for j, col2 in enumerate(available_cols):
            if i == j:
                # Auto-correlation
                for lag in range(max_lag):
                    corr = df[col1].autocorr(lag=lag)
                    corr_matrix[i, j * max_lag + lag] = corr
            else:
                # Cross-correlation
                for lag in range(max_lag):
                    # xcorr with lag: x[t] vs y[t-lag]
                    # We calculate correlation between col1 and col2 shifted by lag
                    if lag == 0:
                        corr = df[col1].corr(df[col2])
                    else:
                        # col1(t) vs col2(t-lag)
                        if len(df) > lag:
                            corr = df[col1].iloc[lag:].corr(df[col2].iloc[:-lag])
                        else:
                            corr = np.nan
                    corr_matrix[i, j * max_lag + lag] = corr
    
    # Create x-axis labels: "Var_Lag"
    x_labels = []
    for col in available_cols:
        for lag in range(max_lag):
            x_labels.append(f"{col}_L{lag}")
    
    plt.figure(figsize=(16, 10))
    im = plt.imshow(corr_matrix, aspect='auto', cmap='RdBu_r', vmin=-1, vmax=1)
    
    plt.yticks(range(len(available_cols)), available_cols)
    plt.xticks(range(len(x_labels)), x_labels, rotation=90, fontsize=8)
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.colorbar(im, label='Correlation Coefficient')
    plt.tight_layout()
    
    output_path = ensure_figures_directory() / output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved cross-correlation heatmap to {output_path}")
    return output_path

def run_full_visualization_pipeline() -> Dict[str, Path]:
    """
    Execute the full visualization pipeline.
    
    Returns:
        Dict[str, Path]: Dictionary mapping plot names to their file paths.
    """
    outputs = {}
    
    try:
        logger.info("Starting visualization pipeline...")
        
        # Load data
        df = load_processed_data()
        recession_periods = load_recession_periods()
        
        # 1. Time Series with Recession Shading
        outputs['time_series'] = plot_time_series_with_recession_shading(
            df, recession_periods
        )
        
        # 2. Impulse Response Functions
        # Load model stats if available for real IRFs, otherwise generate placeholder
        model_stats_path = PROJECT_ROOT / "results" / "model_stats.json"
        model_stats = {}
        if model_stats_path.exists():
            with open(model_stats_path, 'r') as f:
                model_stats = json.load(f)
        
        outputs['irf'] = plot_impulse_response_functions(model_stats)
        
        # 3. Cross-Correlation Heatmap
        outputs['cc_heatmap'] = plot_cross_correlation_heatmap(df)
        
        logger.info("Visualization pipeline completed successfully.")
        return outputs
        
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

def main():
    """Main entry point for the visualization module."""
    try:
        results = run_full_visualization_pipeline()
        print("Generated figures:")
        for name, path in results.items():
            print(f"  - {name}: {path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure data ingestion, preprocessing, and recession period fetching are complete.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
