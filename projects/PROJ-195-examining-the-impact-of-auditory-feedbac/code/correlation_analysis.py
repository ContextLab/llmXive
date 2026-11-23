import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

def setup_logging() -> logging.Logger:
    """Configure logging for the correlation analysis module."""
    logger = logging.getLogger("correlation_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger

def load_roi_betas(
    logger: logging.Logger, input_path: Path = None
) -> pd.DataFrame:
    """
    Load auditory cortex beta values from T028 output.
    Expected columns: subject_id, beta_value (or similar numeric column).
    """
    if input_path is None:
        input_path = DATA_PROCESSED / "roi_betas.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T028 has been executed successfully."
        )

    df = pd.read_csv(input_path)
    logger.info(f"Loaded ROI betas from {input_path}: {len(df)} rows")
    return df

def load_learning_rate_slopes(
    logger: logging.Logger, input_path: Path = None
) -> pd.DataFrame:
    """
    Load learning rate slopes from T032 output.
    Expected columns: subject_id, slope (or similar numeric column).
    """
    if input_path is None:
        input_path = DATA_PROCESSED / "learning_rates.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T032 has been executed successfully."
        )

    df = pd.read_csv(input_path)
    logger.info(f"Loaded learning rates from {input_path}: {len(df)} rows")
    return df

def calculate_pearson_correlation(
    logger: logging.Logger,
    betas_df: pd.DataFrame,
    slopes_df: pd.DataFrame,
    key_col: str = "subject_id",
    beta_col: str = "beta_value",
    slope_col: str = "slope",
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between auditory cortex activation (beta)
    and learning rate slope.

    Returns a dictionary with:
      - r: correlation coefficient
      - p_value: p-value for the correlation
      - ci_lower: lower bound of 95% CI (Fisher Z-transform)
      - ci_upper: upper bound of 95% CI
      - n: number of paired observations
    """
    # Merge on subject_id
    merged = pd.merge(betas_df, slopes_df, on=key_col, how="inner")

    if len(merged) < 3:
        logger.warning(
            f"Insufficient data for correlation: only {len(merged)} subjects found."
        )
        raise ValueError(
            "Need at least 3 subjects to calculate Pearson correlation and CI."
        )

    x = merged[slope_col].dropna()
    y = merged[beta_col].dropna()

    # Ensure alignment after dropna
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]

    if len(x) < 3:
        raise ValueError(
            "After dropping NaNs, insufficient data points remain for correlation."
        )

    logger.info(f"Performing Pearson correlation on {len(x)} paired observations.")

    r, p_value = stats.pearsonr(x, y)

    # Fisher Z-transform for 95% CI
    z = 0.5 * np.log((1 + r) / (1 - r))
    se_z = 1.0 / np.sqrt(len(x) - 3)
    z_lower = z - 1.96 * se_z
    z_upper = z + 1.96 * se_z

    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

    result = {
        "r": float(r),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n": int(len(x)),
    }

    logger.info(
        f"Correlation result: r={r:.4f}, p={p_value:.4f}, "
        f"95% CI [{ci_lower:.4f}, {ci_upper:.4f}]"
    )

    return result

def generate_scatter_plot(
    logger: logging.Logger,
    betas_df: pd.DataFrame,
    slopes_df: pd.DataFrame,
    key_col: str = "subject_id",
    beta_col: str = "beta_value",
    slope_col: str = "slope",
    output_path: Path = None,
) -> None:
    """
    Generate a scatter plot of RT slope vs. Beta values with regression line.
    Saved to figures/brain_behavior_correlation.png (default).
    """
    import matplotlib.pyplot as plt

    if output_path is None:
        figures_dir = PROJECT_ROOT / "figures"
        figures_dir.mkdir(exist_ok=True)
        output_path = figures_dir / "brain_behavior_correlation.png"

    merged = pd.merge(betas_df, slopes_df, on=key_col, how="inner")
    x = merged[slope_col].dropna()
    y = merged[beta_col].dropna()
    common_idx = x.index.intersection(y.index)
    x = x.loc[common_idx]
    y = y.loc[common_idx]

    if len(x) < 2:
        logger.error("Not enough data to generate scatter plot.")
        return

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.7, edgecolors="k", s=60, label="Subjects")

    # Fit regression line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_line, p(x_line), "r--", label=f"Fit: y={z[0]:.3f}x+{z[1]:.3f}")

    plt.xlabel("Learning Rate Slope (ms/trial)")
    plt.ylabel("Auditory Cortex Beta Value")
    plt.title("Brain-Behavior Correlation: Learning Rate vs. Auditory Activation")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.info(f"Scatter plot saved to {output_path}")

def main():
    """
    Main entry point for T033: Calculate Pearson correlation between
    auditory cortex activation and learning rate proxy.
    """
    logger = setup_logging()
    logger.info("Starting T033: Brain-Behavior Correlation Analysis")

    try:
        # Load inputs
        betas_df = load_roi_betas(logger)
        slopes_df = load_learning_rate_slopes(logger)

        # Calculate correlation
        result = calculate_pearson_correlation(logger, betas_df, slopes_df)

        # Save results to JSON
        output_path = DATA_PROCESSED / "correlation_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Correlation results saved to {output_path}")

        # Generate scatter plot
        generate_scatter_plot(logger, betas_df, slopes_df)

        logger.info("T033 completed successfully.")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during T033: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()