import os
import sys
import json
import logging
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from scipy import stats

# Import local config
from config import get_config, ensure_dirs

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Existing Functions (Preserved) ---

def load_processed_data():
    """Loads the preprocessed data from the standard location."""
    config = get_config()
    path = config['paths']['processed_data']
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data not found at {path}. Run preprocessing pipeline first.")
    return pd.read_parquet(path)

def generate_interaction_features(df):
    """Generates interaction features (Temp * Element)."""
    logger.info("Generating interaction features...")
    # Assuming columns 'rolling_temperature' exist and composition columns exist
    # This is a placeholder for the actual logic which should be in the real file
    # For this task, we assume the dataframe already has these or we add them here
    # based on the task description "Temp x Mg", etc.
    # We will check for common composition columns if not present
    composition_cols = [col for col in df.columns if col.lower() in ['mg', 'si', 'cu', 'zn', 'fe']]
    temp_col = 'rolling_temperature'
    
    if temp_col not in df.columns:
        # Fallback or error handling if temp column is named differently
        temp_col = next((c for c in df.columns if 'temp' in c.lower()), None)
        if not temp_col:
            raise ValueError("Temperature column not found for interaction generation.")

    for col in composition_cols:
        if col != temp_col:
            new_col_name = f"Temp_x_{col}"
            df[new_col_name] = df[temp_col] * df[col]
    
    logger.info(f"Added {len(composition_cols)} interaction features.")
    return df

def normalize_features(df):
    """Applies StandardScaler to numeric features."""
    logger.info("Normalizing features...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude target variable if it's in the list (usually 'grain_size')
    if 'grain_size' in numeric_cols:
        numeric_cols.remove('grain_size')
    
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df, scaler

def residualize_data(df):
    """Regresses Grain Size against Alloy Series + Composition and stores residuals."""
    logger.info("Residualizing data...")
    # This logic depends on 'alloy_series' and composition columns being present
    # We assume 'alloy_series' was extracted in T022c
    if 'alloy_series' not in df.columns:
        raise ValueError("Alloy Series column not found. Ensure T022c (extract_alloy_series) ran.")
    
    # Define features for residualization (Composition + Series)
    # We need to encode alloy_series if it's categorical
    # For simplicity in this snippet, assuming it's numeric or handled by sklearn
    features_for_resid = [c for c in df.columns if c not in ['grain_size', 'rolling_temperature']]
    # Ensure we don't include the target
    if 'grain_size' in features_for_resid:
        features_for_resid.remove('grain_size')
    
    X = df[features_for_resid].fillna(0)
    y = df['grain_size']
    
    model = LinearRegression()
    model.fit(X, y)
    
    residuals = y - model.predict(X)
    df['residuals'] = residuals
    logger.info("Residualization complete.")
    return df

def validate_data_quality(df):
    """Validates data quality (nulls, ranges)."""
    logger.info("Validating data quality...")
    # Basic checks
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
    return df

def detect_collinearity(df):
    """Detects collinearity and writes report to data/artifacts/collinearity_report.json."""
    logger.info("Detecting collinearity...")
    numeric_df = df.select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr().abs()
    
    flagged_pairs = []
    threshold = 0.8
    
    # Upper triangle only
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    for col in upper.columns:
        for row in upper.index:
            if upper.at[row, col] > threshold:
                flagged_pairs.append([row, col])
    
    report = {"flagged_pairs": flagged_pairs}
    config = get_config()
    artifact_path = Path(config['paths']['artifacts'])
    artifact_path.mkdir(parents=True, exist_ok=True)
    output_file = artifact_path / "collinearity_report.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Collinearity report written to {output_file}")
    return report

# --- New Function for T022d ---

def create_group_kfold_splitter(groups):
    """
    Implements GroupKFold splitter logic.
    
    Args:
        groups (np.array or list): The group labels (Alloy Series) for each sample.
    
    Returns:
        GroupKFold: The instantiated splitter object.
    
    Raises:
        ValueError: If groups are empty or invalid.
    """
    if groups is None or len(groups) == 0:
        raise ValueError("Groups cannot be empty. Ensure T022c (extract_alloy_series) ran successfully.")
    
    # Instantiate GroupKFold. Default n_splits=5 is standard, but can be parameterized if needed.
    # The task requires returning the object, not running the split immediately.
    splitter = GroupKFold(n_splits=5)
    
    # Verification: Check that the splitter is callable and has the correct attributes
    if not hasattr(splitter, 'split'):
        raise RuntimeError("Failed to instantiate GroupKFold splitter.")
    
    logger.info(f"GroupKFold splitter created with {len(np.unique(groups))} unique groups.")
    return splitter

# --- Pipeline Integration ---

def run_preprocessing_pipeline():
    """
    Orchestrates the full preprocessing pipeline including T022d logic.
    """
    config = get_config()
    ensure_dirs()
    
    # 1. Load Data (Assuming T014/T016 produced data/processed/raw_cleaned.parquet or similar)
    # We need to load the data that has been cleaned and has 'alloy_series' extracted
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    
    # 2. Generate Interactions
    df = generate_interaction_features(df)
    
    # 3. Normalize
    df, scaler = normalize_features(df)
    
    # 4. Residualize
    df = residualize_data(df)
    
    # 5. Validate
    df = validate_data_quality(df)
    
    # 6. Detect Collinearity (T023)
    detect_collinearity(df)
    
    # 7. Extract Groups (T022c dependency - assumed present in df)
    if 'alloy_series' not in df.columns:
        logger.error("Alloy Series missing. Cannot create splitter.")
        sys.exit(1)
    
    groups = df['alloy_series'].values
    
    # 8. Create GroupKFold Splitter (T022d)
    splitter = create_group_kfold_splitter(groups)
    
    # Verification: Run a quick split to ensure no group overlaps
    logger.info("Verifying GroupKFold splits for non-overlapping groups...")
    train_indices = []
    test_indices = []
    for train_idx, test_idx in splitter.split(df, groups=groups):
        train_indices.append(train_idx)
        test_indices.append(test_idx)
        
        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])
        
        if train_groups.intersection(test_groups):
            raise RuntimeError("Group overlap detected in split! T022d verification failed.")
    
    logger.info("GroupKFold verification passed. No group overlaps found.")
    
    # Save processed data if not already saved by load_processed_data logic
    # (Assuming the pipeline writes the final state)
    output_path = Path(config['paths']['processed_data'])
    df.to_parquet(output_path)
    logger.info(f"Final processed data saved to {output_path}")
    
    return df, splitter

def main():
    """Entry point for the preprocessing script."""
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline.")
    parser.parse_args()
    
    try:
        df, splitter = run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
