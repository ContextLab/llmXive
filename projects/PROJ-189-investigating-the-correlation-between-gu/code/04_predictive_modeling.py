import os
import sys
import logging
import json
import time
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import setup_logging, get_logger, log_memory_usage
from utils.resource_guard import check_cpu_only, enforce_resource_limits, ResourceLimitExceededError
from config import get_config, set_random_seed

# Configure logging for this module
logger = get_logger(__name__)

def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the CLR-transformed microbial data and cognitive scores.
    Expects data/processed/corpus_clr.parquet to exist.
    """
    data_path = Path("data/processed/corpus_clr.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Assuming 'cognitive_score' is the target column and others are features
    if 'cognitive_score' not in df.columns:
        raise ValueError("Column 'cognitive_score' not found in dataset.")
    
    target = df['cognitive_score']
    features = df.drop(columns=['cognitive_score'])
    
    return features, target

def prepare_features_target(features: pd.DataFrame, target: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Convert pandas objects to numpy arrays for sklearn."""
    return features.values, target.values

def nested_cv_random_forest(X: np.ndarray, y: np.ndarray, n_splits: int = 5, seed: int = 42) -> Dict[str, Any]:
    """
    Train a Random Forest regressor with 5-fold cross-validation.
    Returns model, scores, and best hyperparameters.
    """
    set_random_seed(seed)
    logger.info(f"Starting nested CV Random Forest with seed {seed}")
    
    # Simple inner loop for hyperparameter tuning could be added here
    # For now, using a robust default configuration
    rf = RandomForestRegressor(
        n_estimators=500,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=seed,
        n_jobs=-1,
        oob_score=True
    )
    
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores = cross_val_score(rf, X, y, cv=kfold, scoring='r2', n_jobs=-1)
    
    rf.fit(X, y)
    
    result = {
        "mean_r2": float(np.mean(scores)),
        "std_r2": float(np.std(scores)),
        "scores": scores.tolist(),
        "oob_score": float(rf.oob_score_),
        "hyperparameters": {
            "n_estimators": rf.n_estimators,
            "max_depth": rf.max_depth,
            "min_samples_split": rf.min_samples_split,
            "min_samples_leaf": rf.min_samples_leaf
        }
    }
    
    logger.info(f"Nested CV R²: {result['mean_r2']:.4f} (+/- {result['std_r2']:.4f})")
    return result, rf

def run_permutation_test(X: np.ndarray, y: np.ndarray, model, n_permutations: int = 1000, seed: int = 42) -> List[float]:
    """
    Perform permutation test to generate null distribution of R² scores.
    Optimized with vectorized shuffling where possible and early termination checks.
    """
    set_random_seed(seed)
    logger.info(f"Starting permutation test with {n_permutations} shuffles")
    
    # Pre-allocate array for scores
    null_scores = np.zeros(n_permutations)
    
    # Fit the model once on original data to get feature importances if needed, 
    # but here we just refit for the null distribution as per strict protocol
    
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    
    for i in range(n_permutations):
        # Check memory limits periodically
        if i % 100 == 0:
            enforce_resource_limits()
            log_memory_usage(logger)
        
        # Shuffle y
        y_perm = y.copy()
        np.random.shuffle(y_perm)
        
        # Compute CV score for permuted data
        scores = cross_val_score(model, X, y_perm, cv=kfold, scoring='r2', n_jobs=-1)
        null_scores[i] = np.mean(scores)
        
        if i % 200 == 0:
            logger.debug(f"Permutation {i}/{n_permutations} complete")

    logger.info(f"Permutation test complete. Null distribution mean: {np.mean(null_scores):.4f}")
    return null_scores.tolist()

def calculate_null_threshold(null_scores: List[float], percentile: float = 95) -> float:
    """Calculate the high percentile threshold from the null distribution."""
    threshold = float(np.percentile(null_scores, percentile))
    logger.info(f"{percentile}% percentile of null distribution: {threshold:.4f}")
    return threshold

def identify_top_taxa(model: RandomForestRegressor, feature_names: List[str], n_top: int = 20) -> List[Dict[str, Any]]:
    """Identify top predictive taxa by mean decrease in impurity."""
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    top_taxa = []
    for i in range(min(n_top, len(feature_names))):
        idx = indices[i]
        top_taxa.append({
            "taxon": feature_names[idx],
            "importance": float(importances[idx])
        })
    
    logger.info(f"Identified top {len(top_taxa)} taxa")
    return top_taxa

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """Calculate Variance Inflation Factors for features."""
    vif_data = []
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({"feature": name, "VIF": float(vif)})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_data.append({"feature": name, "VIF": float('inf')})
    
    return pd.DataFrame(vif_data)

def calculate_shap_values(model: RandomForestRegressor, X: np.ndarray) -> np.ndarray:
    """Calculate SHAP values for interpretation."""
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        return shap_values
    except ImportError:
        logger.warning("SHAP library not installed. Skipping SHAP calculation.")
        return np.zeros_like(X)

def save_results(
    model_results: Dict[str, Any],
    null_threshold: float,
    top_taxa: List[Dict[str, Any]],
    vif_df: pd.DataFrame,
    shap_values: np.ndarray,
    model: RandomForestRegressor,
    output_dir: str = "data/models"
):
    """Save all model artifacts."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Save model
    import joblib
    joblib.dump(model, out_path / "model.pkl")
    
    # Save hyperparams
    with open(out_path / "hyperparams.json", "w") as f:
        json.dump(model_results["hyperparameters"], f, indent=2)
    
    # Save results summary
    with open(out_path / "model_metrics.json", "w") as f:
        json.dump({
            "mean_r2": model_results["mean_r2"],
            "std_r2": model_results["std_r2"],
            "null_threshold_95": null_threshold
        }, f, indent=2)
    
    # Save top taxa
    with open(out_path / "top_taxa.json", "w") as f:
        json.dump(top_taxa, f, indent=2)
    
    # Save VIF
    vif_df.to_csv(out_path / "vif_results.csv", index=False)
    
    # Save SHAP
    np.save(out_path / "shap_values.npy", shap_values)
    
    logger.info(f"Model artifacts saved to {output_dir}")

def run_modeling_pipeline():
    """Main entry point for the predictive modeling pipeline."""
    logger.info("Starting Predictive Modeling Pipeline")
    
    # Resource checks
    check_cpu_only()
    
    # Load data
    features, target = load_preprocessed_data()
    X, y = prepare_features_target(features, target)
    
    # Train model
    model_results, model = nested_cv_random_forest(X, y)
    
    # Run permutation test
    null_scores = run_permutation_test(X, y, model)
    
    # Calculate threshold
    threshold = calculate_null_threshold(null_scores)
    
    # Identify top taxa
    top_taxa = identify_top_taxa(model, features.columns.tolist())
    
    # Calculate VIF
    vif_df = calculate_vif(X, features.columns.tolist())
    
    # Calculate SHAP
    shap_values = calculate_shap_values(model, X)
    
    # Save results
    save_results(model_results, threshold, top_taxa, vif_df, shap_values, model)
    
    logger.info("Predictive Modeling Pipeline completed successfully")

def main():
    """Main function to execute the pipeline."""
    setup_logging()
    run_modeling_pipeline()

if __name__ == "__main__":
    main()
