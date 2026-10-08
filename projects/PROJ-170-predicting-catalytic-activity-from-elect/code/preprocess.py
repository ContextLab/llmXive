import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Import from project config for paths
try:
    from config import get_project_root, get_data_path, get_output_path
except ImportError:
    # Fallback for direct execution if config not in path yet
    from code.config import get_project_root, get_data_path, get_output_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_output_path('run.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_unified_dataframe() -> pd.DataFrame:
    """
    Load the imputed dataset produced by T017a.
    Expects: data/processed/imputed_dataset.csv
    """
    input_path = get_data_path('processed/imputed_dataset.csv')
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("T017a (KNN Imputation) must be completed successfully before running T019.")
        sys.exit(1)
    
    logger.info(f"Loading imputed dataset from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def get_numeric_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify all numeric columns that are NOT the target variable.
    Target variable is 'experimental_tof'.
    String columns (composition, surface_facet, entry_id) are excluded.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude the target variable from scaling features
    target_var = 'experimental_tof'
    if target_var in numeric_cols:
        numeric_cols.remove(target_var)
    
    logger.info(f"Identified {len(numeric_cols)} numeric feature columns for scaling.")
    logger.debug(f"Feature columns: {numeric_cols[:10]}...")
    return numeric_cols

def scale_features(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Scale selected numeric features to zero mean and unit variance using StandardScaler.
    
    Args:
        df: Input DataFrame
        feature_cols: List of column names to scale
        
    Returns:
        Tuple of (scaled DataFrame, fitted StandardScaler)
    """
    if not feature_cols:
        logger.warning("No feature columns found to scale.")
        return df, StandardScaler()

    # Create a copy to avoid modifying original
    df_scaled = df.copy()
    
    scaler = StandardScaler()
    
    logger.info(f"Scaling features: {len(feature_cols)} columns")
    
    # Fit and transform the selected columns
    scaled_values = scaler.fit_transform(df_scaled[feature_cols])
    df_scaled[feature_cols] = scaled_values
    
    logger.info("Scaling completed successfully.")
    
    # Verify scaling (mean ~0, std ~1 for features)
    verification = df_scaled[feature_cols].describe()
    logger.debug(f"Scaling verification (first 3 features):\n{verification[verification.columns[:3]]}")
    
    return df_scaled, scaler

def save_scaler(scaler: StandardScaler, feature_cols: List[str], output_path: Path) -> None:
    """
    Save the fitted scaler and feature list for later use in model training.
    """
    scaler_data = {
        'mean': scaler.mean_.tolist(),
        'scale': scaler.scale_.tolist(),
        'var': scaler.var_.tolist(),
        'feature_names': feature_cols
    }
    
    with open(output_path, 'w') as f:
        json.dump(scaler_data, f, indent=2)
    
    logger.info(f"Scaler saved to {output_path}")

def main() -> None:
    """
    Main execution for T019: Scale all numeric features to zero mean and unit variance.
    
    This task:
    1. Loads the imputed dataset from T017a
    2. Identifies numeric feature columns (excluding target)
    3. Applies StandardScaler (zero mean, unit variance)
    4. Saves the scaled dataset to data/processed/scaled_dataset.csv
    5. Saves the fitted scaler metadata to code/models/scaler_metadata.json
    """
    logger.info("=" * 60)
    logger.info("Starting T019: Feature Scaling")
    logger.info("=" * 60)
    
    # Step 1: Load imputed dataset
    df = load_unified_dataframe()
    
    # Step 2: Identify numeric features (exclude target)
    feature_cols = get_numeric_feature_columns(df)
    
    # Step 3: Scale features
    df_scaled, scaler = scale_features(df, feature_cols)
    
    # Step 4: Save scaled dataset
    output_path = get_data_path('processed/scaled_dataset.csv')
    df_scaled.to_csv(output_path, index=False)
    logger.info(f"Scaled dataset saved to {output_path}")
    
    # Step 5: Save scaler metadata for downstream tasks (T024, T025, T026)
    scaler_metadata_path = get_project_root() / 'code' / 'models' / 'scaler_metadata.json'
    save_scaler(scaler, feature_cols, scaler_metadata_path)
    
    # Step 6: Log summary statistics
    logger.info("Scaling Summary:")
    logger.info(f"  - Total rows: {len(df_scaled)}")
    logger.info(f"  - Total columns: {len(df_scaled.columns)}")
    logger.info(f"  - Features scaled: {len(feature_cols)}")
    logger.info(f"  - Target column preserved: experimental_tof")
    
    # Verify no NaN introduced
    nan_counts = df_scaled.isna().sum()
    if nan_counts.sum() > 0:
        logger.warning(f"NaN values detected after scaling:\n{nan_counts[nan_counts > 0]}")
    else:
        logger.info("Verification: No NaN values in scaled dataset.")
    
    logger.info("=" * 60)
    logger.info("T019 completed successfully")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
