import os
import sys
import pickle
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure directories exist
RESULTS_DIR = Path("results")
DATA_DERIVED_DIR = Path("data/derived")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_models():
    """
    Load the full and reduced LMM models from disk.
    Returns: (full_model, reduced_model) or (None, None) if not found.
    """
    full_model_path = RESULTS_DIR / "full_model.pkl"
    reduced_model_path = RESULTS_DIR / "reduced_model.pkl"

    if not full_model_path.exists():
        logger.warning(f"Full model not found at {full_model_path}")
        full_model = None
    else:
        with open(full_model_path, 'rb') as f:
            full_model = pickle.load(f)

    if not reduced_model_path.exists():
        logger.warning(f"Reduced model not found at {reduced_model_path}")
        reduced_model = None
    else:
        with open(reduced_model_path, 'rb') as f:
            reduced_model = pickle.load(f)

    return full_model, reduced_model

def load_data():
    """
    Load the cleaned data from disk.
    Returns: DataFrame or None if not found.
    """
    data_path = DATA_DERIVED_DIR / "cleaned_data.csv"
    if not data_path.exists():
        logger.error(f"Cleaned data not found at {data_path}")
        return None
    return pd.read_csv(data_path)

def fit_reduced_model(data):
    """
    Fit the reduced model: power_est ~ effect_size + sample_size + (1|field) + (1|original_study_id)
    Note: This is a helper if the model isn't pre-saved, but T012 should have saved it.
    We assume T012 saved it to results/reduced_model.pkl.
    """
    logger.info("Reduced model should be pre-loaded from T012. If missing, re-running fit logic.")
    # In a real pipeline, we would re-fit here if missing, but for T028 we rely on T012 output.
    return None

def calculate_residuals(data, reduced_model):
    """
    Calculate residuals: observed_power - predicted_power_from_REDUCED_model.
    Returns: DataFrame with residuals added.
    """
    if reduced_model is None:
        logger.error("Reduced model is None. Cannot calculate residuals.")
        return None

    # Predict using the reduced model
    # Assuming reduced_model has a 'predict' method compatible with the data
    try:
        predictions = reduced_model.predict(data)
        data['residual_power'] = data['power_est'] - predictions
        logger.info(f"Calculated residuals. Shape: {data.shape}")
        return data
    except Exception as e:
        logger.error(f"Error predicting with reduced model: {e}")
        return None

def plot_residuals_vs_year(data):
    """
    Generate a scatter plot of residual power vs. year.
    Saves to results/power_drift_scatter.png.
    """
    if data is None or 'residual_power' not in data.columns or 'year' not in data.columns:
        logger.error("Invalid data for residual plot.")
        return

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=data, x='year', y='residual_power', alpha=0.5, s=30)
    sns.regplot(data=data, x='year', y='residual_power', scatter=False, color='red', line_kws={'linewidth': 2})
    plt.title('Residual Power vs. Year (Drift after controlling for effect_size, sample_size, and random effects)')
    plt.xlabel('Year')
    plt.ylabel('Residual Power')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    output_path = RESULTS_DIR / "power_drift_scatter.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved residual plot to {output_path}")

def plot_null_distribution_vs_observed():
    """
    Plot the null distribution of the input-permutation drift (from T027)
    and overlay the observed slope (from T012/T026).
    Output: results/null_distribution_plot.png
    """
    # Load observed slope from lmm_final_summary.json
    lmm_summary_path = RESULTS_DIR / "lmm_final_summary.json"
    observed_slope = None
    if lmm_summary_path.exists():
        with open(lmm_summary_path, 'r') as f:
            summary = json.load(f)
            observed_slope = summary.get('slope_year')
            if observed_slope is not None:
                observed_slope = float(observed_slope)
                logger.info(f"Loaded observed slope: {observed_slope}")
    else:
        logger.warning(f"Could not find {lmm_summary_path}. Cannot plot observed slope.")

    # Load null distribution from T027
    null_dist_path = RESULTS_DIR / "null_distribution_implied_power.csv"
    if not null_dist_path.exists():
        logger.error(f"Null distribution file not found at {null_dist_path}. Cannot plot.")
        return

    try:
        null_df = pd.read_csv(null_dist_path)
        if 'simulated_drift' not in null_df.columns:
            logger.error("Column 'simulated_drift' not found in null distribution CSV.")
            return

        logger.info(f"Loaded null distribution with {len(null_df)} samples.")
    except Exception as e:
        logger.error(f"Error loading null distribution: {e}")
        return

    # Plotting
    plt.figure(figsize=(10, 6))
    sns.histplot(null_df['simulated_drift'], kde=True, color='skyblue', edgecolor='black', alpha=0.7, bins=50)
    
    if observed_slope is not None:
        plt.axvline(x=observed_slope, color='red', linestyle='--', linewidth=2, label=f'Observed Slope ({observed_slope:.4f})')
        plt.legend()

    plt.title('Null Distribution of Drift (Input Permutation) vs. Observed Slope')
    plt.xlabel('Simulated Drift Coefficient')
    plt.ylabel('Frequency')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    output_path = RESULTS_DIR / "null_distribution_plot.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved null distribution plot to {output_path}")

def main():
    """
    Main entry point for visualization tasks.
    1. Plot residuals vs year (T013 requirement)
    2. Plot null distribution vs observed slope (T028 requirement)
    """
    logger.info("Starting visualization pipeline.")

    # T013: Residuals vs Year
    # Load data and reduced model (assuming T012 saved reduced_model.pkl)
    data = load_data()
    full_model, reduced_model = load_models()

    if data is not None and reduced_model is not None:
        data_with_resid = calculate_residuals(data, reduced_model)
        if data_with_resid is not None:
            # Save residuals for verification (T013)
            residuals_path = DATA_DERIVED_DIR / "residuals.csv"
            data_with_resid.to_csv(residuals_path, index=False)
            logger.info(f"Saved residuals to {residuals_path}")
            
            plot_residuals_vs_year(data_with_resid)
        else:
            logger.warning("Skipping residual plot due to calculation failure.")
    else:
        logger.warning("Skipping residual plot: missing data or reduced model.")

    # T028: Null Distribution Plot
    plot_null_distribution_vs_observed()

    logger.info("Visualization pipeline complete.")

if __name__ == "__main__":
    main()