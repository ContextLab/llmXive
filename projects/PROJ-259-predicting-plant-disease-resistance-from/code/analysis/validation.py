import os
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score, mean_squared_error
from statsmodels.stats.outliers_influence import variance_inflation_factor
from config import get_path, load_config
from utils.exceptions import PipelineException, EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT
from utils.logging import setup_logger, log_pipeline_step, log_sample_exclusion

logger = setup_logger(__name__)

def load_split_data(split_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the stratified split data (train/val/test) from data/processed.
    
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
    """
    if split_dir is None:
        split_dir = get_path("data_processed")
    
    train_path = split_dir / "train_split.parquet"
    test_path = split_dir / "test_split.parquet"
    
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Split data not found at {split_dir}. Run split pipeline first.")
    
    train_data = pd.read_parquet(train_path)
    test_data = pd.read_parquet(test_path)
    
    # Assuming phenotype is in a column named 'phenotype' and features are the rest
    feature_cols = [col for col in train_data.columns if col != 'phenotype']
    
    X_train = train_data[feature_cols]
    y_train = train_data['phenotype']
    X_test = test_data[feature_cols]
    y_test = test_data['phenotype']
    
    logger.info(f"Loaded split data: Train ({X_train.shape}), Test ({X_test.shape})")
    return X_train, y_train, X_test, y_test

def load_model(model_path: Optional[Path] = None) -> Any:
    """
    Load the trained model from artifacts/models.
    
    Returns:
        The trained model object.
    """
    if model_path is None:
        model_path = get_path("models") / "best_model.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run modeling pipeline first.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_path}")
    return model

def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate the trained model on the independent hold-out test set.
    
    This function calculates accuracy (for classification) or R² (for regression)
    and AUC if applicable. It logs the results and returns a dictionary of metrics.
    
    Args:
        model: The trained model instance.
        X_test: The feature matrix for the test set.
        y_test: The true labels/values for the test set.
        
    Returns:
        Dictionary containing evaluation metrics.
    """
    log_pipeline_step(logger, "Evaluating model on hold-out set")
    
    # Predict
    y_pred = model.predict(X_test)
    
    metrics = {}
    
    # Check if classification or regression based on y_test dtype
    if y_test.dtype in ['int64', 'int32', 'bool'] or len(np.unique(y_test)) < 10:
        # Classification metrics
        metrics['accuracy'] = float(accuracy_score(y_test, y_pred))
        
        # AUC only if binary classification and probabilities can be predicted
        if len(np.unique(y_test)) == 2 and hasattr(model, 'predict_proba'):
            y_prob = model.predict_proba(X_test)[:, 1]
            metrics['auc'] = float(roc_auc_score(y_test, y_prob))
            logger.info(f"AUC calculated: {metrics['auc']:.4f}")
        else:
            metrics['auc'] = None
            logger.info("AUC not calculated (not binary or no predict_proba)")
            
        logger.info(f"Test Accuracy: {metrics['accuracy']:.4f}")
    else:
        # Regression metrics
        metrics['r2'] = float(r2_score(y_test, y_pred))
        metrics['rmse'] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        logger.info(f"Test R²: {metrics['r2']:.4f}")
        logger.info(f"Test RMSE: {metrics['rmse']:.4f}")
    
    log_pipeline_step(logger, "Evaluation complete", extra={"metrics": metrics})
    return metrics

def train_null_model_baseline(X_train: pd.DataFrame, y_train: pd.Series) -> Any:
    """
    Train a null model baseline (e.g., dummy classifier/regressor) for comparison.
    
    This creates a model that predicts the majority class (classification) or
    the mean (regression) to establish a baseline performance.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        
    Returns:
        Trained null model.
    """
    from sklearn.dummy import DummyClassifier, DummyRegressor
    
    if y_train.dtype in ['int64', 'int32', 'bool'] or len(np.unique(y_train)) < 10:
        null_model = DummyClassifier(strategy='most_frequent')
    else:
        null_model = DummyRegressor(strategy='mean')
    
    null_model.fit(X_train, y_train)
    logger.info("Trained null model baseline")
    return null_model

def compare_models(model: Any, null_model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Compare the primary model against the null model baseline on the test set.
    
    Args:
        model: The primary trained model.
        null_model: The null baseline model.
        X_test: Test features.
        y_test: Test labels.
        
    Returns:
        Dictionary with performance of both models and the improvement.
    """
    primary_metrics = evaluate_model(model, X_test, y_test)
    null_metrics = evaluate_model(null_model, X_test, y_test)
    
    comparison = {
        'primary_model': primary_metrics,
        'null_model': null_metrics,
        'improvement': {}
    }
    
    # Calculate improvement
    if 'accuracy' in primary_metrics and primary_metrics['accuracy'] is not None:
        improvement = primary_metrics['accuracy'] - null_metrics.get('accuracy', 0)
        comparison['improvement']['accuracy'] = improvement
        logger.info(f"Accuracy improvement over null: {improvement:.4f}")
    
    if 'r2' in primary_metrics and primary_metrics['r2'] is not None:
        improvement = primary_metrics['r2'] - null_metrics.get('r2', 0)
        comparison['improvement']['r2'] = improvement
        logger.info(f"R² improvement over null: {improvement:.4f}")
        
    return comparison

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        X: Feature DataFrame.
        
    Returns:
        Series of VIF values indexed by feature name.
    """
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    vif_data = pd.Series(
        [variance_inflation_factor(X_with_const.values, i) for i in range(X_with_const.shape[1])],
        index=X_with_const.columns
    )
    # Drop the constant term VIF
    return vif_data.drop('const')

def flag_multicollinearity(X: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """
    Flag features with VIF > threshold indicating multicollinearity.
    
    Args:
        X: Feature DataFrame.
        threshold: VIF threshold for flagging.
        
    Returns:
        List of feature names with high VIF.
    """
    vif_series = calculate_vif(X)
    flagged = vif_series[vif_series > threshold].index.tolist()
    
    if flagged:
        logger.warning(f"Multicollinearity detected in {len(flagged)} features (VIF > {threshold}): {flagged}")
    else:
        logger.info("No multicollinearity detected (all VIF < {threshold})")
        
    return flagged

def run_validation_pipeline(
    model_path: Optional[Path] = None,
    split_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full validation pipeline on the hold-out set.
    
    Steps:
    1. Load split data (specifically the hold-out set).
    2. Load the trained model.
    3. Evaluate the model on the hold-out set.
    4. Train and evaluate a null model baseline.
    5. Compare performance.
    6. Check for multicollinearity in the test set features.
    7. Save results to artifacts/reports/holdout_metrics.json.
    
    Args:
        model_path: Path to the trained model pickle.
        split_dir: Path to the split data directory.
        output_dir: Path to save the results.
        
    Returns:
        Dictionary containing all validation results.
    """
    log_pipeline_step(logger, "Starting validation pipeline on hold-out set")
    
    # Load data
    X_train, y_train, X_test, y_test = load_split_data(split_dir)
    
    # Load model
    model = load_model(model_path)
    
    # Evaluate primary model
    primary_metrics = evaluate_model(model, X_test, y_test)
    
    # Train and evaluate null model
    null_model = train_null_model_baseline(X_train, y_train)
    comparison = compare_models(model, null_model, X_test, y_test)
    
    # Check multicollinearity
    flagged_features = flag_multicollinearity(X_test)
    
    # Compile results
    results = {
        "model_path": str(model_path) if model_path else "default",
        "test_set_size": len(X_test),
        "metrics": primary_metrics,
        "null_model_comparison": comparison,
        "multicollinearity": {
            "flagged_features": flagged_features,
            "threshold": 5.0
        }
    }
    
    # Save results
    if output_dir is None:
        output_dir = get_path("reports")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "holdout_metrics.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_file}")
    log_pipeline_step(logger, "Validation pipeline complete")
    
    return results

def main():
    """Entry point for validation script."""
    logger.info("Running validation module main")
    config = load_config()
    
    # Paths from config or defaults
    model_path = get_path("models") / "best_model.pkl"
    split_dir = get_path("data_processed")
    output_dir = get_path("reports")
    
    try:
        results = run_validation_pipeline(
            model_path=model_path,
            split_dir=split_dir,
            output_dir=output_dir
        )
        print(json.dumps(results, indent=2, default=str))
    except Exception as e:
        logger.error(f"Validation pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()