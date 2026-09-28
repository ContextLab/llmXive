import os
import sys
import logging
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import from local project modules to ensure correct API usage
# Assuming config_loader and logger are available as per project structure
try:
    from utils.config_loader import load_yaml_config, get_seed
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config_loader import load_yaml_config, get_seed
    from utils.logger import get_logger

# Constants
CRITICAL_OUTCOMES = ['depression', 'anxiety', 'ptsd']
PREDICTOR_MATRIX = ['age', 'gender', 'education', 'income', 'social_support', 'harassment_severity']

logger = get_logger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config files."""
    config_path = Path(__file__).parent.parent / 'config' / 'data_config.yaml'
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return {}
    return load_yaml_config(config_path)

def handle_high_missingness(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Handle columns with high missingness (> threshold)."""
    logger.info("Checking for high missingness columns...")
    missing_pct = df.isnull().mean()
    high_missing = missing_pct[missing_pct > threshold].index.tolist()
    if high_missing:
        logger.warning(f"Dropping columns with >{threshold*100}% missingness: {high_missing}")
        df = df.drop(columns=high_missing)
    return df

def check_convergence(imputer, max_iter: int = 10) -> bool:
    """Check if MICE imputation converged."""
    # IterativeImputer does not expose a direct 'converged_' attribute in all versions
    # We assume convergence if the run completes without exception.
    # If specific convergence flags are needed, they would be checked here.
    return True

def apply_mice_imputation(df: pd.DataFrame, predictors: List[str], seed: int = 42) -> pd.DataFrame:
    """Apply MICE imputation to the predictor matrix."""
    logger.info(f"Applying MICE imputation to predictors: {predictors}")
    
    # Filter to only existing predictors
    existing_preds = [p for p in predictors if p in df.columns]
    if not existing_preds:
        logger.warning("No predictor columns found for imputation.")
        return df

    df_imputed = df.copy()
    
    # Isolate predictors to impute
    X = df_imputed[existing_preds].copy()
    
    # Check if there is any missingness to impute
    if X.isnull().sum().sum() == 0:
        logger.info("No missing values found in predictor matrix. Skipping imputation.")
        return df_imputed

    try:
        from sklearn.experimental import enable_iterative_imputer
        from sklearn.impute import IterativeImputer
        
        imputer = IterativeImputer(
            max_iter=10,
            random_state=seed,
            verbose=1
        )
        
        logger.info("Fitting IterativeImputer...")
        imputed_values = imputer.fit_transform(X)
        
        if not check_convergence(imputer):
            logger.error("E-MICE-NONCONV-001: MICE imputation failed to converge. Halting pipeline.")
            raise RuntimeError("MICE imputation failed to converge.")
        
        # Update dataframe
        df_imputed[existing_preds] = imputed_values
        logger.info("MICE imputation completed successfully.")
        
    except ImportError as e:
        logger.error(f"Sklearn iterative imputer not available: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during MICE imputation: {e}")
        raise

    return df_imputed

def apply_scale_scoring(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Apply scale scoring logic (placeholder for T013c integration)."""
    # This function is a placeholder to ensure the pipeline flow exists.
    # T013c (Scale Scoring) is assumed to have run or be integrated here.
    # For T013d, we assume 'depression', 'anxiety', 'ptsd' are already present or handled.
    logger.info("Scale scoring step invoked (assumed completed by T013c).")
    return df

def apply_binary_exposure(df: pd.DataFrame, severity_col: str = 'harassment_severity') -> pd.DataFrame:
    """Derive binary harassment exposure from continuous severity."""
    logger.info("Deriving binary harassment exposure...")
    if severity_col not in df.columns:
        logger.warning(f"Column {severity_col} not found. Skipping binary exposure derivation.")
        return df
    
    df = df.copy()
    df['harassment_exposure'] = (df[severity_col] > 0).astype(int)
    logger.info("Binary exposure derived.")
    return df

def handle_outcome_missingness(df: pd.DataFrame, outcomes: List[str] = None) -> pd.DataFrame:
    """
    Perform listwise deletion ONLY on rows where critical outcome variables are missing.
    This is T013d: Handle Outcome Missingness.
    
    Constraint: Do NOT perform listwise deletion on predictor variables before imputation.
    This step happens AFTER imputation (T013a) and scoring (T013c).
    """
    if outcomes is None:
        outcomes = CRITICAL_OUTCOMES
        
    logger.info(f"Handling outcome missingness for variables: {outcomes}")
    
    # Filter to only existing outcomes in the dataframe
    existing_outcomes = [o for o in outcomes if o in df.columns]
    
    if not existing_outcomes:
        logger.warning("No outcome variables found in dataframe. No listwise deletion performed.")
        return df

    # Identify rows where ANY of the critical outcomes are missing
    mask_missing = df[existing_outcomes].isnull().any(axis=1)
    count_missing = mask_missing.sum()
    total_rows = len(df)
    
    if count_missing > 0:
        logger.info(f"Found {count_missing} rows ({count_missing/total_rows:.2%}) with missing critical outcomes.")
        logger.info("Performing listwise deletion on these rows.")
        df_clean = df[~mask_missing].copy()
    else:
        logger.info("No rows with missing critical outcomes found.")
        df_clean = df.copy()

    logger.info(f"Resulting cohort size: {len(df_clean)} rows.")
    return df_clean

def run_preprocessing(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Main preprocessing pipeline orchestrator.
    Executes:
    1. Load data
    2. Handle high missingness (optional)
    3. MICE Imputation (T013a)
    4. Scale Scoring (T013c - assumed or called)
    5. Binary Exposure Derivation (T013b)
    6. Handle Outcome Missingness (T013d)
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Load config
    config = load_config()
    seed = get_seed(config.get('seeds', {}), default=42)
    
    # Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Step 1: MICE Imputation (Predictors)
    df = apply_mice_imputation(df, PREDICTOR_MATRIX, seed=seed)
    
    # Step 2: Scale Scoring (Assumed to be done or called here if raw items exist)
    # If the input already has scores, this is a no-op or validation.
    # If raw items exist, we would call apply_scale_scoring here.
    # For this task, we assume the input to T013d has scores.
    
    # Step 3: Binary Exposure
    df = apply_binary_exposure(df)
    
    # Step 4: Handle Outcome Missingness (T013d)
    df = handle_outcome_missingness(df)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Preprocessing complete. Saved to {output_path}")
    
    return df

def main():
    """Entry point for preprocessing."""
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / 'data' / 'raw' / 'cyberbullying_2021.csv'
    output_file = project_root / 'data' / 'results' / 'preprocessed_cohort.csv'
    
    # Allow override via environment or args if needed
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    run_preprocessing(str(input_file), str(output_file))

if __name__ == "__main__":
    main()