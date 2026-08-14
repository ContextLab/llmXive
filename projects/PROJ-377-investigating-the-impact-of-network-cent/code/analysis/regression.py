import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy

from utils.logging import setup_logger
from utils.config import get_config

logger = setup_logger(__name__)

def load_behavioral_data() -> pd.DataFrame:
    """
    Load behavioral data (improvement scores) from the processed data directory.
    Expected file: data/processed/behavioral/behavioral_metrics.csv
    """
    config = get_config()
    path = config.output_paths.processed_dir / "behavioral" / "behavioral_metrics.csv"
    
    if not path.exists():
        raise FileNotFoundError(f"Behavioral data not found at {path}. "
                                "Ensure T013/T015 have been run successfully.")
    
    df = pd.read_csv(path)
    required_cols = ['subject_id', 'improvement']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Behavioral data missing required columns: {missing}")
    
    logger.info(f"Loaded behavioral data for {len(df)} subjects from {path}")
    return df

def load_centrality_or_pca_data() -> pd.DataFrame:
    """
    Load either Global Centrality data or PCA components based on T022 output.
    Checks for 'model_predictors.csv' created in T022.
    """
    config = get_config()
    path = config.output_paths.processed_dir / "centrality" / "model_predictors.csv"
    
    if not path.exists():
        raise FileNotFoundError(f"Centrality/PCA predictors not found at {path}. "
                                "Ensure T022 has been run successfully.")
    
    df = pd.read_csv(path)
    # Expected columns: subject_id, Age, Sex, Mean_FD, and either Global_Centrality or PCA_Component_1
    required_base = ['subject_id', 'Age', 'Sex', 'Mean_FD']
    missing_base = [c for c in required_base if c not in df.columns]
    if missing_base:
        raise ValueError(f"Predictors data missing base columns: {missing_base}")
    
    # Identify the centrality/PCA column
    centrality_cols = [c for c in df.columns if 'Global_Centrality' in c or 'PCA_Component' in c]
    if len(centrality_cols) == 0:
        raise ValueError("Predictors data missing centrality or PCA component column.")
    
    # We expect exactly one main predictor column for the model
    main_predictor = centrality_cols[0]
    logger.info(f"Loaded predictors with main feature: {main_predictor} from {path}")
    
    return df, main_predictor

def load_mean_fd_data() -> pd.DataFrame:
    """
    Load Mean FD data. Note: This is now merged in load_centrality_or_pca_data,
    but kept for API compatibility if needed separately.
    """
    # In current flow, FD is loaded with centrality/PCA data in T022.
    # This function is a stub for API compatibility if T022 was split.
    return pd.DataFrame()

def merge_all_data(behavioral_df: pd.DataFrame, predictor_df: pd.DataFrame, main_predictor: str) -> pd.DataFrame:
    """
    Merge behavioral data with predictor data on subject_id.
    Drops rows with any missing values in the required columns.
    """
    merged = pd.merge(behavioral_df, predictor_df, on='subject_id', how='inner')
    
    # Ensure required columns exist
    required = ['subject_id', 'improvement', 'Age', 'Sex', 'Mean_FD', main_predictor]
    missing = [c for c in required if c not in merged.columns]
    if missing:
        raise ValueError(f"Merged data missing columns: {missing}")
    
    # Drop rows with missing values
    initial_count = len(merged)
    merged = merged.dropna(subset=required)
    final_count = len(merged)
    
    if initial_count > final_count:
        logger.warning(f"Dropped {initial_count - final_count} subjects due to missing values.")
    
    logger.info(f"Merged dataset contains {len(merged)} subjects.")
    return merged

def fit_linear_regression(df: pd.DataFrame, main_predictor: str) -> Tuple[sm.RegressionResultsWrapper, str]:
    """
    Fit the linear regression model based on the conditional logic:
    IF PCA used (column name contains 'PCA_Component'):
       Formula: Improvement ~ PCA_Component + Age + Sex + Mean_FD
    ELSE (Global Centrality used):
       Formula: Improvement ~ Global_Centrality + Age + Sex + Mean_FD
    
    Returns:
       results: The fitted statsmodels results object.
       formula_str: The formula string used.
    """
    # Determine formula
    if 'PCA_Component' in main_predictor:
        # Use the specific PCA column name found
        predictor_name = main_predictor
        formula = f"improvement ~ {predictor_name} + Age + Sex + Mean_FD"
    else:
        # Assume Global_Centrality
        formula = f"improvement ~ {main_predictor} + Age + Sex + Mean_FD"
    
    logger.info(f"Fitting linear regression with formula: {formula}")
    
    try:
        model = smf.ols(formula, data=df)
        results = model.fit()
    except Exception as e:
        logger.error(f"Failed to fit linear regression: {e}")
        raise
    
    return results, formula

def save_regression_summary(results: sm.RegressionResultsWrapper, formula: str, output_path: Path):
    """
    Save the regression summary to a CSV file.
    Includes coefficients, p-values, R-squared, and AIC/BIC.
    """
    # Extract key statistics
    summary_data = {
        'metric': ['R-squared', 'Adj. R-squared', 'AIC', 'BIC', 'F-statistic', 'P-value (F-stat)'],
        'value': [
            results.rsquared,
            results.rsquared_adj,
            results.aic,
            results.bic,
            results.fvalue,
            results.f_pvalue
        ]
    }
    
    df_model = pd.DataFrame(summary_data)
    df_model.to_csv(output_path, index=False)
    
    # Also save detailed coefficient table
    coef_table = results.summary2().tables[1]
    coef_df = pd.DataFrame(coef_table)
    # Clean up the dataframe if it has MultiIndex or weird formatting
    # statsmodels summary2 tables are often complex, so we reconstruct from params
    params = results.params
    std_err = results.bse
    t_vals = results.tvalues
    p_vals = results.pvalues
    
    coef_summary = pd.DataFrame({
        'term': params.index,
        'coefficient': params.values,
        'std_error': std_err.values,
        't_statistic': t_vals.values,
        'p_value': p_vals.values
    })
    
    coef_path = output_path.parent / "linear_model_coefficients.csv"
    coef_summary.to_csv(coef_path, index=False)
    
    logger.info(f"Saved regression summary to {output_path} and coefficients to {coef_path}")

def generate_scatter_plot(df: pd.DataFrame, main_predictor: str, output_path: Path):
    """
    Generate a scatter plot of Improvement vs the main predictor.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x=main_predictor, y='improvement', alpha=0.6)
    
    # Fit a simple line for visualization
    z = np.polyfit(df[main_predictor], df['improvement'], 1)
    p = np.poly1d(z)
    plt.plot(df[main_predictor], p(df[main_predictor]), "r--", label=f"Fit: y={z[0]:.3f}x+{z[1]:.3f}")
    
    plt.title(f"Motor Memory Improvement vs {main_predictor}")
    plt.xlabel(main_predictor)
    plt.ylabel("Improvement Score")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved scatter plot to {output_path}")

def run_regression_analysis():
    """
    Main entry point for the regression analysis task (T024).
    Orchestrates loading, merging, fitting, and saving.
    """
    config = get_config()
    output_dir = config.output_paths.processed_dir / "regression"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    logger.info("Loading behavioral data...")
    behavioral_df = load_behavioral_data()
    
    logger.info("Loading centrality/PCA data...")
    predictor_df, main_predictor = load_centrality_or_pca_data()
    
    # 2. Merge
    logger.info("Merging datasets...")
    merged_df = merge_all_data(behavioral_df, predictor_df, main_predictor)
    
    if len(merged_df) < 5:
        raise ValueError("Insufficient data points for regression after merging.")
    
    # 3. Fit Model
    logger.info("Fitting linear regression model...")
    results, formula = fit_linear_regression(merged_df, main_predictor)
    
    # 4. Save Summary
    summary_path = output_dir / "linear_model_summary.csv"
    save_regression_summary(results, formula, summary_path)
    
    # 5. Generate Plot
    plot_path = output_dir / "regression_scatter.png"
    generate_scatter_plot(merged_df, main_predictor, plot_path)
    
    logger.info("Regression analysis completed successfully.")
    return results

def main():
    """
    CLI entry point.
    """
    run_regression_analysis()

if __name__ == "__main__":
    main()