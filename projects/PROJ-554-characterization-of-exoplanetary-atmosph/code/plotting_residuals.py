import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_config
from utils import setup_logging

def load_retrieval_results() -> pd.DataFrame:
    """Load retrieval results from the processed CSV."""
    config = get_config()
    file_path = config["paths"]["processed_dir"] / "retrieval_results.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found at {file_path}")
    
    return pd.read_csv(file_path)

def load_regression_results() -> Dict[str, Any]:
    """Load regression results from the JSON file."""
    config = get_config()
    file_path = config["paths"]["processed_dir"] / "regression_results.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Regression results file not found at {file_path}")
    
    import json
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_residuals(
    df: pd.DataFrame, 
    regression_results: Dict[str, Any]
) -> pd.DataFrame:
    """
    Calculate residuals based on the regression model.
    
    If a fallback to Survival Regression occurred, we use the Cox PH baseline
    hazard or AFT predictions if available. For this implementation, we assume
    the regression_results contains 'predicted_values' if available, or we
    construct a simple linear prediction based on coefficients if the model
    was standard Tobit/OLS.
    
    For the purpose of this diagnostic plot, we calculate residuals as:
    Observed Water Mixing Ratio - Predicted Water Mixing Ratio.
    
    If the model used Survival Regression (fallback), we calculate residuals
    as the difference between the observed value (or limit) and the median
    survival time prediction (or expected value) if available.
    """
    df = df.copy()
    
    # Check if we have pre-calculated predictions in the results
    # This assumes T027 saves predictions if available
    if "predicted_values" in regression_results:
        df["predicted_water_mixing"] = regression_results["predicted_values"]
    else:
        # Fallback: If we have coefficients and predictors, we might need to reconstruct.
        # However, T027 is expected to save the results. If predictions aren't saved,
        # we cannot accurately calculate residuals without re-running the model.
        # We will raise an error if predictions are missing, as this is a critical
        # dependency for the residual plot.
        raise ValueError(
            "Regression results must contain 'predicted_values' to calculate residuals. "
            "Please ensure T027 saves predicted values in regression_results.json."
        )
    
    # Calculate residuals
    # Note: For censored data, residuals are tricky. We calculate them for
    # non-censored points primarily, but we can also plot residuals for censored points
    # as (Observed Limit - Predicted) to see if the limit is consistent.
    df["residuals"] = df["water_mixing_ratio"] - df["predicted_water_mixing"]
    
    return df

def plot_residuals(
    df: pd.DataFrame,
    output_path: Path,
    fallback_triggered: bool = False
) -> None:
    """
    Generate a residual plot: Residuals vs. Predicted Values.
    
    This plot helps identify:
    1. Heteroscedasticity (funnel shape)
    2. Non-linearity (curved pattern)
    3. Outliers
    
    Points are colored by whether they are upper limits (censored) or detections.
    """
    if output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Separate detections and upper limits
    detections = df[~df["is_upper_limit"]]
    upper_limits = df[df["is_upper_limit"]]
    
    # Plot Detections
    if not detections.empty:
        ax.scatter(
            detections["predicted_water_mixing"],
            detections["residuals"],
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5,
            label='Detections',
            color='blue'
        )
    
    # Plot Upper Limits
    # For upper limits, the residual is (Limit - Predicted).
    # We plot them with a downward arrow or distinct marker to indicate direction.
    if not upper_limits.empty:
        ax.scatter(
            upper_limits["predicted_water_mixing"],
            upper_limits["residuals"],
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5,
            label='Upper Limits (Censored)',
            color='red',
            marker='v' # Downward triangle to suggest 'at most'
        )
    
    # Add a horizontal line at y=0
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5, label='Zero Residual')
    
    # Labels and Title
    title = "Residuals vs. Predicted Water Mixing Ratio"
    if fallback_triggered:
        title += " (Survival Regression Fallback)"
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel("Predicted Log10 Water Mixing Ratio", fontsize=12)
    ax.set_ylabel("Residual (Observed - Predicted)", fontsize=12)
    
    ax.legend(loc='best')
    
    # Tight layout
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logging.info(f"Residual plot saved to {output_path}")

def main() -> None:
    """Main entry point for generating the residual plot."""
    config = get_config()
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting residual plot generation (T029b)...")
    
    try:
        # 1. Load Data
        logger.info("Loading retrieval results...")
        retrieval_df = load_retrieval_results()
        
        logger.info("Loading regression results...")
        regression_results = load_regression_results()
        
        fallback_triggered = regression_results.get("fallback_triggered", False)
        
        # 2. Calculate Residuals
        logger.info("Calculating residuals...")
        df_with_residuals = calculate_residuals(retrieval_df, regression_results)
        
        # 3. Generate Plot
        output_path = config["paths"]["results_dir"] / "plots" / "residuals.png"
        logger.info(f"Generating plot at {output_path}...")
        plot_residuals(df_with_residuals, output_path, fallback_triggered)
        
        logger.info("T029b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during residual plot generation: {e}")
        raise

if __name__ == "__main__":
    main()