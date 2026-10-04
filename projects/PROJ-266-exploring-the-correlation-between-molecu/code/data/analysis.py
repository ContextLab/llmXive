import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root, get_data_path, get_figures_path

logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """Load the processed analysis data containing descriptors and logPapp."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "descriptors_raw.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Descriptors data not found at {file_path}. Run descriptors.py first.")
    
    df = pd.read_csv(file_path)
    
    # Ensure we have the confounders if they exist in the source or merge later
    # For this task, we assume the source has them or we load from a merged source if available
    # Based on T019a, we need logP, MW, PSA. 
    # If the current file doesn't have them, we might need to merge with filtered_data
    processed_path = data_path / "processed" / "filtered_data.csv"
    if processed_path.exists():
        merged = pd.merge(df, pd.read_csv(processed_path), on='smiles', how='left')
        # Keep columns needed: descriptors + confounders + logPapp
        needed_cols = ['smiles', 'logPapp', 'bond_variance', 'angle_variance', 'dihedral_variance', 'logP', 'mw', 'psa']
        # Filter to existing columns to avoid KeyError if some are missing
        existing_cols = [c for c in needed_cols if c in merged.columns]
        if len(existing_cols) == len(needed_cols):
            df = merged[needed_cols]
        else:
            logger.warning(f"Missing some confounders in merge. Available: {existing_cols}")
    else:
        logger.warning(f"Filtered data not found at {processed_path}. Confounders might be missing.")
        
    return df

def check_significance(p_value: float, alpha: float = 0.05) -> bool:
    """Check if a p-value is statistically significant."""
    return p_value < alpha

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """Calculate Variance Inflation Factor for each predictor."""
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    vif_data = pd.Series([variance_inflation_factor(X_with_const.values, i) 
                          for i in range(X_with_const.shape[1])], 
                         index=X_with_const.columns)
    return vif_data

def build_multivariate_model(data: pd.DataFrame, 
                             primary_descriptor: str = 'dihedral_variance',
                             confounders: List[str] = None) -> Dict[str, Any]:
    """
    Build a multivariate linear regression model.
    
    Args:
        data: DataFrame with all variables.
        primary_descriptor: The main flexibility metric to test.
        confounders: List of confounder column names (logP, MW, PSA).
    
    Returns:
        Dictionary with model results.
    """
    if confounders is None:
        confounders = ['logP', 'mw', 'psa']
    
    # Check if all required columns exist
    required = [primary_descriptor] + confounders + ['logPapp']
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with NaN
    clean_data = data.dropna(subset=required)
    
    if len(clean_data) < 10:
        raise ValueError(f"Not enough data points after cleaning: {len(clean_data)}")
    
    # Prepare features
    # Per T019a: Include bond/angle ONLY if significant in T015 or for VIF control
    # For simplicity in this implementation, we start with primary + confounders
    # and check VIF.
    features = [primary_descriptor] + confounders
    
    X = clean_data[features]
    y = clean_data['logPapp']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R2
    r2 = model.score(X, y)
    
    # Calculate p-values using OLS from statsmodels for inference
    import statsmodels.api as sm
    X_const = sm.add_constant(X)
    ols_model = sm.OLS(y, X_const).fit()
    
    results = {
        'coefficients': dict(zip(features, model.coef_.tolist())),
        'intercept': float(model.intercept_),
        'r_squared': float(r2),
        'p_values': {col: float(p) for col, p in zip(features, ols_model.pvalues[1:])},
        'vif': calculate_vif(X).to_dict(),
        'n_samples': len(clean_data)
    }
    
    return results

def run_kfold_cross_validation(data: pd.DataFrame, 
                               primary_descriptor: str = 'dihedral_variance',
                               confounders: List[str] = None,
                               k: int = 5) -> Dict[str, float]:
    """
    Run k-fold cross-validation for the multivariate model.
    
    Returns:
        Dictionary with mean R2, RMSE, MAE.
    """
    if confounders is None:
        confounders = ['logP', 'mw', 'psa']
    
    required = [primary_descriptor] + confounders + ['logPapp']
    clean_data = data.dropna(subset=required)
    
    if len(clean_data) < k:
        raise ValueError(f"Not enough data for {k}-fold CV: {len(clean_data)}")
    
    X = clean_data[[primary_descriptor] + confounders]
    y = clean_data['logPapp']
    
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        r2 = model.score(X_test, y_test)
        r2_scores.append(r2)
        
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        rmse_scores.append(rmse)
        
        mae = np.mean(np.abs(y_test - y_pred))
        mae_scores.append(mae)
    
    return {
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores)),
        'mean_mae': float(np.mean(mae_scores)),
        'std_r2': float(np.std(r2_scores))
    }

def main():
    """Entry point for the analysis module."""
    setup_logging_for_script(__name__)
    logger.info("Starting analysis module.")
    
    try:
        # Load data
        data = load_analysis_data()
        logger.info(f"Loaded {len(data)} records for analysis.")
        
        # Build model
        model_results = build_multivariate_model(data)
        logger.info(f"Model R2: {model_results['r_squared']:.4f}")
        
        # Cross-validation
        cv_results = run_kfold_cross_validation(data)
        logger.info(f"CV Mean R2: {cv_results['mean_r2']:.4f}")
        
        # Save results
        output_path = get_data_path() / "processed" / "model_results.json"
        with open(output_path, 'w') as f:
            json.dump({
                'model': model_results,
                'cross_validation': cv_results
            }, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        # Note: T023a requires that plots generated by this module (if any) 
        # or called by it have titles stating "Associational Relationship".
        # This is handled in visualize.py which is the primary plotting module.
        # If analysis.py were to generate plots directly, it would need to 
        # ensure the title includes "Associational Relationship".
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during analysis.")
        sys.exit(1)

if __name__ == "__main__":
    main()