import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root, get_data_path, get_figures_path

logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """Load the processed analysis data from disk."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "analysis_data.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Analysis data not found at {file_path}. Run descriptors.py and analysis pipeline first.")
    return pd.read_csv(file_path)

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    Args:
        X: DataFrame of predictors (features).
    
    Returns:
        Series of VIF values indexed by column name.
    """
    vif_data = {}
    for i, col in enumerate(X.columns):
        # Create a temporary dataframe with the current column as target and others as predictors
        y_temp = X[col]
        X_temp = X.drop(columns=[col])
        
        # Fit a simple linear regression to get R^2
        model = LinearRegression()
        model.fit(X_temp, y_temp)
        r2 = model.score(X_temp, y_temp)
        
        # VIF = 1 / (1 - R^2)
        if r2 == 1.0:
            vif_data[col] = np.inf
        else:
            vif_data[col] = 1.0 / (1.0 - r2)
    
    return pd.Series(vif_data)

def build_multivariate_model(
    data: pd.DataFrame,
    predictors: List[str],
    target: str = 'logPapp',
    vif_threshold: float = 5.0
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Build a multivariate linear regression model with collinearity handling.
    
    Args:
        data: DataFrame containing predictors and target.
        predictors: List of predictor column names.
        target: Target column name.
        vif_threshold: Threshold for VIF to trigger Ridge regression.
    
    Returns:
        Tuple of (model_results_dict, diagnostics_df).
    """
    # Prepare data
    X = data[predictors].dropna()
    y = data.loc[X.index, target]
    
    if len(X) == 0:
        raise ValueError("No valid data points after dropping NaNs.")
    
    # Calculate VIF
    vif_series = calculate_vif(X)
    logger.info(f"VIF values: {vif_series.to_dict()}")
    
    diagnostics = pd.DataFrame({
        'feature': vif_series.index,
        'vif': vif_series.values
    })
    
    # Check for collinearity
    high_vif_features = vif_series[vif_series > vif_threshold].index.tolist()
    
    if high_vif_features:
        logger.warning(f"Collinearity detected (VIF > {vif_threshold}) for: {high_vif_features}. Falling back to Ridge Regression.")
        # Use Ridge regression to handle collinearity
        model = Ridge(alpha=1.0) # alpha=1.0 is a standard starting point
        model.fit(X, y)
        model_type = "Ridge"
    else:
        model = LinearRegression()
        model.fit(X, y)
        model_type = "Linear Regression"
    
    # Calculate metrics
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    
    # Get coefficients
    if hasattr(model, 'coef_'):
        coefficients = dict(zip(predictors, model.coef_))
    else:
        coefficients = {}
    
    if hasattr(model, 'intercept_'):
        intercept = model.intercept_
    else:
        intercept = 0.0
    
    results = {
        'model_type': model_type,
        'r2': r2,
        'rmse': rmse,
        'mae': mae,
        'coefficients': coefficients,
        'intercept': intercept,
        'high_vif_features': high_vif_features,
        'vif_threshold': vif_threshold
    }
    
    return results, diagnostics

def write_regression_results(results: Dict[str, Any], output_path: Path):
    """Write regression results to a text file."""
    with open(output_path, 'w') as f:
        f.write("=== Multivariate Regression Results ===\n\n")
        f.write(f"Model Type: {results['model_type']}\n")
        f.write(f"R^2: {results['r2']:.4f}\n")
        f.write(f"RMSE: {results['rmse']:.4f}\n")
        f.write(f"MAE: {results['mae']:.4f}\n\n")
        
        f.write("Coefficients:\n")
        for feat, coef in results['coefficients'].items():
            f.write(f"  {feat}: {coef:.4f}\n")
        
        f.write(f"Intercept: {results['intercept']:.4f}\n\n")
        
        if results['high_vif_features']:
            f.write(f"Collinearity Warning: VIF > {results['vif_threshold']} detected for: {results['high_vif_features']}\n")
            f.write("Fell back to Ridge Regression to handle collinearity.\n")
        else:
            f.write("No significant collinearity detected (VIF <= 5.0).\n")
    
    logger.info(f"Regression results written to {output_path}")

def run_scaffold_cross_validation(
    data: pd.DataFrame,
    predictors: List[str],
    target: str = 'logPapp',
    n_splits: int = 5
) -> Dict[str, float]:
    """
    Perform scaffold-based cross-validation.
    
    Note: For this implementation, we use a simple K-fold approach as a proxy
    since a real scaffold split requires a 'scaffold' column which may not be present.
    If a 'scaffold' column exists, it would be used for grouping.
    
    Args:
        data: DataFrame with predictors, target, and optionally 'scaffold'.
        predictors: List of predictor column names.
        target: Target column name.
        n_splits: Number of folds.
    
    Returns:
        Dictionary with mean R2, RMSE, and MAE.
    """
    X = data[predictors].dropna()
    y = data.loc[X.index, target]
    
    if 'scaffold' in data.columns:
        # Use scaffold as groups for LeaveOneGroupOut or similar
        # Here we approximate with KFold on scaffold groups if available
        # For simplicity in this generic implementation, we stick to KFold
        # but note that true scaffold splitting requires specific logic.
        groups = data.loc[X.index, 'scaffold']
        # If groups are too few, fall back to random split
        if groups.nunique() < n_splits:
            logger.warning("Not enough unique scaffolds for split. Using random KFold.")
            groups = None
    else:
        groups = None
    
    if groups is None:
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    else:
        # Use GroupKFold if groups are valid
        from sklearn.model_selection import GroupKFold
        cv = GroupKFold(n_splits=n_splits)
    
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for train_idx, test_idx in cv.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2_scores.append(r2_score(y_test, y_pred))
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae_scores.append(mean_absolute_error(y_test, y_pred))
    
    return {
        'mean_r2': np.mean(r2_scores),
        'mean_rmse': np.mean(rmse_scores),
        'mean_mae': np.mean(mae_scores),
        'std_r2': np.std(r2_scores)
    }

def main():
    """Entry point for the analysis module."""
    setup_logging_for_script(__name__)
    logger.info("Starting analysis module.")
    
    try:
        # Load data
        data = load_analysis_data()
        logger.info(f"Loaded {len(data)} records for analysis.")
        
        # Define predictors (flexibility descriptors)
        predictors = ['bond_variance', 'angle_variance', 'dihedral_variance']
        target = 'logPapp'
        
        # Check if all predictors are present
        missing = [p for p in predictors if p not in data.columns]
        if missing:
            logger.error(f"Missing predictors: {missing}. Cannot run analysis.")
            sys.exit(1)
        
        # Run VIF and build model
        results, diagnostics = build_multivariate_model(data, predictors, target)
        
        # Write results
        output_path = get_data_path() / "processed" / "regression_results.txt"
        write_regression_results(results, output_path)
        
        # Run cross-validation
        cv_results = run_scaffold_cross_validation(data, predictors, target)
        logger.info(f"Cross-validation results: {cv_results}")
        
        # Print summary
        print(f"\n=== Analysis Summary ===")
        print(f"Model Type: {results['model_type']}")
        print(f"R^2: {results['r2']:.4f}")
        print(f"CV Mean R^2: {cv_results['mean_r2']:.4f} (+/- {cv_results['std_r2']:.4f})")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during analysis.")
        sys.exit(1)

if __name__ == "__main__":
    main()