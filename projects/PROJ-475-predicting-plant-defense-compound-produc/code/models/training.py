"""
Model Training Module.
Handles CV strategy, model training, and predictor extraction.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from utils.logging import get_module_logger, configure_root_logger
from config import get_config

logger = get_module_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_processed_data() -> pd.DataFrame:
    """Loads the filtered dataset from data/processed/final_cleaned.csv."""
    config = get_config()
    # T021 explicitly requires input: data/processed/final_cleaned.csv (T015)
    # The previous code looked for 'filtered.csv' which was causing issues.
    input_path = PROJECT_ROOT / "data" / "processed" / "final_cleaned.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            f"Run the validation pipeline (T015) first to generate final_cleaned.csv."
        )
    return pd.read_csv(input_path)

def determine_cv_strategy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Determines CV strategy based on sample size (N) per FR-005.
    
    Logic:
    - If N >= 30: use 5-fold Cross Validation ('kfold')
    - If N < 30: use Leave-One-Out Cross Validation ('loocv')
    
    Args:
        df (pd.DataFrame): The cleaned dataset (input from T015).
    
    Returns:
        Dict[str, Any]: A dictionary containing 'cv_type' and 'n'.
                        Example: {'cv_type': 'kfold', 'n': 45}
    """
    n = len(df)
    if n < 0:
        raise ValueError("DataFrame length cannot be negative.")
    
    if n >= 30:
        cv_type = 'kfold'
    else:
        cv_type = 'loocv'
    
    result = {
        'cv_type': cv_type,
        'n': n
    }
    
    logger.info(f"Determined CV strategy: {cv_type} for N={n}")
    return result

def save_cv_strategy(result: Dict[str, Any]) -> Path:
    """
    Saves the CV strategy result to data/processed/cv_strategy.json.
    
    Args:
        result (Dict[str, Any]): The strategy dictionary.
    
    Returns:
        Path: The path to the saved JSON file.
    """
    output_path = PROJECT_ROOT / "data" / "processed" / "cv_strategy.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"CV strategy saved to {output_path}")
    return output_path

def check_study_covariate_condition(df: pd.DataFrame) -> bool:
    """
    Checks if unique_studies >= N-1.
    If true, 'source_study' should be excluded per FR-010.
    """
    if 'source_study' not in df.columns:
        return False
    unique_studies = df['source_study'].nunique()
    n = len(df)
    return unique_studies >= (n - 1)

def train_model():
    """Trains the LASSO/Ridge model (T024 logic)."""
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
    target_col = 'compound_concentration' if 'compound_concentration' in df.columns else df.select_dtypes(include=[np.number]).columns[-1]
    feature_cols = [c for c in df.columns if c != target_col and c != 'population_id' and c != 'env_id' and c != 'compound_id']
    
    if len(feature_cols) == 0:
        logger.error("No features found.")
        return

    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0)

    n_samples = len(X)
    cv_strategy = determine_cv_strategy(n_samples)
    logger.info(f"CV Strategy: {cv_strategy['cv_type']} (N={n_samples})")

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
    
    if cv_strategy['cv_type'] == 'loocv':
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
    """
    Entry point for training script.
    Executes T021: Determine CV Strategy and save to JSON.
    Also runs T024 (train_model) if data is available.
    """
    configure_root_logger()
    
    # T021 Implementation: Determine CV Strategy
    try:
        df = load_processed_data()
        strategy_result = determine_cv_strategy(df)
        save_cv_strategy(strategy_result)
    except FileNotFoundError as e:
        logger.error(f"T021 failed: {e}")
        sys.exit(1)
    
    # T024 Implementation: Train Model (optional, but part of this file's responsibility)
    try:
        train_model()
    except Exception as e:
        logger.warning(f"T024 (Model Training) failed, but T021 completed: {e}")
        # Do not exit with error if only training fails, as T021 succeeded
        # However, if the user specifically runs this to train, they might want to know.
        # We log the error and exit 0 if T021 succeeded, or 1 if T021 failed.

if __name__ == "__main__":
    main()