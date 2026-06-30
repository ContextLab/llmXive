import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV, RidgeCV
from sklearn.model_selection import KFold, LeaveOneOut, cross_val_score
from sklearn.metrics import r2_score
import yaml

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)

def load_processed_data(config: Any) -> pd.DataFrame:
    """
    Load the processed features dataset from disk.
    Expects the file at config.paths.processed_features (derived from data/processed/features.csv).
    """
    input_path = Path("data/processed/features.csv")
    if not input_path.exists():
        logger.error(f"Processed features file not found at {input_path}. Run preprocessing pipeline first.")
        raise FileNotFoundError(f"Processed features file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def determine_cv_strategy(n_samples: int) -> Union[KFold, LeaveOneOut]:
    """
    Determine the Cross-Validation strategy based on sample size N.
    FR-005: 5-fold if N >= 30, LOOCV if N < 30.
    """
    if n_samples >= 30:
        logger.info(f"N={n_samples} >= 30. Using 5-fold Cross Validation.")
        return KFold(n_splits=5, shuffle=True, random_state=42)
    else:
        logger.info(f"N={n_samples} < 30. Using Leave-One-Out Cross Validation.")
        return LeaveOneOut()

def check_study_covariate_condition(df: pd.DataFrame) -> bool:
    """
    Check if unique_studies >= N-1.
    If true, the 'source_study' covariate should be excluded during training (handled by caller).
    Returns True if the condition is met (meaning we should exclude the covariate).
    """
    n = len(df)
    if 'source_study' not in df.columns:
        logger.warning("Column 'source_study' not found in dataframe. Assuming condition not met or column already handled.")
        return False
    
    unique_studies = df['source_study'].nunique()
    logger.info(f"Unique studies: {unique_studies}, N-1: {n-1}")
    
    condition_met = unique_studies >= (n - 1)
    if condition_met:
        logger.info(f"Condition met (unique_studies={unique_studies} >= N-1={n-1}). 'source_study' will be excluded as covariate.")
    else:
        logger.info(f"Condition NOT met. 'source_study' may be retained if present in features.")
    return condition_met

def train_model(
    df: pd.DataFrame, 
    target_col: str = 'compound_yield',
    feature_cols: Optional[List[str]] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a regularized regression model (LASSO or Ridge) using scikit-learn.
    
    Logic:
    1. Identify predictors (X) and target (y).
    2. Apply selected CV strategy (determined by N).
    3. If 'source_study' is in features and study condition is met, drop it.
    4. Train LassoCV (primary) with internal CV.
    5. Return the fitted model and metrics.
    """
    if feature_cols is None:
        # Default: all numeric columns except target
        feature_cols = [c for c in df.columns if c != target_col and df[c].dtype in ['int64', 'float64', 'int32', 'float32']]
    
    # Filter features to ensure they exist
    available_features = [c for c in feature_cols if c in df.columns]
    if len(available_features) == 0:
        raise ValueError("No valid feature columns found for training.")
    
    X = df[available_features].copy()
    y = df[target_col].copy()
    
    # Handle missing values in X or y
    if X.isnull().any().any() or y.isnull().any():
        logger.warning("Missing values detected in features or target. Dropping rows with NaN.")
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]
        if len(X) == 0:
            raise ValueError("No data remaining after dropping NaNs.")

    # Check study condition to potentially drop 'source_study'
    if 'source_study' in X.columns:
        # We need to check the condition on the original data structure, 
        # but here we assume the check was done or we re-evaluate on current subset.
        # Per T023 logic: if unique_studies >= N-1, exclude 'source_study'.
        unique_studies = X['source_study'].nunique()
        if unique_studies >= (len(X) - 1):
            logger.info("Dropping 'source_study' from features based on study condition.")
            X = X.drop(columns=['source_study'])
            if 'source_study' in available_features:
                available_features.remove('source_study')

    # Determine CV strategy based on current N
    cv_strategy = determine_cv_strategy(len(X))

    logger.info(f"Training model with {len(X)} samples and {X.shape[1]} features.")
    logger.info(f"Features: {available_features}")

    # Train LassoCV (automatically selects alpha via internal CV)
    # We use LassoCV as the primary model for feature selection (sparsity)
    model = LassoCV(
        cv=cv_strategy, 
        random_state=42, 
        n_jobs=-1,
        max_iter=10000
    )
    
    model.fit(X, y)
    
    # Calculate R2 on the training set (or use CV score from model)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # Extract best alpha
    best_alpha = model.alpha_
    
    # Calculate CV R2 scores if available from the internal CV
    # Note: model.scores_ might be available depending on sklearn version, 
    # but cross_val_score is more explicit if we need to re-run or verify.
    # For this task, we rely on the model's internal selection and final fit R2.
    
    metrics = {
        "r2_train": r2,
        "best_alpha": best_alpha,
        "n_samples": len(X),
        "n_features": X.shape[1],
        "cv_strategy": "KFold(5)" if len(X) >= 30 else "LOOCV"
    }
    
    logger.info(f"Model trained. R2: {r2:.4f}, Best Alpha: {best_alpha:.6f}")
    
    return model, metrics

def main():
    """
    Main entry point for T024: Train LASSO/Ridge model.
    1. Load config.
    2. Load processed data.
    3. Check study condition (T023 logic).
    4. Train model.
    5. Save model and metrics.
    """
    config = get_config()
    logger.info("Starting T024: Model Training Pipeline")
    
    try:
        # 1. Load Data
        df = load_processed_data(config)
        
        # 2. Check Study Covariate Condition (T023)
        # This ensures we drop 'source_study' if the condition is met
        check_study_covariate_condition(df)
        
        # 3. Train Model
        model, metrics = train_model(df)
        
        # 4. Save Outputs
        # Save model coefficients and metrics to data/processed/model_results.yaml
        output_path = Path("data/processed/model_results.yaml")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare coefficients for saving
        coefficients = dict(zip(model.feature_names_in_, model.coef_))
        
        results = {
            "metrics": metrics,
            "coefficients": coefficients,
            "model_type": "LassoCV"
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(results, f, default_flow_style=False)
        
        logger.info(f"Model results saved to {output_path}")
        
        # Print summary
        print(f"Training Complete.")
        print(f"  R2 Score: {metrics['r2_train']:.4f}")
        print(f"  Best Alpha: {metrics['best_alpha']:.6f}")
        print(f"  Top 5 Features by |Coeff|:")
        sorted_coefs = sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        for feat, coef in sorted_coefs:
            print(f"    {feat}: {coef:.6f}")
            
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()