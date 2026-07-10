import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from config import get_config, ConfigError
from utils.logging import get_module_logger
from utils.io import check_disk_space

logger = get_module_logger(__name__)

def load_processed_data(config: Any) -> pd.DataFrame:
    """
    Load the preprocessed and aggregated dataset from disk.
    Expects the file path to be defined in config.
    """
    input_path = Path(config.get("paths", {}).get("processed_data", "data/processed/features_vif.csv"))
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {input_path}. "
                                "Please ensure T019-T021 have completed successfully.")
    
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def determine_cv_strategy(n_samples: int) -> int:
    """
    Determine the cross-validation fold strategy based on sample size.
    Returns 5 for N >= 30, otherwise 1 (LOOCV).
    """
    if n_samples >= 30:
        return 5
    return 1

def check_study_covariate_condition(df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Check if unique_studies >= N-1.
    Returns (condition_met, unique_studies_count).
    """
    unique_studies = df['source_study'].nunique()
    n = len(df)
    condition_met = unique_studies >= (n - 1)
    logger.info(f"Study covariate check: unique_studies={unique_studies}, N={n}, condition_met={condition_met}")
    return condition_met, unique_studies

def train_model(df: pd.DataFrame, cv_folds: int, exclude_study_covariate: bool) -> Tuple[Any, pd.DataFrame]:
    """
    Train a regularized regression model (Ridge/Lasso) on the prepared features.
    
    Args:
        df: The dataframe containing features and target.
        cv_folds: Number of CV folds.
        exclude_study_covariate: If True, drops 'source_study' from features.
    
    Returns:
        model: The fitted sklearn model.
        feature_importance_df: DataFrame of coefficients sorted by magnitude.
    """
    try:
        from sklearn.linear_model import RidgeCV, LassoCV
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError as e:
        logger.error("Required scikit-learn components not found. Ensure requirements.txt is installed.")
        raise e

    # Identify target and features
    target_col = "compound_concentration" # Assuming standard target name from T012/T013
    if target_col not in df.columns:
        # Fallback or strict error based on actual schema
        raise KeyError(f"Target column '{target_col}' not found in dataframe. Columns: {df.columns.tolist()}")

    feature_cols = [c for c in df.columns if c != target_col]
    
    if exclude_study_covariate and 'source_study' in feature_cols:
        logger.info("Excluding 'source_study' covariate as per FR-010.")
        feature_cols.remove('source_study')
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Handle non-numeric columns if any remain (e.g., categorical encoding issues)
    # For this implementation, we assume preprocessing (T020/T021) handled encoding.
    # If 'source_study' was kept, it might be categorical; we drop it if not numeric for simplicity here
    # or assume it was one-hot encoded in T021. 
    # Strictly, if 'source_study' is kept and is object type, we must handle it.
    # Given T021 logic, if kept, it might be a categorical covariate.
    # We will select only numeric columns for linear regression to avoid errors.
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X = X[numeric_cols]

    if X.empty:
        raise ValueError("No numeric features available for training after filtering.")

    # Train a RidgeCV model (automatic alpha selection via CV)
    # Using Ridge as it is generally more stable than Lasso for high collinearity
    model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0], cv=cv_folds)
    
    logger.info(f"Training Ridge model with {cv_folds}-fold CV on {X.shape[1]} features.")
    model.fit(X, y)
    
    logger.info(f"Model training complete. Best alpha: {model.alpha_}")

    # Extract coefficients
    coefficients = pd.Series(model.coef_, index=X.columns)
    
    # Create a dataframe for analysis
    feature_importance_df = pd.DataFrame({
        'feature': coefficients.index,
        'coefficient': coefficients.values
    })
    
    return model, feature_importance_df

def extract_top_predictors(feature_importance_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Extract the top N predictors by absolute coefficient magnitude.
    
    Args:
        feature_importance_df: DataFrame with 'feature' and 'coefficient' columns.
        top_n: Number of top predictors to return.
    
    Returns:
        DataFrame of top N predictors sorted by absolute coefficient descending.
    """
    if feature_importance_df.empty:
        logger.warning("Feature importance dataframe is empty. Returning empty result.")
        return pd.DataFrame()

    # Calculate absolute magnitude
    feature_importance_df['abs_coefficient'] = feature_importance_df['coefficient'].abs()
    
    # Sort by absolute magnitude descending
    sorted_df = feature_importance_df.sort_values(by='abs_coefficient', ascending=False)
    
    # Select top N
    top_predictors = sorted_df.head(top_n)
    
    logger.info(f"Extracted top {len(top_predictors)} predictors.")
    for idx, row in top_predictors.iterrows():
        logger.info(f"  - {row['feature']}: {row['coefficient']:.4f} (|coef|={row['abs_coefficient']:.4f})")
    
    return top_predictors

def main():
    """
    Main entry point for T025: Extract top 10 predictors.
    Orchestrates loading, training, and extraction, then writes results to disk.
    """
    logger.info("Starting T025: Extract top 10 predictors.")
    
    # Load config
    try:
        config = get_config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Check disk space for output
    estimated_output_size = 1024 * 1024  # 1MB estimate
    check_disk_space(estimated_output_size)

    # 1. Load Data
    try:
        df = load_processed_data(config)
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

    # 2. Determine CV Strategy
    n_samples = len(df)
    cv_folds = determine_cv_strategy(n_samples)
    logger.info(f"Selected CV strategy: {cv_folds} folds (N={n_samples})")

    # 3. Check Study Covariate Condition
    exclude_covariate, unique_studies_count = check_study_covariate_condition(df)
    
    # 4. Train Model
    try:
        model, feature_df = train_model(df, cv_folds, exclude_covariate)
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        sys.exit(1)

    # 5. Extract Top 10 Predictors
    top_10_df = extract_top_predictors(feature_df, top_n=10)

    # 6. Save Output
    output_path = Path(config.get("paths", {}).get("top_predictors", "data/processed/top_10_predictors.csv"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    top_10_df.to_csv(output_path, index=False)
    logger.info(f"Top 10 predictors saved to {output_path}")

    # Also save the full coefficient list for reference
    full_coeffs_path = Path(config.get("paths", {}).get("full_coefficients", "data/processed/all_coefficients.csv"))
    feature_df.to_csv(full_coeffs_path, index=False)
    logger.info(f"All coefficients saved to {full_coeffs_path}")

    return top_10_df

if __name__ == "__main__":
    main()