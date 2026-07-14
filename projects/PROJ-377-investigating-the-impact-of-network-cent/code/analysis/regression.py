"""
Regression analysis module for motor memory consolidation study.

Implements linear regression models based on centrality metrics or PCA components,
with appropriate covariates (Age, Sex, Mean_FD).
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import statsmodels.api as sm
import statsmodels.formula.api as smf
from utils.config import get_config, get_output_paths, get_regression_config
from utils.logging import setup_logger, Timer
from data.subject import Subject
from data.connectivity_matrix import ConnectivityMatrix

# Setup logger
logger = setup_logger(__name__)

def load_behavioral_data() -> pd.DataFrame:
    """
    Load behavioral data (Improvement, Age, Sex) from processed data.
    
    Returns:
        pd.DataFrame: DataFrame with columns ['subject_id', 'improvement', 'age', 'sex']
    """
    config = get_config()
    output_paths = get_output_paths()
    behavioral_path = output_paths.behavioral_dir / "behavioral_metrics.csv"
    
    if not behavioral_path.exists():
        raise FileNotFoundError(f"Behavioral data not found at {behavioral_path}")
    
    df = pd.read_csv(behavioral_path)
    required_cols = ['subject_id', 'improvement', 'age', 'sex']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Behavioral data missing required columns: {missing_cols}")
    
    logger.info(f"Loaded behavioral data for {len(df)} subjects")
    return df

def load_centrality_or_pca_data() -> pd.DataFrame:
    """
    Load either Global_Centrality or PCA components based on VIF analysis.
    
    Returns:
        pd.DataFrame: DataFrame with subject_id and predictor column(s)
    """
    config = get_config()
    output_paths = get_output_paths()
    predictor_path = output_paths.centrality_dir / "model_predictors.csv"
    
    if not predictor_path.exists():
        raise FileNotFoundError(f"Model predictors not found at {predictor_path}")
    
    df = pd.read_csv(predictor_path)
    required_cols = ['subject_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Predictor data missing required columns: {missing_cols}")
    
    logger.info(f"Loaded predictor data for {len(df)} subjects")
    return df

def load_mean_fd_data() -> pd.DataFrame:
    """
    Load Mean Framewise Displacement data.
    
    Returns:
        pd.DataFrame: DataFrame with columns ['subject_id', 'mean_fd']
    """
    config = get_config()
    output_paths = get_output_paths()
    fd_path = output_paths.behavioral_dir / "fd_mean.csv"
    
    if not fd_path.exists():
        raise FileNotFoundError(f"Mean FD data not found at {fd_path}")
    
    df = pd.read_csv(fd_path)
    required_cols = ['subject_id', 'mean_fd']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Mean FD data missing required columns: {missing_cols}")
    
    logger.info(f"Loaded Mean FD data for {len(df)} subjects")
    return df

def merge_all_data(
    behavioral_df: pd.DataFrame,
    predictor_df: pd.DataFrame,
    fd_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge all data sources on subject_id.
    
    Args:
        behavioral_df: DataFrame with behavioral metrics
        predictor_df: DataFrame with centrality or PCA predictors
        fd_df: DataFrame with Mean FD values
        
    Returns:
        pd.DataFrame: Merged DataFrame ready for regression
    """
    # Merge behavioral and predictor data
    merged = pd.merge(behavioral_df, predictor_df, on='subject_id', how='inner')
    
    # Merge with FD data
    merged = pd.merge(merged, fd_df, on='subject_id', how='inner')
    
    logger.info(f"Merged dataset contains {len(merged)} subjects")
    
    # Handle Sex column if it exists (ensure it's numeric for regression)
    if 'sex' in merged.columns:
        # Assuming Sex is coded as 0/1 or 'M'/'F'
        if merged['sex'].dtype == 'object':
            merged['sex'] = merged['sex'].map({'M': 0, 'F': 1, 'Male': 0, 'Female': 1})
            logger.info("Mapped sex values to numeric (M=0, F=1)")
    
    return merged

def fit_linear_regression(
    data: pd.DataFrame,
    use_pca: bool = False
) -> Tuple[sm.RegressionResults, str]:
    """
    Fit linear regression model based on available predictors.
    
    Args:
        data: Merged DataFrame with all variables
        use_pca: If True, use PCA component; else use Global_Centrality
        
    Returns:
        Tuple of (RegressionResults object, formula string used)
    """
    # Determine formula based on PCA usage
    if use_pca:
        # Look for PCA component column (usually PCA_Component_1 or similar)
        pca_cols = [col for col in data.columns if col.startswith('PCA_Component')]
        if not pca_cols:
            raise ValueError("PCA component column not found in data but use_pca=True")
        predictor_col = pca_cols[0]
        formula = f"improvement ~ {predictor_col} + age + sex + mean_fd"
        logger.info(f"Fitting model with PCA component: {predictor_col}")
    else:
        if 'Global_Centrality' not in data.columns:
            raise ValueError("Global_Centrality column not found in data but use_pca=False")
        formula = "improvement ~ Global_Centrality + age + sex + mean_fd"
        logger.info("Fitting model with Global_Centrality")
    
    # Fit the model
    model = smf.ols(formula=formula, data=data)
    results = model.fit()
    
    logger.info(f"Model fitted successfully. R² = {results.rsquared:.4f}")
    
    return results, formula

def save_regression_summary(
    results: sm.RegressionResults,
    formula: str,
    output_path: Path
) -> None:
    """
    Save regression summary to CSV.
    
    Args:
        results: RegressionResults object from statsmodels
        formula: Formula string used for the model
        output_path: Path to save the summary CSV
    """
    # Create summary DataFrame
    summary_data = {
        'parameter': results.params.index,
        'coefficient': results.params.values,
        'std_error': results.bse.values,
        't_statistic': results.tvalues.values,
        'p_value': results.pvalues.values,
        'confidence_interval_lower': results.conf_int()[0].values,
        'confidence_interval_upper': results.conf_int()[1].values
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_df['formula'] = formula
    summary_df['r_squared'] = results.rsquared
    summary_df['adjusted_r_squared'] = results.rsquared_adj
    summary_df['f_statistic'] = results.fvalue
    summary_df['f_p_value'] = results.f_pvalue
    summary_df['n_observations'] = results.nobs
    summary_df['aic'] = results.aic
    summary_df['bic'] = results.bic
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Regression summary saved to {output_path}")

def run_regression_analysis() -> Dict[str, any]:
    """
    Main function to run the complete regression analysis pipeline.
    
    Returns:
        Dictionary containing model results and metadata
    """
    with Timer("Regression Analysis"):
        logger.info("Starting regression analysis")
        
        # Load all data sources
        try:
            behavioral_df = load_behavioral_data()
            predictor_df = load_centrality_or_pca_data()
            fd_df = load_mean_fd_data()
        except FileNotFoundError as e:
            logger.error(f"Data loading failed: {e}")
            raise
        
        # Merge data
        merged_data = merge_all_data(behavioral_df, predictor_df, fd_df)
        
        # Check if PCA was used (based on column names in predictor_df)
        use_pca = any(col.startswith('PCA_Component') for col in predictor_df.columns)
        
        # Fit model
        results, formula = fit_linear_regression(merged_data, use_pca=use_pca)
        
        # Save summary
        config = get_config()
        output_paths = get_output_paths()
        summary_path = output_paths.regression_dir / "linear_model_summary.csv"
        save_regression_summary(results, formula, summary_path)
        
        # Prepare return dictionary
        result_dict = {
            'formula': formula,
            'r_squared': float(results.rsquared),
            'adjusted_r_squared': float(results.rsquared_adj),
            'f_statistic': float(results.fvalue),
            'f_p_value': float(results.f_pvalue),
            'n_observations': int(results.nobs),
            'coefficients': results.params.to_dict(),
            'p_values': results.pvalues.to_dict(),
            'summary_path': str(summary_path)
        }
        
        logger.info(f"Regression analysis completed. Results saved to {summary_path}")
        return result_dict

def main():
    """Entry point for running regression analysis."""
    try:
        result = run_regression_analysis()
        logger.info("Regression analysis completed successfully")
        print(f"Analysis complete. Summary saved to: {result['summary_path']}")
        return 0
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
