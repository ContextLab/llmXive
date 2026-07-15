"""
Model Training Module.
Loads data, determines CV strategy, trains LASSO/Ridge models, and extracts predictors.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
from sklearn.preprocessing import StandardScaler

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)
PROCESSED_DIR = Path("data/processed")

def load_processed_data() -> pd.DataFrame:
    """Loads the final processed features."""
    path = PROCESSED_DIR / "features_final.csv"
    if not path.exists():
        # Fallback to filtered.csv if features_final not created
        path = PROCESSED_DIR / "filtered.csv"
    return pd.read_csv(path)

def determine_cv_strategy(n_samples: int) -> Union[KFold, LeaveOneOut]:
    """
    Determines CV strategy based on sample size.
    5-fold if N >= 30, LOOCV if N < 30.
    """
    if n_samples >= 30:
        return KFold(n_splits=5, shuffle=True, random_state=42)
    else:
        return LeaveOneOut()

def check_study_covariate_condition(df: pd.DataFrame) -> bool:
    """
    Checks if unique_studies >= N-1.
    Returns True if condition is met (global Z-score mode).
    """
    if 'source_study' not in df.columns:
        return False
    unique_studies = df['source_study'].nunique()
    n = len(df)
    return unique_studies >= (n - 1)

def train_model(X: np.ndarray, y: np.ndarray, cv_strategy) -> Tuple[Any, float]:
    """
    Trains a LASSO/Ridge model with cross-validation.
    Returns the best model and mean CV score.
    """
    # Try Lasso first
    model = Lasso(alpha=0.1, random_state=42, max_iter=10000)
    
    try:
        scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='r2')
        mean_score = np.mean(scores)
        logger.info(f"Lasso CV R2: {mean_score:.4f}")
        model.fit(X, y)
        return model, mean_score
    except Exception as e:
        logger.warning(f"Lasso failed: {e}. Trying Ridge.")
        model = Ridge(alpha=1.0, random_state=42)
        scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='r2')
        mean_score = np.mean(scores)
        logger.info(f"Ridge CV R2: {mean_score:.4f}")
        model.fit(X, y)
        return model, mean_score

def extract_top_predictors(model, feature_names: List[str], top_n: int = 10) -> List[Tuple[str, float]]:
    """
    Extracts top predictors by absolute coefficient magnitude.
    """
    coefs = model.coef_
    if len(coefs) != len(feature_names):
        logger.warning("Coefficient count mismatch.")
        return []
    
    abs_coefs = np.abs(coefs)
    indices = np.argsort(abs_coefs)[::-1][:top_n]
    
    predictors = []
    for i in indices:
        predictors.append((feature_names[i], coefs[i]))
    
    return predictors

def main():
    """
    Entry point for training script.
    Loads data, trains model, saves results.
    """
    from utils.logging import configure_root_logger
    configure_root_logger()
    
    logger.info("Starting model training.")
    
    df = load_processed_data()
    
    # Prepare features and target
    # Target: mean_concentration
    # Features: all numeric except IDs and target
    target_col = 'mean_concentration'
    if target_col not in df.columns:
        logger.error(f"Target column {target_col} not found.")
        return

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col and c != 'population_id']
    
    if not feature_cols:
        logger.error("No features found.")
        return

    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle NaNs
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    if len(X) == 0:
        logger.error("No valid samples after NaN removal.")
        return

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # CV Strategy
    cv = determine_cv_strategy(len(X))
    
    # Train
    model, score = train_model(X_scaled, y, cv)
    
    # Extract predictors
    predictors = extract_top_predictors(model, feature_cols)
    logger.info("Top predictors:")
    for name, coef in predictors:
        logger.info(f"  {name}: {coef:.4f}")
    
    logger.info("Training completed.")

if __name__ == "__main__":
    main()
