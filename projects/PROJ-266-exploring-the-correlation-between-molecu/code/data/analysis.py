import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error

from utils.config import get_project_root, set_seed
from utils.logging import get_logger, configure_root_logger

logger = get_logger(__name__)

# --- Data Loading ---

def load_analysis_data(processed_data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed dataset containing descriptors and permeability data.
    
    Args:
        processed_data_path: Path to the processed CSV file. Defaults to 
                             data/processed/descriptors.csv if not provided.
    
    Returns:
        DataFrame with SMILES, descriptors, and logPapp.
    """
    if processed_data_path is None:
        root = get_project_root()
        processed_data_path = root / "data" / "processed" / "descriptors.csv"
    
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {processed_data_path}")
    
    logger.info(f"Loading analysis data from {processed_data_path}")
    df = pd.read_csv(processed_data_path)
    
    required_cols = ['smiles', 'logPapp', 'dihedral_variance', 'bond_variance', 'angle_variance']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")
    
    # Drop rows with NaN in critical columns for regression
    initial_count = len(df)
    df = df.dropna(subset=['logPapp', 'dihedral_variance', 'bond_variance', 'angle_variance'])
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with NaN values in critical columns.")
    
    logger.info(f"Loaded {len(df)} records for analysis.")
    return df

# --- Correlation Analysis ---

def compute_correlations(df: pd.DataFrame, target_col: str = 'logPapp') -> Dict[str, Dict[str, float]]:
    """
    Compute Pearson and Spearman correlations between descriptors and target.
    
    Args:
        df: DataFrame with descriptors and target.
        target_col: Name of the target column (default: logPapp).
    
    Returns:
        Dictionary of correlation results with coefficients and p-values.
    """
    results = {}
    predictors = ['dihedral_variance', 'bond_variance', 'angle_variance']
    
    logger.info("Computing correlations...")
    for pred in predictors:
        if pred not in df.columns:
            logger.warning(f"Predictor {pred} not found in data, skipping.")
            continue
        
        # Remove NaN pairs
        valid_data = df[[pred, target_col]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Not enough data for {pred}, skipping.")
            continue
        
        x = valid_data[pred].values
        y = valid_data[target_col].values
        
        pearson_r, pearson_p = stats.pearsonr(x, y)
        spearman_r, spearman_p = stats.spearmanr(x, y)
        
        results[pred] = {
            'pearson_r': pearson_r,
            'pearson_p': pearson_p,
            'spearman_r': spearman_r,
            'spearman_p': spearman_p
        }
        logger.info(f"{pred}: Pearson r={pearson_r:.4f} (p={pearson_p:.4f}), Spearman r={spearman_r:.4f} (p={spearman_p:.4f})")
    
    return results

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (default: 0.05).
    
    Returns:
        List of booleans indicating which hypotheses are rejected (True = significant).
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BH thresholds
    thresholds = np.arange(1, n + 1) * alpha / n
    
    # Find the largest k such that p_(k) <= threshold_(k)
    # We iterate backwards to find the first one that satisfies the condition
    rejected_mask = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= thresholds[i]:
            # All p-values up to this index (in sorted order) are rejected
            rejected_mask[sorted_indices[:i+1]] = True
            break
    
    return rejected_mask.tolist()

def write_correlation_results(results: Dict[str, Dict[str, float]], output_path: Path):
    """
    Write correlation results to a CSV file.
    
    Args:
        results: Dictionary of correlation results.
        output_path: Path to the output CSV file.
    """
    rows = []
    for pred, metrics in results.items():
        rows.append({
            'predictor': pred,
            'pearson_r': metrics['pearson_r'],
            'pearson_p': metrics['pearson_p'],
            'spearman_r': metrics['spearman_r'],
            'spearman_p': metrics['spearman_p']
        })
    
    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

# --- VIF and Collinearity Handling ---

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    Args:
        df: DataFrame containing predictors.
        predictors: List of predictor column names.
    
    Returns:
        Dictionary mapping predictor names to their VIF values.
    """
    vif_results = {}
    X = df[predictors].values
    
    if X.shape[0] <= X.shape[1]:
        logger.warning("Not enough samples to calculate VIF reliably.")
        return {p: float('inf') for p in predictors}
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    for i, col in enumerate(predictors):
        # Regress predictor i against all other predictors
        y = X_const[:, i]
        X_other = np.delete(X_const, i, axis=1)
        
        # Simple OLS to get R^2
        # Note: Using numpy for simplicity to avoid full statsmodels dependency if not needed
        # But since we import stats, let's use a simple linear algebra approach
        # R^2 = 1 - (SS_res / SS_tot)
        # y = X_other * beta
        
        try:
            # Solve least squares
            beta, _, _, _ = np.linalg.lstsq(X_other, y, rcond=None)
            y_pred = X_other @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                r2 = 0
            else:
                r2 = 1 - (ss_res / ss_tot)
            
            vif = 1 / (1 - r2) if (1 - r2) > 1e-10 else float('inf')
            vif_results[col] = vif
            logger.debug(f"VIF for {col}: {vif:.4f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = float('inf')
    
    return vif_results

def build_multivariate_model(
    df: pd.DataFrame, 
    target_col: str = 'logPapp',
    primary_pred: str = 'dihedral_variance',
    confounders: List[str] = None,
    vif_threshold: float = 5.0
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Build a multivariate linear regression model with collinearity handling.
    
    If VIF > threshold for any predictor, Ridge regression is used as a fallback.
    
    Args:
        df: DataFrame with predictors and target.
        target_col: Name of the target column.
        primary_pred: Name of the primary predictor.
        confounders: List of confounder names (default: ['logP', 'MW', 'PSA']).
        vif_threshold: VIF threshold above which Ridge regression is used.
    
    Returns:
        Tuple of (model_results_dict, vif_values_dict).
    """
    if confounders is None:
        confounders = ['logP', 'MW', 'PSA']
    
    # Ensure all required columns exist
    all_predictors = [primary_pred] + confounders
    missing = [c for c in all_predictors if c not in df.columns]
    if missing:
        # Log warning and try to proceed with available columns
        logger.warning(f"Missing columns for model: {missing}. Attempting with available columns.")
        all_predictors = [c for c in all_predictors if c in df.columns]
    
    if not all_predictors:
        raise ValueError("No valid predictors available for the model.")
    
    # Prepare data
    X = df[all_predictors].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) < 10:
        raise ValueError(f"Insufficient data for model training after dropping NaNs: {len(X)} rows.")
    
    X = X.values
    y = y.values
    
    # Calculate VIF
    vif_dict = calculate_vif(pd.DataFrame(X, columns=all_predictors), all_predictors)
    
    logger.info(f"VIF values: {vif_dict}")
    
    max_vif = max(vif_dict.values()) if vif_dict else 0
    use_ridge = max_vif > vif_threshold
    
    model_results = {
        'method': 'Ridge' if use_ridge else 'OLS',
        'vif_threshold': vif_threshold,
        'max_vif': max_vif,
        'predictors': all_predictors,
        'coefficients': {},
        'r2': None,
        'mse': None,
        'is_ridge': use_ridge
    }
    
    if use_ridge:
        logger.warning(f"Max VIF ({max_vif:.2f}) exceeds threshold ({vif_threshold}). Using Ridge regression fallback.")
        # Normalize data for Ridge
        X_mean = np.mean(X, axis=0)
        X_std = np.std(X, axis=0)
        X_std[X_std == 0] = 1.0
        X_scaled = (X - X_mean) / X_std
        
        # Use cross-validation to find best alpha
        # For simplicity, we use a standard alpha, but in production, GridSearchCV is better
        # Since we are on CPU only, let's pick a reasonable alpha
        alpha = 1.0
        ridge = Ridge(alpha=alpha)
        ridge.fit(X_scaled, y)
        
        # Coefficients need to be mapped back to original scale for interpretation
        # But for the report, we just report the scaled coefficients and alpha
        model_results['coefficients'] = {
            'intercept': float(ridge.intercept_),
            'scaled_coefficients': {p: float(c) for p, c in zip(all_predictors, ridge.coef_)},
            'alpha': alpha
        }
        model_results['r2'] = float(ridge.score(X_scaled, y))
        model_results['mse'] = float(mean_squared_error(y, ridge.predict(X_scaled)))
        
    else:
        logger.info("VIF values within threshold. Using OLS.")
        ols = LinearRegression()
        ols.fit(X, y)
        
        model_results['coefficients'] = {
            'intercept': float(ols.intercept_),
            'coefficients': {p: float(c) for p, c in zip(all_predictors, ols.coef_)}
        }
        model_results['r2'] = float(ols.score(X, y))
        model_results['mse'] = float(mean_squared_error(y, ols.predict(X)))
    
    return model_results, vif_dict

# --- Scaffold Cross Validation ---

def run_scaffold_cross_validation(
    df: pd.DataFrame,
    target_col: str = 'logPapp',
    primary_pred: str = 'dihedral_variance',
    confounders: List[str] = None,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Perform scaffold-based cross-validation.
    
    Note: This implementation assumes a 'scaffold' column exists or generates
    a proxy scaffold ID based on the Bemis-Murcko scaffold if available.
    For this task, we assume the data has a 'scaffold' column or we use
    a simple clustering proxy if not.
    
    Args:
        df: DataFrame with predictors, target, and scaffold info.
        target_col: Target column name.
        primary_pred: Primary predictor name.
        confounders: List of confounder names.
        n_splits: Number of CV splits.
        random_state: Random seed.
    
    Returns:
        Dictionary of CV metrics (mean_r2, std_r2, etc.).
    """
    if confounders is None:
        confounders = ['logP', 'MW', 'PSA']
    
    # Check for scaffold column
    if 'scaffold' not in df.columns:
        logger.warning("'scaffold' column not found. Using random split as proxy.")
        # Fallback: use random split if scaffold not available
        # In a real scenario, we would compute Bemis-Murcko scaffolds here
        groups = np.random.RandomState(random_state).choice(n_splits, size=len(df))
    else:
        # Convert scaffold strings to integer groups
        scaffold_map = {s: i for i, s in enumerate(df['scaffold'].unique())}
        groups = df['scaffold'].map(scaffold_map).values
    
    # Prepare features
    all_preds = [primary_pred] + (confounders if confounders else [])
    available_preds = [p for p in all_preds if p in df.columns]
    
    if len(available_preds) == 0:
        raise ValueError("No predictors available for cross-validation.")
    
    X = df[available_preds].values
    y = df[target_col].values
    
    # Remove NaNs
    valid_mask = ~np.any(np.isnan(X), axis=1) & ~np.isnan(y)
    X = X[valid_mask]
    y = y[valid_mask]
    groups = groups[valid_mask]
    
    if len(X) < n_splits:
        logger.warning(f"Data too small for {n_splits} splits. Reducing splits.")
        n_splits = max(2, len(X) // 5)
    
    gkf = GroupKFold(n_splits=n_splits)
    
    r2_scores = []
    mse_scores = []
    
    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Simple OLS for CV
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2_scores.append(r2_score(y_test, y_pred))
        mse_scores.append(mean_squared_error(y_test, y_pred))
        
        logger.debug(f"Fold {fold+1}: R2={r2_scores[-1]:.4f}, MSE={mse_scores[-1]:.4f}")
    
    return {
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'mean_mse': float(np.mean(mse_scores)),
        'std_mse': float(np.std(mse_scores)),
        'n_splits': n_splits,
        'n_folds_completed': len(r2_scores)
    }

# --- Main Entry Point ---

def main():
    """
    Main function to run the full analysis pipeline including VIF check and Ridge fallback.
    """
    configure_root_logger()
    root = get_project_root()
    
    # Paths
    data_path = root / "data" / "processed" / "descriptors.csv"
    corr_output_path = root / "data" / "processed" / "correlations.csv"
    model_output_path = root / "data" / "processed" / "model_results.json"
    
    try:
        # 1. Load Data
        df = load_analysis_data(data_path)
        
        # 2. Compute Correlations
        corr_results = compute_correlations(df)
        write_correlation_results(corr_results, corr_output_path)
        
        # 3. Apply FDR (Example on p-values)
        p_values = [corr_results[p]['pearson_p'] for p in corr_results if 'pearson_p' in corr_results[p]]
        if p_values:
            significant = apply_benjamini_hochberg(p_values)
            logger.info(f"FDR Significant predictors: {[list(corr_results.keys())[i] for i, sig in enumerate(significant) if sig]}")
        
        # 4. Build Model with VIF check and Ridge fallback
        # Note: This assumes 'logP', 'MW', 'PSA' are available in the data.
        # If they are not, the function will handle it gracefully by dropping them.
        model_results, vif_results = build_multivariate_model(
            df,
            target_col='logPapp',
            primary_pred='dihedral_variance',
            confounders=['logP', 'MW', 'PSA'],
            vif_threshold=5.0
        )
        
        # Save model results
        import json
        with open(model_output_path, 'w') as f:
            json.dump(model_results, f, indent=2)
        logger.info(f"Model results saved to {model_output_path}")
        
        # 5. Cross-Validation
        cv_results = run_scaffold_cross_validation(
            df,
            target_col='logPapp',
            primary_pred='dihedral_variance',
            confounders=['logP', 'MW', 'PSA']
        )
        logger.info(f"Cross-validation R2: {cv_results['mean_r2']:.4f} (+/- {cv_results['std_r2']:.4f})")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

# Import sm for VIF calculation (statsmodels)
import statsmodels.api as sm