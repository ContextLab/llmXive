import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd

# Ensure the project root is in the path so we can import utils if needed
# (though this task primarily uses pandas for merging)
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def setup_logging():
    """Configure logging for the feature engineering pipeline."""
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "feature_engineering.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("feature_engineering")

def load_traditional_descriptors(logger: logging.Logger) -> pd.DataFrame:
    """
    Load traditional molecular descriptors from the processed dataset.
    
    Expects: data/processed/traditional_descriptors.csv
    """
    file_path = PROJECT_ROOT / "data" / "processed" / "traditional_descriptors.csv"
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        logger.error("Data Gap: Traditional descriptors file missing. Ensure T012/T016 completed successfully.")
        raise SystemExit(1)
    
    try:
        df = pd.read_csv(file_path)
        if 'molecule_id' not in df.columns:
            logger.error("Data Gap: 'molecule_id' column missing in traditional descriptors.")
            raise SystemExit(1)
        logger.info(f"Loaded traditional descriptors: {len(df)} molecules, {len(df.columns)} features.")
        return df
    except Exception as e:
        logger.error(f"Error loading traditional descriptors: {e}")
        raise SystemExit(1)

def load_tda_features(logger: logging.Logger) -> pd.DataFrame:
    """
    Load TDA feature vectors from the processed dataset.
    
    Expects: data/processed/tda_vectors_10x10.csv
    """
    file_path = PROJECT_ROOT / "data" / "processed" / "tda_vectors_10x10.csv"
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        logger.error("Data Gap: TDA vectors file missing. Ensure T016 completed successfully.")
        raise SystemExit(1)
    
    try:
        df = pd.read_csv(file_path)
        if 'molecule_id' not in df.columns:
            logger.error("Data Gap: 'molecule_id' column missing in TDA vectors.")
            raise SystemExit(1)
        
        # Check for TDA-specific columns (p_img_0 to p_img_99 for 10x10)
        tda_cols = [col for col in df.columns if col.startswith('p_img_')]
        if len(tda_cols) == 0:
            logger.warning("Warning: No columns starting with 'p_img_' found in TDA vectors.")
        else:
            logger.info(f"Loaded TDA vectors: {len(df)} molecules, {len(tda_cols)} topological features.")
        return df
    except Exception as e:
        logger.error(f"Error loading TDA features: {e}")
        raise SystemExit(1)

def merge_features(traditional_df: pd.DataFrame, tda_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Merge traditional descriptors and TDA features on 'molecule_id'.
    
    Performs an inner join to ensure only molecules present in BOTH datasets are included.
    This prevents introducing NaN values in downstream model training.
    """
    logger.info("Merging datasets on 'molecule_id'...")
    
    merged_df = pd.merge(
        traditional_df, 
        tda_df, 
        on='molecule_id', 
        how='inner', 
        suffixes=('_trad', '_tda')
    )
    
    logger.info(f"Merged dataset shape: {merged_df.shape}")
    
    # Check for missing values
    missing_count = merged_df.isnull().sum().sum()
    if missing_count > 0:
        logger.warning(f"Warning: Merged dataset contains {missing_count} missing values.")
        # Identify which columns have missing values
        null_cols = merged_df.columns[merged_df.isnull().any()].tolist()
        logger.warning(f"Columns with missing values: {null_cols}")
    else:
        logger.info("Merged dataset is clean (no missing values).")
    
    return merged_df

def prepare_combined_feature_matrix(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Prepare the final combined feature matrix.
    
    Ensures correct column ordering and data types.
    """
    logger.info("Preparing combined feature matrix...")
    
    # Ensure 'molecule_id' is the first column
    cols = ['molecule_id'] + [c for c in df.columns if c != 'molecule_id']
    df = df[cols]
    
    # Ensure numeric columns are float64
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].astype('float64')
    
    logger.info(f"Final feature matrix ready: {df.shape[0]} samples, {df.shape[1]} features.")
    return df

def save_combined_features(df: pd.DataFrame, logger: logging.Logger) -> str:
    """
    Save the combined feature matrix to disk.
    
    Output: data/processed/combined_features.csv
    """
    output_path = PROJECT_ROOT / "data" / "processed" / "combined_features.csv"
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved combined features to: {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to save combined features: {e}")
        raise SystemExit(1)

def run_feature_engineering(logger: logging.Logger) -> str:
    """
    Main orchestration function for T017.
    
    1. Load traditional descriptors
    2. Load TDA vectors
    3. Merge on molecule_id
    4. Validate and clean
    5. Save combined CSV
    """
    logger.info("Starting Feature Engineering (T017)...")
    
    # 1. Load Data
    traditional_df = load_traditional_descriptors(logger)
    tda_df = load_tda_features(logger)
    
    # 2. Merge
    merged_df = merge_features(traditional_df, tda_df, logger)
    
    # 3. Prepare
    final_df = prepare_combined_feature_matrix(merged_df, logger)
    
    # 4. Save
    output_path = save_combined_features(final_df, logger)
    
    logger.info("Feature Engineering (T017) completed successfully.")
    return output_path

def main():
    """Entry point for the script."""
    logger = setup_logging()
    try:
        run_feature_engineering(logger)
    except SystemExit as e:
        # Re-raise if it's a controlled exit, otherwise log error
        if e.code != 0:
            logger.error("Feature Engineering failed due to data or configuration issues.")
        sys.exit(e.code)
    except Exception as e:
        logger.error(f"Unexpected error during feature engineering: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()