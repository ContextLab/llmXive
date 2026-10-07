import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.utils import resample
from scipy import stats

# Import existing helpers from the same module (as per API surface)
# If these are defined later in the file, ensure they are called after definition.
# If they are in other files, they must be imported there.
# Assuming these exist in this file based on the "existing project API surface" provided:
# get_project_root, setup_logging, load_cleaned_data, load_descriptors, load_model,
# calculate_correlation_matrix, calculate_p_values, benjamini_hochberg_fdr,
# save_fdr_corrected_pvalues, calculate_vif, save_vif_diagnostic_log,
# calculate_condition_number, log_collinearity_analysis

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Sets up logging to console and optionally a file."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def load_cleaned_data(data_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Loads the cleaned metallic glass dataset."""
    if data_path is None:
        data_path = get_project_root() / "data" / "processed" / "cleaned_mg.csv"
    else:
        data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {data_path}")
    return pd.read_csv(data_path)

def load_descriptors(data_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Loads the computed descriptors."""
    if data_path is None:
        data_path = get_project_root() / "data" / "processed" / "descriptors.csv"
    else:
        data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {data_path}")
    return pd.read_csv(data_path)

def load_model(model_path: Optional[Union[str, Path]] = None) -> Any:
    """Loads the trained model from a pickle file."""
    if model_path is None:
        model_path = get_project_root() / "artifacts" / "models" / "best_model.pkl"
    else:
        model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def calculate_correlation_matrix(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Calculates Pearson and Spearman correlation matrices."""
    corr_matrix = df[features].corr(method='pearson')
    return corr_matrix

def calculate_p_values(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Calculates p-values for correlations."""
    p_values = pd.DataFrame(index=features, columns=features, dtype=float)
    for i in features:
        for j in features:
            if i == j:
                p_values.loc[i, j] = 0.0
            else:
                corr, p = stats.pearsonr(df[i], df[j])
                p_values.loc[i, j] = p
    return p_values

def benjamini_hochberg_fdr(p_values: Union[pd.DataFrame, np.ndarray], alpha: float = 0.05) -> np.ndarray:
    """Applies Benjamini-Hochberg FDR correction to p-values."""
    if isinstance(p_values, pd.DataFrame):
        p_values = p_values.values.flatten()
    else:
        p_values = p_values.flatten()
    p_values = np.sort(p_values)
    n = len(p_values)
    ranks = np.arange(1, n + 1)
    corrected = p_values * n / ranks
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.minimum(corrected, 1.0)
    return corrected

def save_fdr_corrected_pvalues(p_values: np.ndarray, output_path: Union[str, Path]):
    """Saves FDR corrected p-values to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump({"corrected_p_values": p_values.tolist()}, f, indent=2)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculates Variance Inflation Factor (VIF) for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = {}
    X = df[features].values
    for i, feature in enumerate(features):
        vif = variance_inflation_factor(X, i)
        vif_data[feature] = vif
    return vif_data

def save_vif_diagnostic_log(vif_data: Dict[str, float], flagged_threshold: float = 5.0, output_path: Optional[Union[str, Path]] = None):
    """Saves VIF diagnostic log to a JSON file."""
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "vif_diagnostic_log.json"
    else:
        output_path = Path(output_path)
    flagged = [k for k, v in vif_data.items() if v > flagged_threshold]
    log_data = {
        "flagged_features": flagged,
        "vif_values": vif_data
    }
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def calculate_condition_number(df: pd.DataFrame, features: List[str]) -> float:
    """Calculates the condition number for collinearity analysis."""
    X = df[features].values
    cond_num = np.linalg.cond(X)
    return cond_num

def log_collinearity_analysis(condition_number: float, logger: logging.Logger, threshold: float = 30.0):
    """Logs collinearity analysis results."""
    status = "warning" if condition_number > threshold else "ok"
    logger.info(f"Collinearity condition number: {condition_number:.2f} (Status: {status})")

def bootstrap_feature_importance(model: Any, X: np.ndarray, y: np.ndarray, n_resamples: int = 1000, random_state: int = 42) -> Dict[str, Dict[str, float]]:
    """
    Performs bootstrapping to calculate 95% CI for feature importance.
    
    Args:
        model: Trained model with feature_importances_ attribute.
        X: Feature matrix.
        y: Target vector.
        n_resamples: Number of bootstrap resamples.
        random_state: Random seed for reproducibility.
    
    Returns:
        Dictionary with feature names as keys and {'ci_lower', 'ci_upper'} as values.
    """
    logger = logging.getLogger(__name__)
    np.random.seed(random_state)
    
    n_samples, n_features = X.shape
    feature_names = [f"feature_{i}" for i in range(n_features)]
    if hasattr(model, 'feature_names_in_'):
        feature_names = model.feature_names_in_
    
    importances_list = []
    
    logger.info(f"Starting bootstrapping with {n_resamples} resamples...")
    
    for i in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X[indices]
        y_boot = y[indices]
        
        # Retrain model on bootstrap sample
        # We assume the model is a GradientBoostingRegressor or similar
        # We need to clone the model to avoid modifying the original
        try:
            # Attempt to clone if possible, otherwise re-init with same params
            from sklearn.base import clone
            model_boot = clone(model)
            model_boot.fit(X_boot, y_boot)
            imp = model_boot.feature_importances_
        except Exception as e:
            logger.warning(f"Failed to bootstrap on resample {i}: {e}. Skipping.")
            continue
        
        importances_list.append(imp)
    
    if not importances_list:
        raise RuntimeError("Bootstrapping failed to produce any valid results.")
    
    importances_array = np.array(importances_list)
    n_boot = importances_array.shape[0]
    
    result = {}
    for i, feature in enumerate(feature_names):
        scores = importances_array[:, i]
        ci_lower = float(np.percentile(scores, 2.5))
        ci_upper = float(np.percentile(scores, 97.5))
        variance = float(np.var(scores))
        
        result[feature] = {
            "ci_lower": ci_lower,
            "ci_upper": ci_upper
        }
        
        if variance > 0.05:
            logger.warning(f"STABILITY_WARNING: Feature '{feature}' has high variance ({variance:.4f}) in importance scores.")
    
    return result

def main():
    """Main execution function for T036a."""
    logger = setup_logging()
    logger.info("Starting T036a: Bootstrapping for feature importance stability.")
    
    project_root = get_project_root()
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    data_path = project_root / "data" / "processed" / "cleaned_mg.csv"
    output_path = project_root / "artifacts" / "metrics" / "stability_metrics.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load model
        logger.info(f"Loading model from {model_path}")
        model = load_model(model_path)
        
        # Load data
        logger.info(f"Loading cleaned data from {data_path}")
        df = load_cleaned_data(data_path)
        
        # Identify feature columns (exclude 'Tg' and composition fields if any)
        # Assuming descriptors.csv has been joined or we use specific columns
        # For this task, we assume the model was trained on specific features.
        # We need to extract X and y from the cleaned data.
        # The cleaned data likely has 'Tg' as target and other columns as features.
        # Let's assume the model's feature names are available or we infer from data.
        
        # Check if model has feature_names_in_
        if hasattr(model, 'feature_names_in_'):
            feature_cols = list(model.feature_names_in_)
        else:
            # Fallback: assume all numeric columns except 'Tg' are features
            # This might need adjustment based on actual data schema
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'Tg' in numeric_cols:
                numeric_cols.remove('Tg')
            feature_cols = numeric_cols
        
        # Prepare X and y
        if 'Tg' not in df.columns:
            raise ValueError("Target column 'Tg' not found in cleaned data.")
        
        X = df[feature_cols].values
        y = df['Tg'].values
        
        logger.info(f"Running bootstrapping on {len(feature_cols)} features...")
        stability_metrics = bootstrap_feature_importance(model, X, y, n_resamples=1000)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(stability_metrics, f, indent=2)
        
        logger.info(f"Stability metrics saved to {output_path}")
        logger.info("T036a completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T036a execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
