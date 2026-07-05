import os
import sys
import math
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from src.utils.config import get_project_root, get_processed_data_dir, get_figures_dir, get_interim_data_dir
from src.utils.logging import setup_logger

# Ensure seaborn style is applied for publication quality
sns.set_style("whitegrid")

def load_final_dataset():
    """Load the final processed dataset."""
    data_dir = get_processed_data_dir()
    file_path = data_dir / "final_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Final dataset not found at {file_path}. Please run T020 first.")
    return pd.read_csv(file_path)

def run_loso_cross_validation(df, complexity_col='syllable_count', noise_col='noise_level_db'):
    """
    Perform Leave-One-Species-Out (LOSO) cross-validation.
    Returns a dictionary of results for each left-out species.
    """
    logger = logging.getLogger(__name__)
    species_list = df['species_id'].unique()
    results = []

    logger.info(f"Starting LOSO CV with {len(species_list)} species.")

    for i, test_species in enumerate(species_list):
        test_mask = df['species_id'] == test_species
        train_df = df[~test_mask]
        test_df = df[test_mask]

        if len(train_df) == 0 or len(test_df) == 0:
            continue

        # Fit model on training data
        try:
            model = smf.mixedlm(f"{complexity_col} ~ {noise_col}", train_df, groups=train_df['species_id'])
            fitted = model.fit()

            # Predict on test data
            predictions = fitted.predict(test_df)
            residuals = test_df[complexity_col].values - predictions

            mse = np.mean(residuals**2)
            results.append({
                'left_out_species': test_species,
                'mse': mse,
                'n_test': len(test_df)
            })
        except Exception as e:
            logger.warning(f"Failed to fit model for LOSO iteration {test_species}: {e}")

    return pd.DataFrame(results)

def save_loso_results(results_df):
    """Save LOSO results to interim directory."""
    interim_dir = get_interim_data_dir()
    output_path = interim_dir / "loso_cv_results.csv"
    results_df.to_csv(output_path, index=False)
    return output_path

def run_t027_loso_analysis():
    """Wrapper to run LOSO analysis and save results."""
    logger = setup_logger("modeling_t027")
    df = load_final_dataset()
    results = run_loso_cross_validation(df)
    path = save_loso_results(results)
    logger.info(f"LOSO analysis complete. Results saved to {path}")
    return results

def generate_residual_diagnostics():
    """
    Generate residual diagnostics for the Linear Mixed-Effects model.
    Produces:
    1. Q-Q plot of residuals
    2. Residuals vs Fitted plot
    Saves figures to data/figures/
    """
    logger = setup_logger("modeling_t028")
    
    # Load data
    df = load_final_dataset()
    complexity_col = 'syllable_count'
    noise_col = 'noise_level_db'
    groups_col = 'species_id'

    logger.info("Fitting LME model for residual diagnostics...")
    try:
        # Fit the model: complexity ~ noise + (1|species)
        # Note: The plan specifies (1|species) + (1|location), but location might not be in the final dataset
        # depending on T020. We attempt to include it if present, otherwise fallback.
        if 'location_id' in df.columns:
            formula = f"{complexity_col} ~ {noise_col} + (1|{groups_col}) + (1|location_id)"
        else:
            formula = f"{complexity_col} ~ {noise_col} + (1|{groups_col})"
        
        model = smf.mixedlm(formula, df, groups=df[groups_col])
        fitted_model = model.fit()
        
        # Extract residuals and fitted values
        residuals = fitted_model.resid
        fitted_values = fitted_model.fittedvalues

        # Ensure figures directory exists
        figures_dir = get_figures_dir()
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Create a figure with 2 subplots
        fig, axs = plt.subplots(1, 2, figsize=(14, 6))

        # 1. Q-Q Plot
        # Use statsmodels' ProbPlot for proper quantile matching
        sm.qqplot(residuals, line='45', fit=True, ax=axs[0])
        axs[0].set_title('Normal Q-Q Plot of Residuals')
        axs[0].set_xlabel('Theoretical Quantiles')
        axs[0].set_ylabel('Standardized Residuals')

        # 2. Residuals vs Fitted Plot
        axs[1].scatter(fitted_values, residuals, alpha=0.6, edgecolors='w', s=50)
        # Add a horizontal line at 0
        axs[1].axhline(0, color='red', linestyle='--', linewidth=2)
        axs[1].set_title('Residuals vs Fitted')
        axs[1].set_xlabel('Fitted Values')
        axs[1].set_ylabel('Residuals')
        
        # Add a lowess trend line to check for patterns
        from statsmodels.nonparametric.smoothers_lowess import lowess
        smoothed = lowess(residuals, fitted_values, frac=0.3)
        axs[1].plot(smoothed[:, 0], smoothed[:, 1], color='blue', linewidth=2, label='Trend')
        axs[1].legend()

        plt.tight_layout()
        
        # Save the plot
        output_path = figures_dir / "residual_diagnostics.png"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Residual diagnostics saved to {output_path}")

        # Optional: Save raw residuals to CSV for further inspection
        residuals_df = pd.DataFrame({
            'residuals': residuals,
            'fitted_values': fitted_values
        })
        residuals_csv_path = get_interim_data_dir() / "model_residuals.csv"
        residuals_df.to_csv(residuals_csv_path, index=False)
        logger.info(f"Raw residuals saved to {residuals_csv_path}")

        return True

    except Exception as e:
        logger.error(f"Failed to generate residual diagnostics: {e}")
        raise

def main():
    """Main entry point for T028."""
    logger = setup_logger("main_t028")
    logger.info("Starting T028: Residual Diagnostics Generation")
    try:
        generate_residual_diagnostics()
        logger.info("T028 completed successfully.")
    except Exception as e:
        logger.error(f"T028 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()