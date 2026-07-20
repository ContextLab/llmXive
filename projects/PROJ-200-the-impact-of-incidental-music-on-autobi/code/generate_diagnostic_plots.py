"""
Diagnostic Plot Generation Module.

Generates diagnostic plots for the regression model results:
- Residuals vs Fitted
- Normal Q-Q plot
- Scale-Location plot
- Residuals vs Leverage plot

Outputs are saved to data/final/plots/
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure consistent styling
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_regression_results() -> pd.DataFrame:
    """
    Load the regression summary results.

    Returns:
        pd.DataFrame: The regression summary with coefficients, SEs, and p-values.
    """
    root = get_project_root()
    file_path = root / "data" / "final" / "regression_summary.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Regression results file not found at {file_path}. "
            "Please run the modeling pipeline first (T038)."
        )

    df = pd.read_csv(file_path)
    logger.info(f"Loaded regression results from {file_path}")
    return df

def load_user_track_pairs() -> pd.DataFrame:
    """
    Load the aggregated User-Track pairs dataset.

    Returns:
        pd.DataFrame: The user-track pairs with residuals and fitted values.
    """
    root = get_project_root()
    file_path = root / "data" / "processed" / "user_track_pairs.parquet"

    if not file_path.exists():
        raise FileNotFoundError(
            f"User-Track pairs file not found at {file_path}. "
            "Please run the aggregation pipeline first (T029)."
        )

    df = pd.read_parquet(file_path)
    logger.info(f"Loaded user-track pairs from {file_path}")
    return df

def calculate_residuals(model_results: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate residuals and fitted values for plotting.

    Args:
        model_results: DataFrame with model coefficients.
        data: DataFrame with original data including predictors.

    Returns:
        pd.DataFrame: Data with added 'fitted' and 'residual' columns.
    """
    # This function assumes the data has been processed to include
    # the necessary columns for prediction. If the modeling step
    # saved fitted values and residuals, we use those directly.
    # Otherwise, we reconstruct them.

    # Check if residuals are already present (saved by modeling step)
    if 'residuals' in data.columns and 'fitted' in data.columns:
        logger.info("Using pre-calculated residuals and fitted values.")
        return data

    # Fallback: reconstruct if columns are missing (should not happen if pipeline is correct)
    # We assume the main model was: mean_vividness ~ residualized_exposure + popularity
    # We need the coefficients to reconstruct.
    # Since we are generating plots for the main model, we expect the data to be
    # the one used in the final model fit.

    # For the purpose of this task, we assume the data passed here is the
    # one used for the final model and contains the necessary columns.
    # If the modeling step saved the model object or predictions, we would load them.
    # Here we simulate the calculation based on typical statsmodels output structure
    # if the data was enriched during the modeling step.

    # NOTE: In a real scenario, the modeling step (T033/T034) should save
    # the predictions and residuals into the parquet file or a separate CSV.
    # If they are missing, we cannot generate accurate plots without re-running the model.
    # We will raise an error if the required columns are missing to prevent silent failure.

    required_cols = ['mean_vividness', 'residualized_exposure_score', 'overall_popularity_score']
    if not all(col in data.columns for col in required_cols):
        raise ValueError(
            f"Data must contain {required_cols} to calculate residuals. "
            "Ensure the modeling step saved predictions or the data is enriched."
        )

    # Extract coefficients from the regression_summary if possible, or assume standard model
    # For now, we assume the modeling step saved 'fitted' and 'residuals' columns.
    # If not, we cannot proceed without re-fitting.
    # Let's assume the data passed here is the one that was used for the model
    # and if it lacks 'fitted'/'residuals', we try to compute them if we have the model object.
    # Since we only have the summary CSV, we cannot re-fit easily without the model object.
    # However, the task T039 (permutation) and T038 (summary) imply the model was run.
    # We will assume the `user_track_pairs.parquet` was updated by the modeling step
    # to include 'fitted' and 'residuals'. If not, we raise an error.

    if 'fitted' not in data.columns or 'residuals' not in data.columns:
        # Attempt to compute if we can get coefficients from summary
        # This is a fallback and might be approximate
        logger.warning("Fitted values and residuals not found in data. Attempting to reconstruct from summary.")
        # This is complex without the full model object. We will raise an error
        # to force the modeling step to save these values.
        raise ValueError(
            "The 'fitted' and 'residuals' columns are missing from the data. "
            "Please ensure the modeling step (T033/T034) saves these columns to the output dataset."
        )

    return data

def create_residuals_plot(data: pd.DataFrame, output_path: Path) -> None:
    """
    Create Residuals vs Fitted plot.

    Args:
        data: DataFrame with 'fitted' and 'residuals' columns.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x='fitted',
        y='residuals',
        data=data,
        alpha=0.6,
        edgecolor=None
    )
    plt.axhline(0, color='red', linestyle='--', linewidth=1.5)
    plt.title('Residuals vs Fitted')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved residuals vs fitted plot to {output_path}")

def create_qq_plot(data: pd.DataFrame, output_path: Path) -> None:
    """
    Create Normal Q-Q plot of residuals.

    Args:
        data: DataFrame with 'residuals' column.
        output_path: Path to save the plot.
    """
    from scipy import stats

    residuals = data['residuals'].dropna()
    fig = plt.figure(figsize=(8, 8))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title('Normal Q-Q Plot')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Q-Q plot to {output_path}")

def create_scale_location_plot(data: pd.DataFrame, output_path: Path) -> None:
    """
    Create Scale-Location plot (sqrt(|residuals|) vs Fitted).

    Args:
        data: DataFrame with 'fitted' and 'residuals' columns.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    data['sqrt_residual'] = np.sqrt(np.abs(data['residuals']))
    sns.scatterplot(
        x='fitted',
        y='sqrt_residual',
        data=data,
        alpha=0.6,
        edgecolor=None
    )
    # Add a smoothed line
    sns.regplot(
        x='fitted',
        y='sqrt_residual',
        data=data,
        scatter=False,
        color='red',
        line_kws={'linestyle': '--'}
    )
    plt.title('Scale-Location')
    plt.xlabel('Fitted Values')
    plt.ylabel(r'$\sqrt{|Residuals|}$')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved scale-location plot to {output_path}")

def create_residuals_leverage_plot(data: pd.DataFrame, output_path: Path) -> None:
    """
    Create Residuals vs Leverage plot.

    Args:
        data: DataFrame with 'fitted', 'residuals', and 'leverage' columns.
        output_path: Path to save the plot.
    """
    # If leverage is not present, we calculate it approximately or skip
    # For simplicity, we assume the modeling step saved leverage if available.
    # If not, we might need to calculate it, which requires the design matrix.
    # We will try to use existing columns.
    if 'leverage' not in data.columns:
        # Fallback: approximate leverage or skip.
        # Since we don't have the full model matrix here, we will raise a warning
        # and try to plot without leverage if possible, or skip this plot.
        logger.warning("Leverage values not found. Skipping Residuals vs Leverage plot.")
        return

    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        x='leverage',
        y='residuals',
        data=data,
        alpha=0.6,
        edgecolor=None
    )
    plt.title('Residuals vs Leverage')
    plt.xlabel('Leverage')
    plt.ylabel('Residuals')
    # Add Cook's distance contours if possible
    # This requires more complex calculation, so we skip for now
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved residuals vs leverage plot to {output_path}")

def generate_all_plots() -> None:
    """
    Generate all diagnostic plots and save them to data/final/plots/.
    """
    root = get_project_root()
    plots_dir = root / "data" / "final" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting diagnostic plot generation...")

    try:
        # Load data
        regression_summary = load_regression_results()
        user_track_data = load_user_track_pairs()

        # Calculate residuals if not present
        enriched_data = calculate_residuals(regression_summary, user_track_data)

        # Generate plots
        create_residuals_plot(
            enriched_data,
            plots_dir / "residuals_vs_fitted.png"
        )
        create_qq_plot(
            enriched_data,
            plots_dir / "qq_plot.png"
        )
        create_scale_location_plot(
            enriched_data,
            plots_dir / "scale_location.png"
        )
        create_residuals_leverage_plot(
            enriched_data,
            plots_dir / "residuals_vs_leverage.png"
        )

        logger.info("All diagnostic plots generated successfully.")

    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

def main():
    """Main entry point for the script."""
    logger.info("Running generate_diagnostic_plots script.")
    generate_all_plots()
    logger.info("Script completed.")

if __name__ == "__main__":
    main()