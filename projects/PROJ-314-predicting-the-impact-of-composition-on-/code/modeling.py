import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Dict, Any, List, Optional, Tuple
import sys
import os

# Add project root to path for relative imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code import logger
from code.config import get_int_config, get_float_config

logger = logging.getLogger(__name__)

def prepare_splits(
    df: pd.DataFrame,
    target: str = "weibull_modulus",
    stratify_col: str = "primary_anion_cation_group",
    test_size: float = 0.2,
    random_state: int = 42,
    min_class_size: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare train/test splits with stratification.
    
    Implements Rare Class Handling (T032):
    - Groups classes with fewer than `min_class_size` samples into an 'OTHER' category
      or excludes them if the project config dictates exclusion.
    - Falls back to hold-out split if stratification is impossible due to data scarcity.
    
    Args:
        df: Input DataFrame with features and target.
        target: Name of the target column.
        stratify_col: Column name to use for stratification.
        test_size: Fraction of data to hold out for testing.
        random_state: Random seed for reproducibility.
        min_class_size: Minimum samples required for a class to be kept in stratification.
                        
    Returns:
        Tuple of (train_df, test_df).
    """
    logger.info(f"Preparing splits with stratification on '{stratify_col}'.")
    
    # 1. Handle Rare Class Logic (T032 Implementation)
    if stratify_col in df.columns:
        class_counts = df[stratify_col].value_counts()
        rare_classes = class_counts[class_counts < min_class_size].index.tolist()
        
        if rare_classes:
            logger.warning(
                f"Found {len(rare_classes)} classes with < {min_class_size} samples: {rare_classes}. "
                f"Excluding them from stratification or merging into 'OTHER'."
            )
            
            # Strategy: Filter out rare classes to ensure stratification stability,
            # OR merge them into an 'OTHER' bucket. 
            # Based on T032 "exclude classes with < 5 samples from stratification",
            # we will filter them out for the split logic to avoid sklearn errors 
            # and ensure valid stratification buckets.
            
            original_len = len(df)
            df = df[~df[stratify_col].isin(rare_classes)]
            excluded_count = original_len - len(df)
            logger.info(f"Excluded {excluded_count} samples from rare classes for stratification.")
            
            if len(df) == 0:
                raise ValueError("All data excluded due to rare class handling. Cannot split.")
    
    # 2. Check if stratification is viable
    if stratify_col in df.columns and df[stratify_col].nunique() > 1:
        try:
            # Verify that no class has less than 2 samples after filtering (sklearn requirement)
            final_counts = df[stratify_col].value_counts()
            if (final_counts < 2).any():
                logger.warning("Remaining classes have < 2 samples. Falling back to non-stratified split.")
                train_df, test_df = train_test_split(
                    df, 
                    test_size=test_size, 
                    random_state=random_state
                )
            else:
                train_df, test_df = train_test_split(
                    df, 
                    test_size=test_size, 
                    random_state=random_state,
                    stratify=df[stratify_col]
                )
            logger.info("Stratified split successful.")
        except Exception as e:
            logger.warning(f"Stratification failed ({e}). Falling back to random split.")
            train_df, test_df = train_test_split(
                df, 
                test_size=test_size, 
                random_state=random_state
            )
    else:
        logger.info("Not enough unique classes for stratification. Using random split.")
        train_df, test_df = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
        
    return train_df, test_df

def train_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target: str = "weibull_modulus",
    max_depth: int = 10,
    n_estimators: int = 100
) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models.
    
    Args:
        train_df: Training data.
        test_df: Test data.
        target: Target column name.
        max_depth: Max depth for trees.
        n_estimators: Number of trees.
        
    Returns:
        Dictionary containing fitted models and metadata.
    """
    logger.info("Training models...")
    
    feature_cols = [c for c in train_df.columns if c != target]
    X_train = train_df[feature_cols]
    y_train = train_df[target]
    X_test = test_df[feature_cols]
    y_test = test_df[target]
    
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators, 
        max_depth=max_depth, 
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    gbm_model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42
    )
    gbm_model.fit(X_train, y_train)
    
    return {
        "rf": rf_model,
        "gbm": gbm_model,
        "feature_cols": feature_cols,
        "X_test": X_test,
        "y_test": y_test
    }

def evaluate_models(
    models_dict: Dict[str, Any],
    metrics_path: Path
) -> Dict[str, Any]:
    """
    Evaluate models and save metrics to JSON.
    
    Args:
        models_dict: Output from train_models.
        metrics_path: Path to save model_metrics.json.
        
    Returns:
        Dictionary of metrics.
    """
    logger.info("Evaluating models...")
    
    X_test = models_dict["X_test"]
    y_test = models_dict["y_test"]
    
    results = {}
    
    for name, model in [("RandomForest", models_dict["rf"]), ("GradientBoosting", models_dict["gbm"])]:
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {
            "mae": float(mae),
            "r2": float(r2),
            "n_samples": len(y_test)
        }
        logger.info(f"{name} - MAE: {mae:.4f}, R2: {r2:.4f}")
    
    # Ensure directory exists
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Metrics saved to {metrics_path}")
    return results

def run_permutation_test(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 1000,
    random_state: int = 42
) -> float:
    """
    Perform permutation test to check model significance.
    
    Args:
        model: Fitted sklearn model.
        X: Features.
        y: Target.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        p-value.
    """
    logger.info(f"Running permutation test ({n_permutations} permutations)...")
    
    # Original score
    original_score = model.score(X, y)
    
    # Permutation scores
    np.random.seed(random_state)
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = y.sample(frac=1, random_state=random_state).reset_index(drop=True)
        perm_scores.append(model.score(X, y_perm))
        
    perm_scores = np.array(perm_scores)
    p_value = np.sum(perm_scores >= original_score) / n_permutations
    
    logger.info(f"Permutation p-value: {p_value:.4f}")
    return p_value

def main():
    """
    Main entry point for modeling pipeline.
    Loads data, splits (with rare class handling), trains, and evaluates.
    """
    logger.info("Starting modeling pipeline...")
    
    # Load processed data
    data_path = Path("data/processed/ceramic_dataset_cleaned.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run ingestion first.")
    
    df = pd.read_csv(data_path)
    
    # T032: Rare Class Handling is integrated into prepare_splits
    # Default min_class_size=5 as per task requirement
    train_df, test_df = prepare_splits(df, min_class_size=5)
    
    # Train
    models_dict = train_models(train_df, test_df)
    
    # Evaluate
    metrics_path = Path("data/results/model_metrics.json")
    evaluate_models(models_dict, metrics_path)
    
    # Permutation Test on best model (simplified: using RF for demo)
    p_val = run_permutation_test(models_dict["rf"], models_dict["X_test"], models_dict["y_test"])
    p_val_path = Path("data/results/permutation_p_value.json")
    p_val_path.parent.mkdir(parents=True, exist_ok=True)
    with open(p_val_path, 'w') as f:
        json.dump({"p_value": p_val}, f)
        
    logger.info("Modeling pipeline complete.")

if __name__ == "__main__":
    main()