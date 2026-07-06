import logging
import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
import json
from .utils import calculate_exclusion_ratio, calculate_processing_success_rate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_processed_data(filepath: str = "data/processed/coating_adhesion_dataset.csv") -> pd.DataFrame:
    """Load the processed dataset from disk."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found at {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded dataset with shape {df.shape}")
    return df

def prepare_surface_only_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """Extract surface-only features (RMS, skewness, kurtosis, etc.)."""
    surface_cols = [col for col in df.columns if col.startswith('surface_') or col in ['RMS', 'skewness', 'kurtosis', 'Ra', 'Rz']]
    if not surface_cols:
        logger.warning("No surface features found. Returning empty array.")
        return np.array([]), []
    X = df[surface_cols].values
    return X, surface_cols

def prepare_composition_only_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """Extract compositional features (elemental, one-hot encoded, proxies)."""
    comp_cols = [col for col in df.columns if col.startswith('comp_') or col.startswith('atomic_') or col.startswith('crosslinker')]
    if not comp_cols:
        logger.warning("No compositional features found. Returning empty array.")
        return np.array([]), []
    X = df[comp_cols].values
    return X, comp_cols

def prepare_full_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """Extract all features (surface + composition)."""
    surface_cols = [col for col in df.columns if col.startswith('surface_') or col in ['RMS', 'skewness', 'kurtosis', 'Ra', 'Rz']]
    comp_cols = [col for col in df.columns if col.startswith('comp_') or col.startswith('atomic_') or col.startswith('crosslinker')]
    all_features = surface_cols + comp_cols
    if not all_features:
        logger.warning("No features found.")
        return np.array([]), []
    X = df[all_features].values
    return X, all_features

def train_baseline_model(X: np.ndarray, y: np.ndarray, model_type: str = 'rf', cv_folds: int = 5) -> Dict[str, Any]:
    """Train a baseline model and return metrics."""
    if X.size == 0:
        return {"error": "Empty feature set", "r2": np.nan, "rmse": np.nan, "mae": np.nan}
    
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    elif model_type == 'ridge':
        model = Ridge(random_state=42)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    scores_r2 = cross_val_score(model, X, y, cv=kf, scoring='r2')
    
    # Fit on full data for final metrics (approximate)
    model.fit(X, y)
    y_pred = model.predict(X)
    
    return {
        "r2_mean": np.mean(scores_r2),
        "r2_std": np.std(scores_r2),
        "rmse": np.sqrt(mean_squared_error(y, y_pred)),
        "mae": mean_absolute_error(y, y_pred),
        "model_type": model_type
    }

def train_surface_only_baseline(df: pd.DataFrame, y_col: str = 'adhesion_strength') -> Dict[str, Any]:
    """Train and evaluate surface-only baseline."""
    X, cols = prepare_surface_only_features(df)
    y = df[y_col].values
    logger.info(f"Training surface-only baseline with {len(cols)} features.")
    return train_baseline_model(X, y, model_type='rf')

def train_composition_only_baseline(df: pd.DataFrame, y_col: str = 'adhesion_strength') -> Dict[str, Any]:
    """Train and evaluate composition-only baseline."""
    X, cols = prepare_composition_only_features(df)
    y = df[y_col].values
    logger.info(f"Training composition-only baseline with {len(cols)} features.")
    return train_baseline_model(X, y, model_type='rf')

def run_baseline_evaluation_pipeline(df: pd.DataFrame, y_col: str = 'adhesion_strength') -> Dict[str, Any]:
    """Run full baseline evaluation pipeline."""
    logger.info("Starting baseline evaluation pipeline.")
    
    surface_results = train_surface_only_baseline(df, y_col)
    comp_results = train_composition_only_baseline(df, y_col)
    full_results = train_baseline_model(*prepare_full_features(df), y=df[y_col].values, model_type='rf')
    
    return {
        "surface_only": surface_results,
        "composition_only": comp_results,
        "full_model": full_results
    }

def execute_nadeau_bengio_ttest(
    scores_full: np.ndarray, 
    scores_baseline: np.ndarray, 
    n_train: int, 
    n_test: int
) -> Dict[str, Any]:
    """
    Execute Nadeau & Bengio corrected t-test.
    scores_full: Array of R2 scores from full model CV folds
    scores_baseline: Array of R2 scores from baseline CV folds
    n_train: Number of training samples
    n_test: Number of test samples
    """
    if len(scores_full) != len(scores_baseline):
        raise ValueError("Score arrays must have equal length (same CV folds)")
    
    diff = scores_full - scores_baseline
    mean_diff = np.mean(diff)
    var_diff = np.var(diff, ddof=1)
    
    # Nadeau & Bengio correction factor
    # lambda = 1/n_train + 1/n_test
    n = len(scores_full)
    lambda_val = (1 / n_train) + (1 / n_test)
    
    # t-statistic
    # t = mean_diff / sqrt( (1/n + lambda) * var_diff )
    # Note: Standard error of the mean difference with correction
    se_corrected = np.sqrt((1/n + lambda_val) * var_diff)
    
    if se_corrected == 0:
        logger.warning("Standard error is zero. Returning p=1.0.")
        return {"t_stat": 0.0, "p_value": 1.0, "significant": False}
    
    t_stat = mean_diff / se_corrected
    df = n - 1
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    return {
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "mean_diff": float(mean_diff),
        "significant": p_value < 0.05
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction to a list of p-values."""
    k = len(p_values)
    if k == 0:
        return {"corrected_p_values": [], "significant_count": 0}
    
    corrected_alpha = alpha / k
    corrected_p_values = [min(p * k, 1.0) for p in p_values]
    significant = [p < corrected_alpha for p in corrected_p_values]
    
    return {
        "corrected_p_values": corrected_p_values,
        "corrected_alpha": corrected_alpha,
        "significant": significant,
        "significant_count": sum(significant)
    }

def flag_informative_null(
    full_model_results: Dict[str, Any], 
    baseline_results: Dict[str, Any], 
    p_value: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Flag "Informative Null" if full model does not statistically outperform baselines.
    
    Logic:
    1. Check if full model R2 > baseline R2 (point estimate).
    2. Check if the difference is statistically significant (p < threshold).
    3. If full model is better but NOT significant -> Informative Null (likely noise).
    4. If full model is NOT better -> Informative Null (features not useful).
    5. If full model is better AND significant -> Not Null (success).
    
    Returns a dict with the flag status and reasoning.
    """
    full_r2 = full_model_results.get("r2_mean", -np.inf)
    baseline_r2 = baseline_results.get("r2_mean", -np.inf)
    
    is_better = full_r2 > baseline_r2
    is_significant = p_value < threshold
    
    result = {
        "full_r2": full_r2,
        "baseline_r2": baseline_r2,
        "p_value": p_value,
        "is_better": is_better,
        "is_significant": is_significant,
        "informative_null_flag": False,
        "reasoning": ""
    }
    
    if not is_better:
        result["informative_null_flag"] = True
        result["reasoning"] = "Full model R2 is not greater than baseline R2. Features provide no added value."
    elif not is_significant:
        result["informative_null_flag"] = True
        result["reasoning"] = "Full model R2 is slightly higher but not statistically significant (p >= 0.05). Result is likely noise."
    else:
        result["reasoning"] = "Full model significantly outperforms baseline. Result is valid."
        
    logger.info(f"Informative Null Flag: {result['informative_null_flag']} - {result['reasoning']}")
    return result

def main():
    """Main entry point for evaluation pipeline including Informative Null check."""
    logger.info("Starting Evaluation Pipeline (US3).")
    
    # Load data
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"status": "error", "message": str(e)}
    
    # Run baseline evaluation
    results = run_baseline_evaluation_pipeline(df)
    
    # Extract R2 scores for t-test (mocking CV score extraction for t-test)
    # In a real scenario, we would capture the individual fold scores from cross_val_score
    # Here we approximate by running a specific CV loop to get fold scores
    y = df['adhesion_strength'].values
    X_full, _ = prepare_full_features(df)
    X_base, _ = prepare_composition_only_features(df) # Using comp-only as baseline for t-test example
    
    if X_full.size == 0 or X_base.size == 0:
        logger.error("Feature sets are empty.")
        return {"status": "error", "message": "Empty feature sets"}
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    full_scores = cross_val_score(GradientBoostingRegressor(n_estimators=100, random_state=42), X_full, y, cv=kf, scoring='r2')
    base_scores = cross_val_score(GradientBoostingRegressor(n_estimators=100, random_state=42), X_base, y, cv=kf, scoring='r2')
    
    # Calculate t-test
    n_train = len(y) // 5 # Approximate
    n_test = len(y) // 5
    ttest_results = execute_nadeau_bengio_ttest(full_scores, base_scores, n_train, n_test)
    
    # Apply Bonferroni (if multiple comparisons, here just 1)
    bonf_results = apply_bonferroni_correction([ttest_results["p_value"]])
    
    # Flag Informative Null
    null_check = flag_informative_null(
        results["full_model"],
        results["composition_only"], # Comparing against comp-only baseline
        ttest_results["p_value"]
    )
    
    final_report = {
        "baselines": results,
        "statistical_test": ttest_results,
        "bonferroni": bonf_results,
        "informative_null": null_check,
        "status": "completed"
    }
    
    # Save report
    output_path = "data/processed/evaluation_report.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Evaluation report saved to {output_path}")
    return final_report

if __name__ == "__main__":
    main()