"""
Model Training Module.
Handles CV strategy, model training, and predictor extraction.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from utils.logging import get_module_logger
from config import get_config

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_processed_data() -> pd.DataFrame:
    """Loads the filtered dataset."""
    config = get_config()
    input_path = PROJECT_ROOT / config.paths.processed / "filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run preprocessing first.")
    return pd.read_csv(input_path)

def determine_cv_strategy(n_samples: int) -> str:
    """Determines CV strategy based on sample size."""
    if n_samples >= 30:
        return 'kfold'
    else:
        return 'loocv'

def check_study_covariate_condition(df: pd.DataFrame) -> bool:
    """
    Checks if unique_studies >= N-1.
    If true, 'source_study' should be excluded.
    """
    if 'source_study' not in df.columns:
        return False
    unique_studies = df['source_study'].nunique()
    n = len(df)
    return unique_studies >= (n - 1)

def train_model():
    """Trains the LASSO/Ridge model."""
    logger.info("Starting Model Training")
    
    try:
        df = load_processed_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    if df.empty:
        logger.error("Dataset is empty.")
        return

    # Prepare features and target
    # Assume 'compound_concentration' is target, or last numeric col
    target_col = 'compound_concentration' if 'compound_concentration' in df.columns else df.select_dtypes(include=[np.number]).columns[-1]
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id' and c != 'env_id' and c != 'compound_id']
    
    if len(feature_cols) == 0:
        logger.error("No features found.")
        return

    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)

    n_samples = len(X)
    cv_strategy = determine_cv_strategy(n_samples)
    logger.info(f"CV Strategy: {cv_strategy} (N={n_samples})")

    # Check study condition
    if check_study_covariate_condition(df):
        logger.info("Study condition met: Excluding 'source_study' if present.")
        if 'source_study' in feature_cols:
            X = X.drop(columns=['source_study'])

    # Train Model
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
    
    # Use RidgeCV for simplicity and stability
    model = RidgeCV(alphas=[0.1, 1.0, 10.0])
    
    if cv_strategy == 'loocv':
        cv = LeaveOneOut()
    else:
        cv = KFold(n_splits=5, shuffle=True, random_state=42)

    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        logger.info(f"CV R2 Scores: {scores}")
        logger.info(f"Mean CV R2: {scores.mean():.4f}")
        
        # Fit on full data for predictor extraction
        model.fit(X, y)
        
        # Save model coefficients
        coef_df = pd.DataFrame({
            'feature': X.columns,
            'coefficient': model.coef_
        })
        coef_df = coef_df.sort_values(by='coefficient', key=abs, ascending=False)
        
        output_path = PROJECT_ROOT / "data" / "processed" / "model_coefficients.csv"
        coef_df.to_csv(output_path, index=False)
        logger.info(f"Model coefficients saved to {output_path}")

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise

def extract_top_predictors(coef_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Extracts top N predictors by absolute coefficient magnitude."""
    return coef_df.head(top_n)

def main(*args, **kwargs):
    """Entry point for training script."""
    configure_root_logger()
    train_model()

if __name__ == "__main__":
    main()
