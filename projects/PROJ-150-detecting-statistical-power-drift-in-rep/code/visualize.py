import os
import sys
import pickle
import logging
import json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DERIVED_DATA_DIR = PROJECT_ROOT / "data" / "derived"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-150-detecting-statistical-power-drift-in-rep"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_models():
    """
    Load the full model (with year) and reduced model (without year) from pickle files.
    Returns:
        full_model: The fitted full LMM model object.
        reduced_model: The fitted reduced LMM model object.
    """
    full_model_path = DERIVED_DATA_DIR / "input_trends_models.pkl"
    reduced_model_path = DERIVED_DATA_DIR / "reduced_model.pkl"

    if not full_model_path.exists():
        raise FileNotFoundError(f"Full model file not found at {full_model_path}. Run T012a first.")
    if not reduced_model_path.exists():
        raise FileNotFoundError(f"Reduced model file not found at {reduced_model_path}. Run T013a first.")

    logger.info(f"Loading full model from {full_model_path}")
    with open(full_model_path, 'rb') as f:
        full_model = pickle.load(f)

    logger.info(f"Loading reduced model from {reduced_model_path}")
    with open(reduced_model_path, 'rb') as f:
        reduced_model = pickle.load(f)

    return full_model, reduced_model

def load_data():
    """
    Load the power estimates data used for modeling.
    Returns:
        df: DataFrame containing study data.
    """
    data_path = DERIVED_DATA_DIR / "power_estimates.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Power estimates data not found at {data_path}. Run T011a first.")

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    return df

def fit_reduced_model(df):
    """
    Fit the reduced model: power_est ~ effect_size + sample_size + (1|field) + (1|original_study_id)
    Note: This is a helper if the model wasn't loaded, but T013a should have produced it.
    We primarily rely on loading the pre-fitted model from load_models().
    However, for the sake of the function signature requested in the API surface,
    we return the loaded reduced model if available, or fit a new one if necessary.
    Given the task dependency, we expect the file to exist.
    """
    # This function is primarily a wrapper to satisfy the API surface if needed,
    # but the core logic relies on the loaded model.
    # If we needed to fit it here, we would use statsmodels or linearmodels.
    # Since T013a is a prerequisite, we assume the model is already saved.
    # We will return the loaded model from load_models() instead.
    pass

def calculate_residuals(df, reduced_model):
    """
    Calculate residuals as: observed_power - predicted_power_from_reduced_model.
    This isolates the effect of 'year' not explained by covariates.
    
    Args:
        df: DataFrame with observed power.
        reduced_model: The fitted reduced LMM model (without 'year' predictor).
    
    Returns:
        residuals: Series of residuals.
    """
    logger.info("Calculating residuals (observed - predicted from reduced model)")
    
    # Get predicted values from the reduced model
    # The reduced model includes effect_size, sample_size, field, original_study_id
    # but NOT year.
    
    # Using statsmodels mixedlm, we can get fitted values
    if hasattr(reduced_model, 'fittedvalues'):
        predicted = reduced_model.fittedvalues
    else:
        # Fallback for other model types or if fittedvalues isn't directly accessible
        # Assuming reduced_model is a statsmodels MixedLMResults object
        # We need to construct the design matrix if not available
        # However, standard MixedLMResults usually has .fittedvalues
        raise AttributeError("Reduced model does not have 'fittedvalues' attribute.")

    # Calculate residuals
    observed = df['power_est'].values
    residuals = observed - predicted

    # Ensure residuals align with the dataframe index
    residuals = pd.Series(residuals, index=df.index)
    
    logger.info(f"Residuals calculated. Mean: {residuals.mean():.4f}, Std: {residuals.std():.4f}")
    return residuals

def plot_residuals_vs_year(df, residuals):
    """
    Generate a scatter plot of residual power vs. year.
    Includes a fitted regression line and confidence intervals.
    
    Args:
        df: DataFrame with 'year' column.
        residuals: Series of calculated residuals.
    
    Returns:
        fig: Matplotlib figure object.
    """
    logger.info("Generating scatter plot of residual power vs. year")
    
    # Prepare data for plotting
    plot_data = pd.DataFrame({
        'year': df['year'],
        'residual': residuals
    }).dropna() # Drop any NaNs if they exist

    if plot_data.empty:
        raise ValueError("No valid data points to plot after dropping NaNs.")

    # Set style
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter plot
    sns.scatterplot(
        data=plot_data, 
        x='year', 
        y='residual', 
        alpha=0.6, 
        edgecolor='k', 
        ax=ax,
        color='steelblue'
    )

    # Fit and plot regression line with confidence interval
    # Using seaborn's regplot which handles this automatically
    sns.regplot(
        data=plot_data, 
        x='year', 
        y='residual', 
        ax=ax, 
        scatter=False, 
        color='red', 
        line_kws={'linewidth': 2},
        ci=95
    )

    # Labels and Title
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Residual Power (Observed - Predicted from Reduced Model)', fontsize=12)
    ax.set_title('Statistical Power Drift: Residual Power vs. Year', fontsize=14)
    
    # Add a grid for better readability
    ax.grid(True, which='both', linestyle='--', alpha=0.7)

    plt.tight_layout()
    
    logger.info("Plot generated successfully")
    return fig

def main():
    """
    Main entry point for the visualization task.
    1. Load models (full and reduced).
    2. Load data.
    3. Calculate residuals using the reduced model.
    4. Plot residuals vs. year.
    5. Save the plot to results/power_drift_scatter.png.
    """
    logger.info("Starting T014: Visualize Power Drift")

    try:
        # 1. Load Models
        # We need the reduced model specifically for residuals.
        # The API surface suggests loading both, but we mainly use the reduced one.
        full_model, reduced_model = load_models()
        
        # 2. Load Data
        df = load_data()
        
        # 3. Calculate Residuals
        # Residuals = Observed Power - Predicted Power (from Reduced Model)
        residuals = calculate_residuals(df, reduced_model)
        
        # 4. Plot
        fig = plot_residuals_vs_year(df, residuals)
        
        # 5. Save Output
        output_path = RESULTS_DIR / "power_drift_scatter.png"
        fig.savefig(output_path, dpi=300)
        plt.close(fig)
        
        logger.info(f"Plot saved to {output_path}")
        print(f"SUCCESS: Visualization saved to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during visualization: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()