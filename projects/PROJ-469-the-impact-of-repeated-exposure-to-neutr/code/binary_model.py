"""
Binary Model Analysis Pipeline (T024b).
Fits a linear regression using a binary ideology variable (median split)
instead of continuous ideology to test robustness of the interaction effect.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import logging
from pathlib import Path
from typing import Dict, Any

from config_manager import get_data_processed_path, get_results_path
from logging_config import get_logger

logger = get_logger(__name__)

def fit_binary_model(data: pd.DataFrame) -> Any:
    """
    Fits a linear regression model using binary ideology.
    Model: IAT_D ~ news_exposure_z * ideology_binary

    Args:
        data: DataFrame containing processed variables.

    Returns:
        Fitted OLS results object.
    """
    logger.info("Fitting binary ideology model...")

    # Ensure required columns exist
    required_cols = ['IAT_D_score', 'news_exposure_z', 'ideology_binary']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns for binary model: {missing}")

    # Prepare data
    # Drop rows with missing values in relevant columns
    model_data = data.dropna(subset=required_cols)

    if len(model_data) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for binary model.")

    y = model_data['IAT_D_score']
    X = model_data[['news_exposure_z', 'ideology_binary']]

    # Create interaction term manually to ensure control
    X['interaction'] = X['news_exposure_z'] * X['ideology_binary']

    # Add constant
    X = sm.add_constant(X)

    # Fit model
    model = sm.OLS(y, X)
    results = model.fit()

    logger.info(f"Binary model fitted. N={len(model_data)}, R-squared={results.rsquared:.4f}")

    return results

def save_binary_model_results(results: Any, output_path: Path) -> None:
    """
    Saves the binary model results to a CSV file.

    Args:
        results: Fitted OLS results object.
        output_path: Path to save the CSV file.
    """
    logger.info(f"Saving binary model results to: {output_path}")

    # Extract summary table
    summary_df = results.summary2().tables[1].as_data_frame()

    # Flatten index for easier saving if needed, or keep standard format
    # Standard format: index is term, columns are Coef, Std Err, t, P>|t|, [0.025, 0.975]
    summary_df.reset_index(inplace=True)
    summary_df.rename(columns={'index': 'term'}, inplace=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info("Binary model results saved.")

def run_binary_model_pipeline() -> Path:
    """
    Orchestrates the binary model analysis pipeline:
    1. Load processed data.
    2. Fit binary model.
    3. Save results.

    Returns:
        Path to the saved results file.
    """
    logger.info("Starting Binary Model Analysis Pipeline...")

    # Load processed data
    data_path = get_data_processed_path()
    # The imputed data should be written by preprocessing pipeline
    # We assume it's named 'imputed_data.csv' based on T014
    imputed_file = data_path / "imputed_data.csv"

    if not imputed_file.exists():
        raise FileNotFoundError(f"Imputed data file not found at: {imputed_file}. "
                                "Please ensure preprocessing pipeline (T014) has run successfully.")

    data = pd.read_csv(imputed_file)

    # Fit model
    results = fit_binary_model(data)

    # Save results
    output_path = get_results_path() / "binary_model.csv"
    save_binary_model_results(results, output_path)

    return output_path

def main():
    """Entry point for standalone execution."""
    from logging_config import setup_logging
    setup_logging()
    try:
        run_binary_model_pipeline()
        logger.info("Binary model pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Binary model pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
