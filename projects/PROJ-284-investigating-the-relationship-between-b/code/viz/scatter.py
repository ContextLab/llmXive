"""Scatter plot generation for correlation results."""
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger

logger = get_logger(__name__)


def generate_scatter_plot(
    input_csv: Optional[str] = None,
    x: Optional[str] = None,
    y: Optional[str] = None,
    output: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    title: Optional[str] = None
) -> None:
    """Generate scatter plot from correlation results."""
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats

    if input_csv is None or x is None or y is None or output is None:
        logger.warning("Missing required arguments for scatter plot")
        return

    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        return

    # Load data
    df = pd.read_csv(input_csv)

    if x not in df.columns or y not in df.columns:
        logger.error(f"Columns {x} or {y} not found in {input_csv}")
        return

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 8))

    x_data = df[x].values
    y_data = df[y].values

    # Remove NaN values
    valid_idx = ~(np.isnan(x_data) | np.isnan(y_data))
    x_clean = x_data[valid_idx]
    y_clean = y_data[valid_idx]

    ax.scatter(x_clean, y_clean, alpha=0.6, s=50)

    # Add regression line
    if len(x_clean) > 2:
        z = np.polyfit(x_clean, y_clean, 1)
        p = np.poly1d(z)
        x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, label="Linear fit")

        # Calculate correlation
        r, p_val = stats.pearsonr(x_clean, y_clean)
        ax.text(0.05, 0.95, f"r={r:.3f}\np={p_val:.3e}", 
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel(x_label or x)
    ax.set_ylabel(y_label or y)
    ax.set_title(title or f"{x} vs {y}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save figure
    os.makedirs(os.path.dirname(output), exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches='tight')
    logger.info(f"Saved scatter plot to {output}")
    plt.close()


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate scatter plots")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--x", required=True, help="X-axis column")
    parser.add_argument("--y", required=True, help="Y-axis column")
    parser.add_argument("--x-label", help="X-axis label")
    parser.add_argument("--y-label", help="Y-axis label")
    parser.add_argument("--output", required=True, help="Output PNG file")
    parser.add_argument("--title", help="Plot title")

    args = parser.parse_args()

    generate_scatter_plot(
        input_csv=args.input,
        x=args.x,
        y=args.y,
        output=args.output,
        x_label=args.x_label,
        y_label=args.y_label,
        title=args.title
    )


if __name__ == "__main__":
    main()