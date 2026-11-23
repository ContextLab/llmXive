import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def create_regression_plot(
    data_path: str,
    output_path: str,
    x_col: str = "island_width",
    y_col: str = "tau_e",
    title: str = "Topology vs Confinement",
    x_label: str = "Island Width (m)",
    y_label: str = "Tau_E (s)",
    bootstrap_iterations: int = 1000,
    random_seed: int = 42,
) -> None:
    """
    Generate a diagnostic scatter plot of topology vs confinement with
    linear regression line and confidence interval band.

    This function reads the unified dataset, performs bootstrap resampling
    to estimate confidence intervals for the regression line, and saves
    the resulting plot.

    Args:
        data_path: Path to the input CSV file containing discharge data.
        output_path: Path where the plot will be saved.
        x_col: Column name for the x-axis (default: "island_width").
        y_col: Column name for the y-axis (default: "tau_e").
        title: Plot title.
        x_label: X-axis label.
        y_label: Y-axis label.
        bootstrap_iterations: Number of bootstrap iterations for CI estimation.
        random_seed: Random seed for reproducibility.
    """
    # Set random seed for reproducibility
    np.random.seed(random_seed)

    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Validate required columns
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Required columns {x_col} and/or {y_col} not found in data.")

    # Filter out NaN values
    valid_mask = df[x_col].notna() & df[y_col].notna()
    df_valid = df[valid_mask]

    if len(df_valid) < 2:
        raise ValueError("Insufficient valid data points for regression analysis.")

    x = df_valid[x_col].values
    y = df_valid[y_col].values

    # Perform linear regression on the full dataset
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    logger.info(f"Regression: slope={slope:.4f}, intercept={intercept:.4f}, r={r_value:.4f}, p={p_value:.4f}")

    # Generate x values for the regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    # Bootstrap resampling for confidence intervals
    logger.info(f"Performing bootstrap resampling ({bootstrap_iterations} iterations)...")
    n_samples = len(x)
    y_preds = []

    for _ in range(bootstrap_iterations):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]

        # Fit regression to bootstrap sample
        try:
            boot_slope, boot_intercept, _, _, _ = stats.linregress(x_boot, y_boot)
            # Predict at original x_line points
            y_boot_pred = boot_slope * x_line + boot_intercept
            y_preds.append(y_boot_pred)
        except ValueError:
            # Skip if regression fails (e.g., all x values identical in bootstrap sample)
            continue

    y_preds = np.array(y_preds)

    # Calculate confidence intervals (2.5th and 97.5th percentiles)
    ci_lower = np.percentile(y_preds, 2.5, axis=0)
    ci_upper = np.percentile(y_preds, 97.5, axis=0)

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot of data points
    ax.scatter(x, y, alpha=0.6, edgecolors='k', linewidth=0.5, label='Data points')

    # Regression line
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear fit (r={r_value:.2f})')

    # Confidence interval band
    ax.fill_between(x_line, ci_lower, ci_upper, color='red', alpha=0.2, label='95% CI')

    # Labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    logger.info(f"Plot saved to {output_path}")

def main():
    """Main entry point for generating the topology vs confinement plot."""
    # Default paths based on project structure
    data_path = "data/processed/unified_analysis.csv"
    output_path = "outputs/topology_vs_confinement.png"

    # Allow override via command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Generate topology vs confinement scatter plot")
    parser.add_argument("--data", type=str, default=data_path, help="Path to input CSV data")
    parser.add_argument("--output", type=str, default=output_path, help="Path to output plot")
    parser.add_argument("--iterations", type=int, default=1000, help="Bootstrap iterations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    try:
        create_regression_plot(
            data_path=args.data,
            output_path=args.output,
            bootstrap_iterations=args.iterations,
            random_seed=args.seed,
        )
        print(f"Successfully generated plot: {args.output}")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        raise

if __name__ == "__main__":
    main()