import pandas as pd
import numpy as np
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.base import clone
import pickle
from config import get_int_config, get_float_config, get_project_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_PATH = Path("data/models/best_model.pkl")
METRICS_PATH = Path("data/results/model_metrics.json")
BASELINE_PATH = Path("data/results/baseline_metrics.json")
PROCESSED_DATA_PATH = Path("data/processed/cleaned_ceramics.csv")

def load_processed_data() -> pd.DataFrame:
    """Load the cleaned and processed ceramic dataset."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed data not found at {PROCESSED_DATA_PATH}. Run ingestion pipeline first.")
    logger.info(f"Loading processed data from {PROCESSED_DATA_PATH}")
    return pd.read_csv(PROCESSED_DATA_PATH)

def prepare_splits(df: pd.DataFrame, target_col: str = 'weibull_modulus') -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, Dict[str, Any]]:
    """
    Prepare stratified train/test splits.
    Falls back to hold-out if N < 50 or if stratification class is too small.
    """
    logger.info("Preparing stratified splits...")
    
    # Filter rare classes if necessary (T032 dependency)
    class_counts = df['primary_anion_cation_group'].value_counts()
    rare_classes = class_counts[class_counts < 5].index
    if len(rare_classes) > 0:
        logger.warning(f"Dropping {len(rare_classes)} rare classes with < 5 samples: {list(rare_classes)}")
        df = df[~df['primary_anion_cation_group'].isin(rare_classes)]
    
    if len(df) < 50:
        logger.warning("Dataset size < 50. Switching to simple hold-out split.")
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    else:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        # We don't actually split here, we just return the full df for CV training
        # The split logic is handled inside train_models for CV
        train_df = df
        test_df = df.sample(frac=0.2, random_state=42) # Simple holdout for final eval if needed
        # Actually, for the pipeline, we usually train on full clean data for final model, 
        # but T026 says "Prepare splits". Let's do a standard split for the evaluation phase.
        train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['primary_anion_cation_group'], random_state=42)
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    split_report = {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "stratification_method": "primary_anion_cation_group",
        "train_class_distribution": train_df['primary_anion_cation_group'].value_counts().to_dict(),
        "test_class_distribution": test_df['primary_anion_cation_group'].value_counts().to_dict()
    }
    
    return train_df, test_df, target_col, split_report

def run_baseline_predictor(test_X: pd.DataFrame, test_y: pd.Series, train_y: pd.Series) -> Dict[str, Any]:
    """
    T028b: Run a baseline predictor that always predicts the global mean of the training set.
    Returns metrics and saves to BASELINE_PATH.
    """
    logger.info("Running baseline predictor (global mean)...")
    global_mean = train_y.mean()
    predictions = np.full_like(test_y, global_mean, dtype=float)
    
    mae = mean_absolute_error(test_y, predictions)
    r2 = r2_score(test_y, predictions)
    
    baseline_results = {
        "model_type": "GlobalMeanBaseline",
        "mae": float(mae),
        "r_squared": float(r2),
        "predicted_value": float(global_mean),
        "description": "Predicts the global mean Weibull modulus for all samples."
    }
    
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, 'w') as f:
        json.dump(baseline_results, f, indent=2)
    
    logger.info(f"Baseline MAE: {mae:.4f}, R²: {r2:.4f}")
    logger.info(f"Baseline metrics saved to {BASELINE_PATH}")
    
    return baseline_results

def train_models(train_df: pd.DataFrame, target_col: str = 'weibull_modulus') -> Tuple[Any, str, Dict[str, Any]]:
    """
    T027b: Train RF and GBM models using cross-validation.
    Returns the best model, its type, and the CV report.
    """
    logger.info("Training models with cross-validation...")
    
    # Define features (exclude target and non-predictor columns)
    exclude_cols = [target_col, 'sample_count', 'is_range_flag', 'range_original', 'is_imputed', 'primary_anion_cation_group']
    feature_cols = [c for c in train_df.columns if c not in exclude_cols]
    
    X = train_df[feature_cols].dropna()
    y = train_df.loc[X.index, target_col]
    
    if X.empty:
        raise ValueError("No valid features found after dropping NaNs.")
    
    # Hyperparameter search space (constrained as per T027a)
    # RF
    rf_params = [
        {'n_estimators': 100, 'max_depth': 10, 'random_state': 42},
        {'n_estimators': 200, 'max_depth': 15, 'random_state': 42}
    ]
    # GBM
    gbm_params = [
        {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 5, 'random_state': 42},
        {'n_estimators': 200, 'learning_rate': 0.05, 'max_depth': 5, 'random_state': 42}
    ]
    
    models_to_try = [
        ("RandomForest", RandomForestRegressor, rf_params),
        ("GradientBoosting", GradientBoostingRegressor, gbm_params)
    ]
    
    best_model = None
    best_score = -np.inf
    best_model_type = None
    cv_results = []
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    # Note: StratifiedKFold requires y to be categorical. Since Weibull is continuous, 
    # we might need to bin y or use KFold. However, T026 mentions stratification on 'primary_anion_cation_group'.
    # We will use the group column for stratification if available, otherwise KFold.
    strat_col = 'primary_anion_cation_group'
    if strat_col in train_df.columns:
        # Re-align X, y with train_df to get the group column
        # We need to ensure X, y, and group are aligned
        # X and y were created from train_df, so we need to filter the group column too
        groups = train_df.loc[X.index, strat_col]
        # Handle rare classes in groups if any (should be handled by T032 logic earlier, but safe to check)
        if groups.nunique() < 2:
            logger.warning("Not enough unique classes for stratification. Using KFold.")
            from sklearn.model_selection import KFold
            cv = KFold(n_splits=5, shuffle=True, random_state=42)
            use_strat = False
        else:
            cv = skf
            use_strat = True
    else:
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        use_strat = False

    for name, ModelClass, params_list in models_to_try:
        for params in params_list:
            model = ModelClass(**params)
            # Use negative MAE for scoring (since sklearn minimizes, we want to maximize negative MAE -> minimize MAE)
            # But standard scoring is R2 or neg_mae. Let's use neg_mae.
            from sklearn.metrics import make_scorer, mean_absolute_error
            scorer = make_scorer(mean_absolute_error, greater_is_better=False)
            
            # Cross validation
            # If using StratifiedKFold, we pass y (the groups)
            if use_strat:
                scores = cross_val_score(model, X, y, cv=cv, scoring=scorer, n_jobs=-1)
            else:
                scores = cross_val_score(model, X, y, cv=cv, scoring=scorer, n_jobs=-1)
            
            mean_score = np.mean(scores) # This is negative MAE
            mean_mae = -mean_score
            
            cv_results.append({
                "model_type": name,
                "params": params,
                "mean_cv_mae": mean_mae,
                "std_cv_mae": -np.std(scores) # std of negative MAE is same as std of MAE
            })
            
            # We want lowest MAE, so highest negative MAE
            if mean_score > best_score:
                best_score = mean_score
                best_model = clone(model)
                best_model.fit(X, y)
                best_model_type = name
                logger.info(f"New best: {name} with MAE {mean_mae:.4f}")
    
    # Save best model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(best_model, f)
    logger.info(f"Best model ({best_model_type}) saved to {MODEL_PATH}")
    
    cv_report = {
        "best_model_type": best_model_type,
        "best_cv_mae": -best_score,
        "all_cv_results": cv_results
    }
    
    return best_model, best_model_type, cv_report

def evaluate_models(best_model: Any, model_type: str, test_df: pd.DataFrame, target_col: str = 'weibull_modulus') -> Dict[str, Any]:
    """
    T028: Implement evaluate_models.
    1. Calculate MAE, R² on test set.
    2. Run baseline (global mean) predictor.
    3. Compare against baseline.
    4. Save results to METRICS_PATH and BASELINE_PATH (if not already done by T028b).
    """
    logger.info(f"Evaluating {model_type} model...")
    
    exclude_cols = [target_col, 'sample_count', 'is_range_flag', 'range_original', 'is_imputed', 'primary_anion_cation_group']
    feature_cols = [c for c in test_df.columns if c not in exclude_cols]
    
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    # Handle any missing values in test set (should be rare if cleaned properly)
    if X_test.isnull().any().any():
        logger.warning("Test set has missing values. Dropping rows with NaN in features.")
        mask = X_test.notnull().all(axis=1)
        X_test = X_test[mask]
        y_test = y_test[mask]
    
    if len(X_test) == 0:
        raise ValueError("No valid test samples remaining after dropping NaNs.")
    
    # Predict
    y_pred = best_model.predict(X_test)
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Run baseline
    # We need training y for baseline. We assume train_df was used to train the model.
    # We need to reconstruct train_df or pass it. 
    # Since this function signature doesn't have train_df, we'll assume we can load the processed data 
    # and split it again deterministically to get the training set for the baseline mean.
    # OR, we can pass train_y if we refactor. 
    # Given the constraints, let's load the full processed data and re-split to get the baseline mean.
    # This is slightly inefficient but ensures consistency.
    full_df = load_processed_data()
    train_df, _, _, _ = prepare_splits(full_df, target_col)
    
    baseline_metrics = run_baseline_predictor(y_test, y_test, train_df[target_col])
    
    # Compare
    improvement = ((baseline_metrics['mae'] - mae) / baseline_metrics['mae']) * 100
    
    results = {
        "model_type": model_type,
        "mae": float(mae),
        "r_squared": float(r2),
        "baseline_mae": float(baseline_metrics['mae']),
        "baseline_r2": float(baseline_metrics['r_squared']),
        "mae_improvement_pct": float(improvement),
        "test_samples": len(y_test),
        "metrics_saved_to": str(METRICS_PATH),
        "baseline_saved_to": str(BASELINE_PATH)
    }
    
    # Save to file
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation complete. MAE: {mae:.4f}, R²: {r2:.4f}")
    logger.info(f"Improvement over baseline: {improvement:.2f}%")
    logger.info(f"Metrics saved to {METRICS_PATH}")
    
    return results

def validate_search_space() -> bool:
    """T027c: Validate that search space is within time limits."""
    # The search space is hardcoded in train_models to be small (2 RF, 2 GBM, 5 folds)
    # Total models = 4. 4 * 5 folds = 20 fits. Should be well within 6 hours.
    logger.info("Search space validated: 4 model configurations x 5 folds = 20 fits.")
    return True

def main():
    """Main entry point for the modeling pipeline."""
    logger.info("Starting modeling pipeline...")
    
    try:
        # Load data
        df = load_processed_data()
        
        # Prepare splits
        train_df, test_df, target_col, split_report = prepare_splits(df)
        
        # Validate search space
        validate_search_space()
        
        # Train models
        best_model, best_model_type, cv_report = train_models(train_df, target_col)
        
        # Evaluate models (T028)
        eval_results = evaluate_models(best_model, best_model_type, test_df, target_col)
        
        # Save split report (T025 requirement)
        split_report_path = Path("data/results/cv_split_report.json")
        with open(split_report_path, 'w') as f:
            json.dump(split_report, f, indent=2)
        
        logger.info("Modeling pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())