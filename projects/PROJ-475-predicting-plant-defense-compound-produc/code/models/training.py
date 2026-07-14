import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)

def load_processed_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the preprocessed features dataframe from disk.
    Expects the file at data/processed/features_vif.csv as per T020.
    """
    data_path = Path(config['paths']['processed_features'])
    if not data_path.exists():
        raise FileNotFoundError(f"Processed features file not found at {data_path}")
    
    logger.info(f"Loading processed features from {data_path}")
    df = pd.read_csv(data_path)
    return df

def determine_cv_strategy(n_samples: int) -> str:
    """
    Determine cross-validation strategy based on sample size.
    FR-005: 5-fold if N>=30, LOOCV if N<30.
    """
    if n_samples >= 30:
        return 'kfold'
    else:
        return 'leave_one_out'

def check_study_covariate_condition(df: pd.DataFrame) -> bool:
    """
    Check if unique_studies >= N-1.
    If true, the 'source_study' covariate should be excluded during training (FR-010).
    Returns True if condition is met.
    """
    n = len(df)
    if 'source_study' not in df.columns:
        return False
    
    unique_studies = df['source_study'].nunique()
    condition_met = unique_studies >= (n - 1)
    logger.info(f"Study covariate check: unique_studies={unique_studies}, N-1={n-1}, condition_met={condition_met}")
    return condition_met

def train_model(df: pd.DataFrame, target_col: str, cv_strategy: str, exclude_study_cov: bool = False) -> Tuple[Any, Dict[str, float]]:
    """
    Train a LASSO/Ridge model using scikit-learn.
    
    Args:
        df: DataFrame with features and target.
        target_col: Name of the target column.
        cv_strategy: 'kfold' or 'leave_one_out'.
        exclude_study_cov: If True, remove 'source_study' column before training.
        
    Returns:
        Tuple of (fitted model, dict of coefficients)
    """
    from sklearn.linear_model import ElasticNet
    from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    # Prepare data
    X = df.drop(columns=[target_col])
    y = df[target_col]

    if exclude_study_cov and 'source_study' in X.columns:
        X = X.drop(columns=['source_study'])
        logger.info("Excluded 'source_study' covariate per FR-010 condition.")

    # Select CV splitter
    if cv_strategy == 'kfold':
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
    else:
        cv = LeaveOneOut()

    # Create pipeline: Standardize then fit ElasticNet (Lasso/Ridge mix)
    # Using ElasticNet with high l1_ratio for Lasso-like behavior as per T024 context
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', ElasticNet(alpha=0.1, l1_ratio=0.9, random_state=42, max_iter=5000))
    ])

    # Fit the model
    logger.info("Training model...")
    pipeline.fit(X, y)

    # Extract coefficients
    # The model is inside the pipeline steps
    model = pipeline.named_steps['model']
    feature_names = X.columns.tolist()
    coefficients = dict(zip(feature_names, model.coef_))

    logger.info(f"Model trained. Non-zero coefficients: {sum(1 for c in coefficients.values() if c != 0)}")
    return pipeline, coefficients

def extract_top_predictors(coefficients: Dict[str, float], n_top: int = 10) -> List[Tuple[str, float]]:
    """
    Extract the top N predictors by absolute coefficient magnitude.
    
    Args:
        coefficients: Dictionary mapping feature names to coefficient values.
        n_top: Number of top predictors to return (default 10).
        
    Returns:
        List of tuples (feature_name, coefficient) sorted by absolute value descending.
    """
    # Sort by absolute value descending
    sorted_predictors = sorted(
        coefficients.items(),
        key=lambda item: abs(item[1]),
        reverse=True
    )
    
    # Return top N
    top_predictors = sorted_predictors[:n_top]
    
    logger.info(f"Extracted top {len(top_predictors)} predictors:")
    for name, coef in top_predictors:
        logger.info(f"  {name}: {coef:.4f} (|coef|: {abs(coef):.4f})")
        
    return top_predictors

def main():
    """
    Main entry point for T025: Extract top 10 predictors.
    Orchestrates loading, training, and extraction.
    """
    config = get_config()
    
    # Check disk space
    try:
        check_disk_space(estimated_size=1024*1024*100) # 100MB buffer
    except DiskSpaceError as e:
        logger.error(str(e))
        sys.exit(1)

    # Load data
    try:
        df = load_processed_data(config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if df.empty:
        logger.error("Loaded dataframe is empty.")
        sys.exit(1)

    # Determine CV strategy
    n_samples = len(df)
    cv_strategy = determine_cv_strategy(n_samples)
    logger.info(f"Selected CV strategy: {cv_strategy} for N={n_samples}")

    # Check study condition
    exclude_study = check_study_covariate_condition(df)

    # Define target (assumed to be 'compound_concentration' or similar based on spec context)
    # The spec implies a target exists in the processed data. We look for a likely column.
    target_candidates = ['compound_concentration', 'defense_level', 'target']
    target_col = None
    for cand in target_candidates:
        if cand in df.columns:
            target_col = cand
            break
    
    if target_col is None:
        # Fallback: assume the last column is the target if not named conventionally
        # This is a heuristic to ensure the script runs on generated data
        target_col = df.columns[-1]
        logger.warning(f"Target column not found in standard names, using '{target_col}' as target.")

    # Train model
    model, coefficients = train_model(df, target_col, cv_strategy, exclude_study)

    # Extract top 10 predictors
    top_10 = extract_top_predictors(coefficients, n_top=10)

    # Save results to data/processed/top_predictors.csv
    output_path = Path(config['paths']['data_processed']) / 'top_predictors.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results_df = pd.DataFrame(top_10, columns=['predictor', 'coefficient'])
    results_df.to_csv(output_path, index=False)
    
    logger.info(f"Top 10 predictors saved to {output_path}")
    
    return top_10

if __name__ == '__main__':
    main()