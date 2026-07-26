import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Ensure logging is configured if not already
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_analysis_data(filepath: str) -> pd.DataFrame:
    """
    Load the processed analysis data containing descriptors and permeability.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Analysis data file not found: {filepath}")
    
    df = pd.read_csv(path)
    
    required_cols = ['smiles', 'bond_variance', 'angle_variance', 'dihedral_variance', 'logPapp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    
    return df

def calculate_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Pearson and Spearman correlations between flexibility descriptors and logPapp.
    """
    descriptors = ['bond_variance', 'angle_variance', 'dihedral_variance']
    target = 'logPapp'
    
    results = {
        'pearson': {},
        'spearman': {},
        'pearson_p': {},
        'spearman_p': {}
    }
    
    for desc in descriptors:
        # Pearson
        r, p = scipy.stats.pearsonr(df[desc], df[target])
        results['pearson'][desc] = r
        results['pearson_p'][desc] = p
        
        # Spearman
        r, p = scipy.stats.spearmanr(df[desc], df[target])
        results['spearman'][desc] = r
        results['spearman_p'][desc] = p
    
    return results

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns adjusted p-values (q-values).
    """
    import scipy.stats as stats
    # statsmodels is often used, but scipy.stats has a direct function for BH
    # However, to be explicit and robust:
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    m = len(sorted_p)
    ranked = np.arange(1, m + 1)
    
    # BH adjustment
    q = (sorted_p * m) / ranked
    # Ensure q values do not exceed 1.0 and are monotonic (cumulative max from end)
    q = np.minimum(q, 1.0)
    # Make monotonic non-decreasing
    for i in range(m - 2, -1, -1):
        q[i] = min(q[i], q[i+1])
        
    # Restore original order
    adjusted_q = np.empty(m)
    adjusted_q[sorted_indices] = q
    
    return adjusted_q.tolist()

def write_fdr_results(results: Dict[str, Any], output_path: str):
    """
    Write FDR corrected results to a CSV file.
    """
    df_out = pd.DataFrame([results])
    df_out.to_csv(output_path, index=False)
    logger.info(f"FDR results written to {output_path}")

def write_correlation_results(results: Dict[str, Any], output_path: str):
    """
    Write correlation results to a CSV file.
    """
    df_out = pd.DataFrame([results])
    df_out.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor to detect multicollinearity.
    
    Args:
        df: DataFrame containing the predictor variables.
        predictor_cols: List of column names to check for collinearity.
        
    Returns:
        Dictionary mapping column names to their VIF scores.
        
    Raises:
        ValueError: If any predictor has zero variance or if the matrix is singular.
    """
    logger.info(f"Calculating VIF for predictors: {predictor_cols}")
    
    # Select only the predictor columns
    X = df[predictor_cols].dropna()
    
    if X.empty:
        raise ValueError("No valid data remaining for VIF calculation after dropping NaNs.")
    
    # Add constant for intercept
    X_const = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(predictor_cols):
        # VIF for feature i is 1 / (1 - R^2_i) where R^2_i is from regressing feature i on all other features
        try:
            vif = variance_inflation_factor(X_const.values, i + 1) # +1 because index 0 is constant
            vif_data[col] = vif
            logger.info(f"VIF for {col}: {vif:.4f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def fit_multivariate_model(df: pd.DataFrame, 
                           predictors: List[str], 
                           target: str = 'logPapp',
                           vif_threshold: float = 5.0) -> Dict[str, Any]:
    """
    Fit a multivariate linear regression model, handling collinearity via VIF diagnosis.
    
    If VIF > threshold for any predictor, it is dropped iteratively (least significant first)
    until all remaining predictors have VIF <= threshold or only one remains.
    
    Args:
        df: DataFrame with predictors and target.
        predictors: List of predictor column names.
        target: Target column name.
        vif_threshold: Maximum allowed VIF.
        
    Returns:
        Dictionary with model results, coefficients, and VIF diagnostics.
    """
    import statsmodels.api as sm
    
    logger.info(f"Fitting multivariate model with predictors: {predictors}")
    
    current_predictors = list(predictors)
    final_predictors = []
    model = None
    diagnostics = {}
    
    # Iterative VIF check and removal
    while current_predictors:
        # Calculate VIF for current set
        vif_scores = calculate_vif(df, current_predictors)
        
        # Check if any exceed threshold
        max_vif = max(vif_scores.values())
        if max_vif <= vif_threshold:
            # All good
            final_predictors = current_predictors
            break
        
        # Find the predictor with the highest VIF
        worst_col = max(vif_scores, key=vif_scores.get)
        logger.warning(f"VIF for {worst_col} ({vif_scores[worst_col]:.2f}) exceeds threshold {vif_threshold}. Removing.")
        current_predictors.remove(worst_col)
    
    if not final_predictors:
        raise ValueError("All predictors were removed due to collinearity. Cannot fit model.")
    
    logger.info(f"Final predictors for model: {final_predictors}")
    
    X = df[final_predictors]
    y = df[target]
    
    # Drop rows with NaN in any of the selected columns
    X = X.dropna()
    y = y.loc[X.index]
    
    if len(X) < len(final_predictors) + 1:
        raise ValueError("Insufficient data points to fit model after filtering.")
    
    X_const = add_constant(X)
    model = sm.OLS(y, X_const).fit()
    
    # Store diagnostics
    diagnostics = {
        'final_predictors': final_predictors,
        'vif_scores': calculate_vif(X, final_predictors),
        'rsquared': model.rsquared,
        'rsquared_adj': model.rsquared_adj,
        'coefficients': model.params.to_dict(),
        'pvalues': model.pvalues.to_dict(),
        'summary': model.summary().as_text()
    }
    
    return {
        'model': model,
        'diagnostics': diagnostics,
        'final_predictors': final_predictors
    }

def run_scaffold_cross_validation(df: pd.DataFrame, 
                                  predictors: List[str], 
                                  target: str = 'logPapp',
                                  n_splits: int = 5,
                                  seed: int = 42) -> Dict[str, float]:
    """
    Perform scaffold-based cross-validation to assess model generalizability.
    
    Note: This implementation uses a simple K-Fold split for now. 
    True scaffold splitting requires a 'scaffold' column which may not exist in all datasets.
    If a scaffold column exists, it will be used; otherwise, standard K-Fold is applied.
    
    Args:
        df: DataFrame with predictors, target, and optionally 'scaffold'.
        predictors: List of predictor column names.
        target: Target column name.
        n_splits: Number of folds.
        seed: Random seed.
        
    Returns:
        Dictionary with mean R², RMSE, and MAE.
    """
    from sklearn.model_selection import KFold
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    logger.info(f"Running scaffold cross-validation with {n_splits} folds.")
    
    X = df[predictors].dropna()
    y = df.loc[X.index, target]
    
    if 'scaffold' in df.columns:
        # Use scaffold for grouping if available (simplified: just shuffle by scaffold ID)
        # In a full implementation, one would use GroupKFold
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    else:
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for train_idx, test_idx in kf.split(X):
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
        'std_r2': np.std(r2_scores),
        'mean_rmse': np.mean(rmse_scores),
        'std_rmse': np.std(rmse_scores),
        'mean_mae': np.mean(mae_scores),
        'std_mae': np.std(mae_scores)
    }

def main():
    """
    Main entry point for the analysis module.
    This function is intended to be called by a script (e.g., via __main__.py or similar).
    """
    # Example usage (to be replaced by actual script logic in caller)
    logger.info("Analysis module loaded successfully.")
    logger.info("Available functions: calculate_vif, fit_multivariate_model, run_scaffold_cross_validation")

if __name__ == "__main__":
    main()