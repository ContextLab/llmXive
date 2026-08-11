import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.formula.api import gam
from statsmodels.iolib.summary import summary_col

from utils.config import get_config, get_output_paths
from utils.logging import setup_logger

# Configure logger
logger = setup_logger(__name__)

def load_behavioral_data() -> pd.DataFrame:
    """
    Load behavioral data from the processed directory.
    Expects data/processed/behavioral/behavioral_metrics.csv
    """
    config = get_config()
    paths = get_output_paths()
    file_path = paths.behavioral_metrics_file
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Behavioral metrics file not found at {file_path}. "
                                "Please run data preprocessing first.")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded behavioral data: {len(df)} subjects")
    return df

def load_centrality_or_pca_data() -> pd.DataFrame:
    """
    Load centrality metrics or PCA components based on VIF check results.
    Expects data/processed/centrality/model_predictors.csv
    """
    config = get_config()
    paths = get_output_paths()
    file_path = paths.model_predictors_file
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model predictors file not found at {file_path}. "
                                "Please run centrality analysis and VIF check first.")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded centrality/PCA data: {len(df)} subjects")
    return df

def load_mean_fd_data() -> pd.DataFrame:
    """
    Load Mean Framewise Displacement data.
    Expects data/processed/behavioral/fd_mean.csv
    """
    config = get_config()
    paths = get_output_paths()
    file_path = paths.fd_mean_file
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Mean FD file not found at {file_path}. "
                                "Please run FD analysis first.")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded Mean FD data: {len(df)} subjects")
    return df

def merge_all_data() -> pd.DataFrame:
    """
    Merge behavioral, centrality/PCA, and FD data on subject_id.
    """
    df_behavioral = load_behavioral_data()
    df_centrality = load_centrality_or_pca_data()
    df_fd = load_mean_fd_data()
    
    # Ensure subject_id is consistent type
    df_behavioral['subject_id'] = df_behavioral['subject_id'].astype(str)
    df_centrality['subject_id'] = df_centrality['subject_id'].astype(str)
    df_fd['subject_id'] = df_fd['subject_id'].astype(str)
    
    # Merge
    df = pd.merge(df_behavioral, df_centrality, on='subject_id', how='inner')
    df = pd.merge(df, df_fd, on='subject_id', how='inner')
    
    # Drop any remaining NaNs
    df = df.dropna()
    
    logger.info(f"Merged dataset: {len(df)} subjects")
    return df

def fit_linear_regression(df: pd.DataFrame) -> Tuple:
    """
    Fit a linear regression model based on the configuration.
    Formula depends on whether PCA was used or Global Centrality.
    """
    import statsmodels.api as sm
    
    config = get_config()
    # Determine predictor column name
    if 'PCA_Component_1' in df.columns:
        predictor_col = 'PCA_Component_1'
        formula = 'Improvement_Score ~ PCA_Component_1 + Age + Sex + Mean_FD'
    else:
        predictor_col = 'Global_Centrality'
        formula = 'Improvement_Score ~ Global_Centrality + Age + Sex + Mean_FD'
    
    logger.info(f"Fitting linear regression with formula: {formula}")
    
    try:
        model = sm.OLS.from_formula(formula, data=df)
        results = model.fit()
    except Exception as e:
        logger.error(f"Failed to fit linear regression: {e}")
        raise
    
    return results, formula

def fit_gam_polynomial(df: pd.DataFrame) -> Tuple:
    """
    Fit a GAM with polynomial term for non-linearity check.
    Uses the same predictor set as the linear model.
    """
    config = get_config()
    
    if 'PCA_Component_1' in df.columns:
        predictor_col = 'PCA_Component_1'
        # GAM formula with spline on the predictor
        formula = 'Improvement_Score ~ s(' + predictor_col + ', 4) + Age + Sex + Mean_FD'
    else:
        predictor_col = 'Global_Centrality'
        formula = 'Improvement_Score ~ s(' + predictor_col + ', 4) + Age + Sex + Mean_FD'
    
    logger.info(f"Fitting GAM with formula: {formula}")
    
    try:
        # statsmodels gam uses patsy-like formulas
        model = gam(formula, data=df)
        results = model.fit()
    except Exception as e:
        logger.error(f"Failed to fit GAM: {e}")
        raise
    
    return results, formula

def save_regression_summary(linear_results, gam_results, linear_formula, gam_formula, output_path: Path):
    """
    Save regression summaries to CSV.
    """
    # Extract key metrics
    linear_summary = {
        'Model': 'Linear',
        'R2': linear_results.rsquared,
        'Adj_R2': linear_results.rsquared_adj,
        'AIC': linear_results.aic,
        'BIC': linear_results.bic,
        'Formula': linear_formula
    }
    
    gam_summary = {
        'Model': 'GAM',
        'R2': gam_results.rsquared,
        'Adj_R2': gam_results.rsquared_adj,
        'AIC': gam_results.aic,
        'BIC': gam_results.bic,
        'Formula': gam_formula
    }
    
    df_summary = pd.DataFrame([linear_summary, gam_summary])
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Saved regression summary to {output_path}")

def generate_scatter_plot(df: pd.DataFrame, linear_results, gam_results, output_path: Path):
    """
    Generate a scatter plot with regression line and non-linearity fit (GAM).
    """
    config = get_config()
    paths = get_output_paths()
    
    # Determine predictor and response
    if 'PCA_Component_1' in df.columns:
        predictor_col = 'PCA_Component_1'
        predictor_label = 'PCA Component 1'
    else:
        predictor_col = 'Global_Centrality'
        predictor_label = 'Global Centrality'
    
    response_col = 'Improvement_Score'
    
    # Create figure
    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")
    
    # Scatter plot
    sns.scatterplot(x=predictor_col, y=response_col, data=df, 
                    alpha=0.6, color='blue', label='Subjects')
    
    # Sort data for line plotting
    sorted_indices = df.sort_values(predictor_col).index
    x_sorted = df.loc[sorted_indices, predictor_col]
    y_sorted = df.loc[sorted_indices, response_col]
    
    # Plot Linear Regression line
    # Get predictions from linear model
    linear_pred = linear_results.predict(df)
    linear_pred_sorted = linear_pred.loc[sorted_indices]
    plt.plot(x_sorted, linear_pred_sorted, color='red', linewidth=2, 
             label='Linear Fit', zorder=5)
    
    # Plot GAM fit (non-linearity)
    # We need to generate predictions from the GAM model over a range
    x_range = np.linspace(df[predictor_col].min(), df[predictor_col].max(), 100)
    df_range = df.copy()
    df_range[predictor_col] = x_range
    
    # Re-fit GAM on this range to get smooth curve? 
    # Actually, we can predict on the new dataframe if the formula is compatible
    # But simpler: just plot the GAM result points if available, or refit on range
    # Since statsmodels GAM predict works on new dataframes with same structure:
    try:
        gam_pred_range = gam_results.predict(df_range)
        plt.plot(x_range, gam_pred_range, color='green', linewidth=2, 
                 linestyle='--', label='GAM (Non-linear) Fit', zorder=6)
    except Exception as e:
        logger.warning(f"Could not plot GAM fit curve: {e}")
    
    plt.xlabel(predictor_label)
    plt.ylabel('Motor Memory Improvement Score')
    plt.title(f'Impact of {predictor_label} on Motor Memory Consolidation')
    plt.legend()
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Saved scatter plot to {output_path}")

def run_regression_analysis():
    """
    Main function to run the full regression analysis pipeline including plotting.
    """
    logger.info("Starting regression analysis...")
    
    # Load and merge data
    df = merge_all_data()
    
    if len(df) == 0:
        logger.error("No data available for regression analysis.")
        return
    
    # Fit models
    linear_results, linear_formula = fit_linear_regression(df)
    gam_results, gam_formula = fit_gam_polynomial(df)
    
    # Save summary
    config = get_config()
    paths = get_output_paths()
    summary_path = paths.linear_model_summary_file
    save_regression_summary(linear_results, gam_results, linear_formula, gam_formula, summary_path)
    
    # Generate plot
    plot_path = paths.scatter_plot_file
    generate_scatter_plot(df, linear_results, gam_results, plot_path)
    
    logger.info("Regression analysis completed successfully.")

def main():
    """
    Entry point for the regression analysis script.
    """
    logger.info("Running regression analysis main...")
    run_regression_analysis()
    logger.info("Done.")

if __name__ == "__main__":
    main()