"""
Statistical testing module for comparing model performance against a null model.

Implements null-model statistical tests using bootstrap resampling and t-tests
to determine if the trained model is statistically distinguishable from a null model.
"""
import json
import os
import sys
import logging
from typing import Dict, Any, List
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json(filepath: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved results to {filepath}")

def load_processed_data(data_path: str) -> tuple:
    """Load processed alloy data and extract features/target."""
    import pandas as pd
    df = pd.read_csv(data_path)
    
    # Define feature columns (thermodynamic descriptors)
    feature_cols = [
        'mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance',
        'valence_electron_concentration'
    ]
    
    # Ensure all feature columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns: {missing_cols}")
    
    X = df[feature_cols].values
    y = df['critical_cooling_rate'].values
    
    return X, y

def run_cross_validation_scores(
    X: np.ndarray,
    y: np.ndarray,
    model_class,
    model_params: Dict[str, Any],
    n_splits: int = 5,
    random_state: int = 42
) -> List[float]:
    """
    Run k-fold cross-validation and return RMSE scores for each fold.
    
    Args:
        X: Feature matrix
        y: Target values
        model_class: sklearn model class
        model_params: Parameters for model initialization
        n_splits: Number of CV folds
        random_state: Random seed for reproducibility
        
    Returns:
        List of RMSE scores for each fold
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    rmse_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = model_class(**model_params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        rmse_scores.append(rmse)
    
    return rmse_scores

def bootstrap_null_distribution(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    n_bootstrap: int = 1000,
    random_state: int = 42
) -> np.ndarray:
    """
    Generate bootstrap distribution of CV RMSE scores for a null model.
    
    Args:
        X: Feature matrix
        y: Target values
        n_splits: Number of CV folds per bootstrap iteration
        n_bootstrap: Number of bootstrap resamples
        random_state: Random seed
        
    Returns:
        Array of bootstrap RMSE scores
    """
    logger.info(f"Generating null distribution with {n_bootstrap} bootstrap resamples...")
    
    np.random.seed(random_state)
    null_scores = []
    
    # Use a fixed random state generator for reproducibility within bootstrap
    rng = np.random.RandomState(random_state)
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = rng.choice(len(X), size=len(X), replace=True)
        X_resample = X[indices]
        y_resample = y[indices]
        
        # Run CV on resampled data with null model
        null_params = {'strategy': 'mean'}
        scores = run_cross_validation_scores(
            X_resample, y_resample, DummyRegressor, null_params, 
            n_splits=n_splits, random_state=random_state
        )
        
        # Store mean RMSE for this bootstrap iteration
        null_scores.append(np.mean(scores))
        
        if (i + 1) % 200 == 0:
            logger.info(f"  Bootstrap iteration {i + 1}/{n_bootstrap}")
    
    return np.array(null_scores)

def run_statistical_test(
    model_cv_scores: List[float],
    X: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: int = 42,
    output_dir: str = "data/models"
) -> Dict[str, Any]:
    """
    Perform statistical test comparing model CV scores against null model distribution.
    
    Args:
        model_cv_scores: List of RMSE scores from the trained model's CV
        X: Feature matrix
        y: Target values
        n_bootstrap: Number of bootstrap resamples for null distribution
        random_state: Random seed
        output_dir: Directory to save results
        
    Returns:
        Dictionary with test results
    """
    logger.info("Starting null-model statistical test...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate null distribution
    null_distribution = bootstrap_null_distribution(
        X, y, n_splits=5, n_bootstrap=n_bootstrap, random_state=random_state
    )
    
    # Save null distribution
    null_distribution_path = os.path.join(output_dir, "null_model_cv_scores.json")
    save_json({
        "null_scores": null_distribution.tolist(),
        "mean_null_rmse": float(np.mean(null_distribution)),
        "std_null_rmse": float(np.std(null_distribution)),
        "n_bootstrap": n_bootstrap
    }, null_distribution_path)
    
    logger.info(f"Null distribution: mean={np.mean(null_distribution):.4f}, "
               f"std={np.std(null_distribution):.4f}")
    
    # Convert model scores to array
    model_scores_array = np.array(model_cv_scores)
    
    # Perform two-sample t-test
    t_stat, p_value = stats.ttest_ind(model_scores_array, null_distribution)
    
    logger.info(f"T-statistic: {t_stat:.4f}")
    logger.info(f"P-value: {p_value:.6f}")
    
    # Determine if SC-002 is met (p < 0.05)
    sc002_met = p_value < 0.05
    
    results = {
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "sc002_met": sc002_met,
        "model_cv_scores": model_cv_scores,
        "model_mean_rmse": float(np.mean(model_scores_array)),
        "model_std_rmse": float(np.std(model_scores_array)),
        "null_mean_rmse": float(np.mean(null_distribution)),
        "null_std_rmse": float(np.std(null_distribution)),
        "n_bootstrap": n_bootstrap
    }
    
    # Save results
    output_path = os.path.join(output_dir, "statistical_comparison.json")
    save_json(results, output_path)
    
    logger.info(f"Statistical test complete. SC-002 {'PASSED' if sc002_met else 'FAILED'} "
               f"(p={p_value:.6f})")
    
    return results

def main():
    """Main entry point for statistical test."""
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "processed", "processed_alloys.csv")
    cv_metrics_path = os.path.join(base_dir, "data", "models", "cv_metrics.json")
    output_dir = os.path.join(base_dir, "data", "models")
    
    # Verify inputs exist
    if not os.path.exists(data_path):
        logger.error(f"Processed data not found at {data_path}")
        sys.exit(1)
        
    if not os.path.exists(cv_metrics_path):
        logger.error(f"CV metrics not found at {cv_metrics_path}")
        sys.exit(1)
    
    # Load CV scores from model
    cv_metrics = load_json(cv_metrics_path)
    model_cv_scores = cv_metrics.get("fold_scores", [])
    
    if not model_cv_scores or len(model_cv_scores) != 5:
        logger.error(f"Invalid CV scores: expected 5 fold scores, got {len(model_cv_scores)}")
        sys.exit(1)
    
    logger.info(f"Loaded model CV scores: {model_cv_scores}")
    
    # Load data
    X, y = load_processed_data(data_path)
    logger.info(f"Loaded data: {len(X)} samples, {X.shape[1]} features")
    
    # Run statistical test
    results = run_statistical_test(
        model_cv_scores=model_cv_scores,
        X=X,
        y=y,
        n_bootstrap=1000,
        random_state=42,
        output_dir=output_dir
    )
    
    # Print summary
    print("\n" + "="*50)
    print("STATISTICAL TEST RESULTS")
    print("="*50)
    print(f"T-statistic: {results['t_statistic']:.4f}")
    print(f"P-value: {results['p_value']:.6f}")
    print(f"Model Mean RMSE: {results['model_mean_rmse']:.4f}")
    print(f"Null Mean RMSE: {results['null_mean_rmse']:.4f}")
    print(f"SC-002 Met: {results['sc002_met']}")
    print("="*50)
    
    return results

if __name__ == "__main__":
    main()