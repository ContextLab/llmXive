import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import GradientBoostingRegressor
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_descriptors(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load descriptors from the processed CSV file."""
    if filepath is None:
        filepath = str(PROJECT_ROOT / "data" / "processed" / "descriptors.csv")
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {path}")
    logger.info(f"Loading descriptors from {path}")
    return pd.read_csv(path)

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Pearson correlation matrix for numeric columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    logger.info(f"Calculating correlation matrix for columns: {list(numeric_cols)}")
    corr_matrix = df[numeric_cols].corr(method='pearson')
    return corr_matrix

def calculate_p_values(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate p-values for Pearson correlations."""
    from scipy import stats
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    p_values = pd.DataFrame(np.zeros((len(numeric_cols), len(numeric_cols))),
                            index=numeric_cols, columns=numeric_cols)
    
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i != j:
                corr, p_val = stats.pearsonr(df[col1], df[col2])
                p_values.loc[col1, col2] = p_val
            elif i == j:
                p_values.loc[col1, col2] = 0.0 # Perfect correlation, p=0
    
    return p_values

def benjamini_hochberg_fdr(p_values: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    from scipy.stats import fdr_bh
    flat_p = p_values.values.flatten()
    # Filter out zeros or inf if any (though we set diagonal to 0.0)
    # fdr_bh expects 1D array. We need to map back.
    # Note: fdr_bh returns (rejections, q_values). We want q_values (adjusted p-values).
    # Actually, scipy.stats.fdr_bh returns (rejections, q_values).
    # Let's use a manual implementation for clarity on the matrix structure.
    
    # Flatten and get indices
    flat_p = p_values.values.flatten()
    indices = np.arange(len(flat_p))
    
    # Sort p-values
    sorted_indices = np.argsort(flat_p)
    sorted_p = flat_p[sorted_indices]
    
    # Calculate q-values
    n = len(sorted_p)
    q_values = np.zeros(n)
    for i in range(n):
        q_values[i] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i+1])
    
    # Cap at 1.0
    q_values = np.clip(q_values, 0.0, 1.0)
    
    # Reshape back to matrix
    adjusted_p = q_values.reshape(p_values.shape)
    
    # Map back to original indices
    final_p_values = np.zeros_like(adjusted_p)
    flat_indices = indices.reshape(p_values.shape)
    for i in range(n):
        orig_idx = sorted_indices[i]
        r, c = np.unravel_index(orig_idx, p_values.shape)
        final_p_values[r, c] = q_values[i]
        
    return pd.DataFrame(final_p_values, index=p_values.index, columns=p_values.columns)

def save_correlation_matrix(corr_matrix: pd.DataFrame, filepath: Optional[str] = None):
    """Save correlation matrix to CSV."""
    if filepath is None:
        filepath = str(PROJECT_ROOT / "data" / "processed" / "correlation_matrix.csv")
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    corr_matrix.to_csv(path)
    logger.info(f"Saved correlation matrix to {path}")

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor (VIF) for predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    # Select only numeric columns, excluding target if present
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    # Assume target is 'Tg' or similar, exclude it if it's in the numeric cols
    # For VIF, we usually look at predictors. Let's assume the last column is target or named 'Tg'
    # Better: rely on the fact that descriptors.csv has specific columns.
    # We will calculate VIF for all numeric columns except 'Tg' if it exists.
    if 'Tg' in numeric_cols:
        predictors = numeric_cols.drop('Tg')
    else:
        predictors = numeric_cols
        
    X = df[predictors]
    vif_data = pd.DataFrame()
    vif_data["Feature"] = predictors
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(predictors))]
    return vif_data

def save_vif_diagnostic_log(vif_data: pd.DataFrame, filepath: Optional[str] = None):
    """Save VIF diagnostic log to JSON."""
    if filepath is None:
        filepath = str(PROJECT_ROOT / "data" / "processed" / "vif_diagnostic_log.json")
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to list of dicts for JSON
    data = vif_data.to_dict(orient='records')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved VIF diagnostic log to {path}")

def bootstrap_feature_importance(model_path: str, X: pd.DataFrame, y: pd.Series, 
                                 n_resamples: int = 1000, random_state: int = 42) -> Dict[str, Any]:
    """
    Perform bootstrapping to calculate 95% CI for feature importance.
    
    Args:
        model_path: Path to the saved best model (pkl).
        X: Feature dataframe.
        y: Target series.
        n_resamples: Number of bootstrap resamples.
        random_state: Random seed.
        
    Returns:
        Dictionary containing mean importance, 95% CI (lower, upper), and std dev.
    """
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    if not hasattr(model, 'feature_importances_'):
        raise ValueError("Loaded model does not have feature_importances_ attribute.")
    
    features = X.columns
    importance_means = np.zeros((n_resamples, len(features)))
    
    rng = np.random.default_rng(random_state)
    
    logger.info(f"Starting bootstrapping with {n_resamples} resamples...")
    start_time = time.time()
    
    for i in range(n_resamples):
        # Resample with replacement
        indices = rng.choice(len(X), size=len(X), replace=True)
        X_boot = X.iloc[indices]
        y_boot = y.iloc[indices]
        
        # Train a new model on the resampled data
        # We assume the model type is GradientBoostingRegressor based on T024
        # We need to use the same hyperparameters as the best model.
        # Since we don't have the exact hyperparams here, we assume the loaded model's params
        # OR we re-train a fresh one with default/standard params if we can't extract them easily.
        # Better approach: Extract params from the loaded model if possible, or re-train a generic one.
        # However, the task says "Input: artifacts/models/best_model.pkl". 
        # To get the CI for *that* model's importance, we usually re-train on resampled data 
        # using the *same* hyperparameters.
        
        # Let's try to get params from the loaded model
        try:
            params = model.get_params()
            # Remove random_state to ensure we can set it for reproducibility if needed, 
            # but here we are resampling data, so model randomness is less critical if we fix data.
            # Actually, we should set random_state for the model to ensure consistency.
            params['random_state'] = random_state + i # Vary seed slightly or keep same
            new_model = GradientBoostingRegressor(**params)
        except:
            # Fallback to default if get_params fails (unlikely)
            new_model = GradientBoostingRegressor(random_state=random_state + i)
            
        new_model.fit(X_boot, y_boot)
        importance_means[i] = new_model.feature_importances_
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_resamples} resamples")
    
    elapsed = time.time() - start_time
    logger.info(f"Bootstrapping completed in {elapsed:.2f} seconds")
    
    # Calculate statistics
    mean_importance = np.mean(importance_means, axis=0)
    std_importance = np.std(importance_means, axis=0)
    lower_ci = np.percentile(importance_means, 2.5, axis=0)
    upper_ci = np.percentile(importance_means, 97.5, axis=0)
    
    results = {
        "features": list(features),
        "mean_importance": mean_importance.tolist(),
        "std_importance": std_importance.tolist(),
        "ci_95_lower": lower_ci.tolist(),
        "ci_95_upper": upper_ci.tolist(),
        "n_resamples": n_resamples,
        "random_state": random_state,
        "runtime_seconds": elapsed
    }
    
    return results

def save_stability_metrics(metrics: Dict[str, Any], filepath: Optional[str] = None):
    """Save stability metrics to JSON."""
    if filepath is None:
        filepath = str(PROJECT_ROOT / "artifacts" / "metrics" / "stability_metrics.json")
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved stability metrics to {path}")

def main():
    """Main entry point for analysis tasks."""
    logger.info("Starting analyze.py main execution")
    
    # 1. Load Descriptors
    try:
        df = load_descriptors()
    except FileNotFoundError as e:
        logger.error(f"Failed to load descriptors: {e}")
        sys.exit(1)
    
    # 2. Calculate Correlation Matrix
    corr_matrix = calculate_correlation_matrix(df)
    save_correlation_matrix(corr_matrix)
    
    # 3. Calculate P-values
    p_values = calculate_p_values(df)
    
    # 4. FDR Correction
    fdr_corrected = benjamini_hochberg_fdr(p_values)
    # Save FDR corrected p-values? The task T034 says save correlation matrix, 
    # but T034 implies the correction is part of the process. 
    # We'll save the FDR matrix if needed, but the task T036 is about stability.
    # Let's just ensure the logic is there.
    
    # 5. VIF Calculation
    vif_data = calculate_vif(df)
    save_vif_diagnostic_log(vif_data)
    
    # 6. Bootstrap Feature Importance (T036)
    model_path = str(PROJECT_ROOT / "artifacts" / "models" / "best_model.pkl")
    if not Path(model_path).exists():
        logger.error(f"Model file not found at {model_path}. Cannot perform bootstrapping.")
        sys.exit(1)
    
    # Prepare X and y
    # Assume 'Tg' is the target column in descriptors.csv
    if 'Tg' not in df.columns:
        logger.error("Target column 'Tg' not found in descriptors dataframe.")
        sys.exit(1)
        
    X = df.drop(columns=['Tg'])
    y = df['Tg']
    
    stability_results = bootstrap_feature_importance(
        model_path=model_path,
        X=X,
        y=y,
        n_resamples=1000,
        random_state=42
    )
    
    save_stability_metrics(stability_results)
    
    logger.info("Analysis completed successfully.")

if __name__ == "__main__":
    main()