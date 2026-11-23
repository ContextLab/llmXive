"""
Preprocessing module for the Cyberbullying Survey analysis.
Handles MICE imputation, scale scoring, and derivation of binary exposure.
"""
import os
import sys
import logging
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config_loader import load_yaml_config, get_seed

logger = get_logger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = project_root / "code" / "config" / "data_sources.yaml"
    return load_yaml_config(config_path)

def apply_mice_imputation(
    df: pd.DataFrame,
    predictor_cols: List[str],
    max_iter: int = 10,
    random_state: int = 42
) -> Tuple[pd.DataFrame, bool]:
    """
    Apply Multiple Imputation by Chained Equations (MICE) to missing values.
    
    Args:
        df: Input DataFrame
        predictor_cols: List of columns to impute
        max_iter: Maximum number of iterations
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (imputed DataFrame, convergence status)
    """
    logger.info(f"Applying MICE imputation to columns: {predictor_cols}")
    
    # Filter to only the predictor columns
    df_predictors = df[predictor_cols].copy()
    
    # Check for any missing values
    if df_predictors.isnull().sum().sum() == 0:
        logger.info("No missing values in predictor matrix. Skipping imputation.")
        return df, True
    
    try:
        from sklearn.experimental import enable_iterative_imputer
        from sklearn.impute import IterativeImputer
    except ImportError:
        logger.error("scikit-learn is required for MICE imputation.")
        raise RuntimeError("scikit-learn not found. Install with: pip install scikit-learn")
    
    # Initialize the imputer with explicit parameters
    imputer = IterativeImputer(
        max_iter=max_iter,
        random_state=random_state,
        verbose=1
    )
    
    # Fit and transform
    logger.info("Fitting IterativeImputer...")
    imputed_values = imputer.fit_transform(df_predictors)
    
    # Check convergence
    if hasattr(imputer, 'n_iter_'):
        converged = imputer.n_iter_ < max_iter
        logger.info(f"Imputation converged: {converged} (iterations: {imputer.n_iter_})")
    else:
        # Fallback: assume convergence if no error
        converged = True
        logger.warning("Could not determine convergence status. Assuming success.")
    
    # Update the original DataFrame
    df_imputed = df.copy()
    df_imputed[predictor_cols] = imputed_values
    
    return df_imputed, converged

def check_convergence(converged: bool) -> None:
    """
    Check if MICE imputation converged and raise error if not.
    
    Args:
        converged: Boolean indicating if imputation converged
        
    Raises:
        RuntimeError: If imputation did not converge
    """
    if not converged:
        error_msg = "E-MICE-NONCONV-001: MICE imputation failed to converge. Halting pipeline."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    logger.info("MICE imputation converged successfully.")

def apply_scale_scoring(
    df: pd.DataFrame,
    config_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Apply scoring algorithms defined in config/scales.yaml.
    
    Args:
        df: Input DataFrame
        config_path: Path to scales configuration
        
    Returns:
        DataFrame with scored variables
    """
    if config_path is None:
        config_path = project_root / "code" / "config" / "scales.yaml"
    
    config = load_yaml_config(config_path)
    logger.info(f"Loaded scale config: {list(config.keys())}")
    
    # Check if raw items exist or if we have pre-aggregated scores
    # For CES-D (depression)
    if 'depression' in df.columns:
        logger.info("Using pre-aggregated 'depression' column from dataset.")
        logger.warning("W-AGGREGATE-SCORES-001: Using pre-aggregated scores from dataset.")
    else:
        # Check for raw items (e.g., cesd_1, cesd_2, etc.)
        raw_cols = [col for col in df.columns if col.startswith('cesd_')]
        if raw_cols:
            logger.info(f"Scoring CES-D from {len(raw_cols)} raw items.")
            # Simple sum of raw items (assuming 0-3 or 0-4 scale)
            df['depression'] = df[raw_cols].sum(axis=1)
        else:
            logger.warning("W-PCL5-MISSING: No depression data found. Skipping.")
    
    # For GAD-7 (anxiety)
    if 'anxiety' in df.columns:
        logger.info("Using pre-aggregated 'anxiety' column from dataset.")
        logger.warning("W-AGGREGATE-SCORES-001: Using pre-aggregated scores from dataset.")
    else:
        raw_cols = [col for col in df.columns if col.startswith('gad_')]
        if raw_cols:
            logger.info(f"Scoring GAD-7 from {len(raw_cols)} raw items.")
            df['anxiety'] = df[raw_cols].sum(axis=1)
        else:
            logger.warning("W-PCL5-MISSING: No anxiety data found. Skipping.")
    
    # For PCL-5 (PTSD) - Optional
    if 'ptsd' in df.columns:
        logger.info("Using pre-aggregated 'ptsd' column from dataset.")
        logger.warning("W-AGGREGATE-SCORES-001: Using pre-aggregated scores from dataset.")
    else:
        raw_cols = [col for col in df.columns if col.startswith('pcl_')]
        if raw_cols:
            logger.info(f"Scoring PCL-5 from {len(raw_cols)} raw items.")
            df['ptsd'] = df[raw_cols].sum(axis=1)
        else:
            logger.warning("W-PCL5-MISSING: No PTSD data found. Proceeding without it.")
    
    return df

def apply_binary_exposure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive the binary 'harassment_exposure' variable from the imputed 'harassment_severity'.
    
    Logic: exposure = 1 if severity > 0 else 0
    
    Args:
        df: Input DataFrame with 'harassment_severity' column
        
    Returns:
        DataFrame with new 'harassment_exposure' column
    """
    logger.info("Deriving binary harassment_exposure from harassment_severity.")
    
    if 'harassment_severity' not in df.columns:
        raise ValueError("E-NO-SEVERITY-001: 'harassment_severity' column not found in DataFrame.")
    
    # Create binary exposure: 1 if severity > 0, else 0
    df['harassment_exposure'] = (df['harassment_severity'] > 0).astype(int)
    
    # Log distribution
    exposure_dist = df['harassment_exposure'].value_counts().sort_index()
    logger.info(f"Harassment exposure distribution:\n{exposure_dist}")
    
    return df

def handle_outcome_missingness(df: pd.DataFrame, outcome_cols: List[str]) -> pd.DataFrame:
    """
    Perform listwise deletion on rows where critical outcome variables are missing.
    
    Args:
        df: Input DataFrame
        outcome_cols: List of outcome columns to check (e.g., ['depression', 'anxiety', 'ptsd'])
        
    Returns:
        DataFrame with rows containing missing outcomes removed
    """
    logger.info(f"Checking for missing outcomes in: {outcome_cols}")
    
    # Filter to only existing outcome columns
    existing_outcomes = [col for col in outcome_cols if col in df.columns]
    
    if not existing_outcomes:
        logger.warning("No outcome columns found. Skipping outcome missingness check.")
        return df
    
    initial_count = len(df)
    df_clean = df.dropna(subset=existing_outcomes)
    final_count = len(df_clean)
    
    dropped = initial_count - final_count
    logger.info(f"Dropped {dropped} rows ({dropped/initial_count*100:.2f}%) with missing outcomes.")
    
    return df_clean

def run_preprocessing() -> pd.DataFrame:
    """
    Main preprocessing pipeline:
    1. Load raw data
    2. Apply MICE imputation to predictors
    3. Check convergence
    4. Apply scale scoring
    5. Derive binary exposure
    6. Handle outcome missingness
    
    Returns:
        Cleaned and processed DataFrame
    """
    logger.info("Starting preprocessing pipeline.")
    
    # 1. Load raw data
    raw_path = project_root / "data" / "raw" / "cyberbullying_2021.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"E-NO-DATA-001: Raw data not found at {raw_path}")
    
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded {len(df)} rows from {raw_path}")
    
    # 2. Configure MICE imputation
    # Predictor matrix as defined in T013a-Config
    predictor_cols = ['age', 'gender', 'education', 'income', 'social_support', 'harassment_severity']
    
    # Check for platform column
    if 'platform' in df.columns:
        predictor_cols.append('platform')
        logger.info("Including 'platform' in predictor matrix.")
    else:
        logger.warning("W-NO-PLATFORM-001: 'platform' column not found. Excluding from predictor matrix.")
    
    # 3. Apply MICE imputation
    df_imputed, converged = apply_mice_imputation(
        df, 
        predictor_cols, 
        max_iter=10, 
        random_state=get_seed()
    )
    
    # 4. Check convergence
    check_convergence(converged)
    
    # 5. Apply scale scoring
    df_scored = apply_scale_scoring(df_imputed)
    
    # 6. Derive binary exposure (T013b)
    df_exposed = apply_binary_exposure(df_scored)
    
    # 7. Handle outcome missingness (T013d)
    outcome_cols = ['depression', 'anxiety', 'ptsd']
    df_clean = handle_outcome_missingness(df_exposed, outcome_cols)
    
    logger.info(f"Preprocessing complete. Final cohort size: {len(df_clean)}")
    return df_clean

def main():
    """Entry point for preprocessing script."""
    try:
        df = run_preprocessing()
        
        # Save intermediate results
        output_path = project_root / "data" / "results" / "preprocessed_cohort.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved preprocessed cohort to {output_path}")
        
        return df
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
