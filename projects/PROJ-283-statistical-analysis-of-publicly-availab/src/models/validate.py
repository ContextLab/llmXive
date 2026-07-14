import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.tools import add_constant
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SC-003 Threshold constant for model instability
SC_003_THRESHOLD = 0.05

def perform_kfold_cross_validation(
    data: pd.DataFrame,
    target_col: str = 'outcome_deviation',
    feature_cols: Optional[List[str]] = None,
    n_splits: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform K-Fold cross-validation on the dataset using both Gaussian GLM and Ridge Regression.
    
    Calculates R² and MSE for each fold.
    Specifically calculates the standard deviation of R² across folds.
    If std_dev_r2 >= 0.05 (SC-003), raises RuntimeError.
    
    Args:
        data: DataFrame containing features and target
        target_col: Name of the target column
        feature_cols: List of feature column names. If None, all numeric cols except target are used.
        n_splits: Number of K-Fold splits
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing fold metrics, aggregated stats, and model details.
        
    Raises:
        RuntimeError: If SC-003 threshold is exceeded (Model instability detected)
    """
    if feature_cols is None:
        # Select numeric columns excluding target
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c != target_col]
        
    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")
        
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
        
    X = data[feature_cols].values
    y = data[target_col].values
    
    # Handle missing values if any (simple drop for robustness)
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    if len(X) < n_splits:
        raise ValueError(f"Dataset size {len(X)} is too small for {n_splits} splits.")

    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    results = {
        'n_splits': n_splits,
        'fold_metrics': [],
        'model_types': ['Ridge', 'GaussianGLM']
    }
    
    r2_scores = []
    mse_scores = []
    
    # Ridge Regression
    ridge_model = Ridge(alpha=1.0)
    
    # Gaussian GLM
    # Note: statsmodels GLM requires adding constant for intercept
    
    fold_idx = 0
    for train_idx, test_idx in kfold.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        fold_result = {'fold': fold_idx + 1}
        
        # --- Ridge Regression ---
        ridge_model.fit(X_train, y_train)
        ridge_pred = ridge_model.predict(X_test)
        
        # Calculate R² for Ridge
        ss_res_ridge = np.sum((y_test - ridge_pred) ** 2)
        ss_tot_ridge = np.sum((y_test - np.mean(y_test)) ** 2)
        r2_ridge = 1 - (ss_res_ridge / ss_tot_ridge) if ss_tot_ridge != 0 else 0.0
        
        # Calculate MSE for Ridge
        mse_ridge = np.mean((y_test - ridge_pred) ** 2)
        
        fold_result['ridge_r2'] = r2_ridge
        fold_result['ridge_mse'] = mse_ridge
        
        r2_scores.append(r2_ridge)
        mse_scores.append(mse_ridge)
        
        # --- Gaussian GLM ---
        # Add constant for intercept
        X_train_const = add_constant(X_train)
        X_test_const = add_constant(X_test)
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                glm_model = GLM(y_train, X_train_const, family=families.Gaussian())
                glm_results = glm_model.fit()
            
            glm_pred = glm_results.predict(X_test_const)
            
            # Calculate R² for GLM (using pseudo R² or standard R²)
            ss_res_glm = np.sum((y_test - glm_pred) ** 2)
            ss_tot_glm = np.sum((y_test - np.mean(y_test)) ** 2)
            r2_glm = 1 - (ss_res_glm / ss_tot_glm) if ss_tot_glm != 0 else 0.0
            
            # Calculate MSE for GLM
            mse_glm = np.mean((y_test - glm_pred) ** 2)
            
            fold_result['glm_r2'] = r2_glm
            fold_result['glm_mse'] = mse_glm
            
        except Exception as e:
            logger.warning(f"GLM failed on fold {fold_idx + 1}: {e}")
            fold_result['glm_r2'] = None
            fold_result['glm_mse'] = None
        
        results['fold_metrics'].append(fold_result)
        fold_idx += 1
    
    # Aggregate Statistics
    # Calculate standard deviation of R² (using Ridge scores as primary indicator per task context)
    valid_r2 = [r for r in r2_scores if r is not None]
    valid_mse = [m for m in mse_scores if m is not None]
    
    if not valid_r2:
        raise ValueError("No valid R² scores calculated.")
        
    mean_r2 = np.mean(valid_r2)
    std_dev_r2 = np.std(valid_r2)
    mean_mse = np.mean(valid_mse)
    
    results['aggregated'] = {
        'mean_r2': mean_r2,
        'std_dev_r2': std_dev_r2,
        'mean_mse': mean_mse
    }
    
    # SC-003 Check: Model Instability
    if std_dev_r2 >= SC_003_THRESHOLD:
        raise RuntimeError(f"SC-003 Threshold Exceeded: Model instability detected")
        
    logger.info(f"Cross-validation complete. Mean R²: {mean_r2:.4f}, Std Dev R²: {std_dev_r2:.4f}")
    return results

def run_validation_pipeline(
    data_path: str,
    output_path: str,
    target_col: str = 'outcome_deviation',
    feature_cols: Optional[List[str]] = None,
    n_splits: int = 5
) -> Dict[str, Any]:
    """
    Main pipeline to run cross-validation and save results.
    
    Args:
        data_path: Path to input CSV/Parquet file
        output_path: Path to save JSON results
        target_col: Target column name
        feature_cols: Feature columns
        n_splits: Number of folds
        
    Returns:
        Results dictionary
    """
    logger.info(f"Loading data from {data_path}")
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
        
    try:
        results = perform_kfold_cross_validation(
            data=df,
            target_col=target_col,
            feature_cols=feature_cols,
            n_splits=n_splits
        )
        
        # Save results
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Results saved to {output_path}")
        return results
        
    except RuntimeError as e:
        # Re-raise SC-003 errors to halt the pipeline as per requirement
        raise e
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Entry point for script execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run K-Fold Cross-Validation and SC-003 Check")
    parser.add_argument('--data', type=str, required=True, help='Path to input data file (CSV or Parquet)')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--target', type=str, default='outcome_deviation', help='Target column name')
    parser.add_argument('--splits', type=int, default=5, help='Number of folds')
    
    args = parser.parse_args()
    
    try:
        run_validation_pipeline(
            data_path=args.data,
            output_path=args.output,
            target_col=args.target,
            n_splits=args.splits
        )
        print("Validation completed successfully.")
    except RuntimeError as e:
        print(f"Validation Failed: {e}")
        # Exit with error code to signal failure in CI/CD
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()