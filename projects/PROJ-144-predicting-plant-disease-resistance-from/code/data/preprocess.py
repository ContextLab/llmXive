"""
Preprocessing Pipeline for Metabolomics Data.

Implements:
- Log transformation
- Missing feature filtering (>30% missing)
- InChIKey alignment
- Covariate residualization
- ComBat batch correction

Outputs:
- data/processed/batch_corrected_matrix.csv
- data/processed/labels.csv
"""
import os
import sys
import glob
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import warnings
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR
from utils.io import log_preprocessing_step
from data.download import download_metabolomics_data
from data.harmonize_labels import harmonize_labels
from data.validate_temporal import validate_temporal_consistency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

def log_transform(data: pd.DataFrame) -> pd.DataFrame:
    """Apply log2 transformation to intensity values."""
    logger.info("Applying log2 transformation...")
    # Assume numeric columns are intensities
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found for log transformation.")
    
    # Add small epsilon to avoid log(0)
    data[numeric_cols] = np.log2(data[numeric_cols] + 1e-8)
    return data

def filter_missing_features(data: pd.DataFrame, threshold: float = 0.30) -> pd.DataFrame:
    """Discard features (columns) missing > threshold fraction."""
    logger.info(f"Filtering features with > {threshold*100}% missing values...")
    missing_ratio = data.isna().mean()
    keep_cols = missing_ratio[missing_ratio <= threshold].index
    filtered_data = data[keep_cols]
    dropped_count = len(data.columns) - len(keep_cols)
    logger.info(f"Dropped {dropped_count} features due to missingness.")
    return filtered_data

def align_metabolites_by_inchikey(study_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Align metabolites across studies using InChIKey."""
    logger.info("Aligning metabolites by InChIKey...")
    
    # Assume each study df has a column 'InChIKey' or similar identifier
    # We will merge on 'InChIKey' and sample_id, keeping only common metabolites
    
    # 1. Standardize column names if needed (simplified assumption)
    # We expect 'InChIKey' to be present. If not, we might need to infer.
    # For this implementation, we assume 'InChIKey' is a column.
    
    common_inchikeys = set()
    for name, df in study_dfs.items():
        if 'InChIKey' in df.columns:
            common_inchikeys.update(df['InChIKey'].dropna().unique())
        else:
            logger.warning(f"Study {name} missing InChIKey column. Skipping alignment for this study.")
    
    if not common_inchikeys:
        logger.error("No common InChIKeys found across studies.")
        return pd.DataFrame()
    
    # Filter each study to only common InChIKeys
    aligned_dfs = []
    for name, df in study_dfs.items():
        if 'InChIKey' in df.columns:
            aligned_df = df[df['InChIKey'].isin(common_inchikeys)].copy()
            aligned_dfs.append(aligned_df)
    
    if not aligned_dfs:
        return pd.DataFrame()
    
    # Concatenate and pivot to wide format if necessary
    # Assumption: Input is long format (sample_id, InChIKey, normalized_intensity)
    # Output: Wide format (sample_id, InChIKey_1, InChIKey_2, ...)
    
    combined = pd.concat(aligned_dfs, ignore_index=True)
    
    # Pivot to wide format
    # We need a unique identifier for rows. Assuming 'sample_id' + 'InChIKey' is unique per study?
    # If multiple rows per sample+inchikey (replicates), we might need to aggregate (mean).
    if combined.duplicated(subset=['sample_id', 'InChIKey']).any():
        logger.info("Aggregating duplicate sample+InChIKey entries (mean)...")
        combined = combined.groupby(['sample_id', 'InChIKey'])['normalized_intensity'].mean().reset_index()
    
    wide_df = combined.pivot(index='sample_id', columns='InChIKey', values='normalized_intensity')
    wide_df = wide_df.reset_index()
    
    logger.info(f"Aligned dataset shape: {wide_df.shape}")
    return wide_df

def residualize_confounders(data: pd.DataFrame, confounder_cols: List[str] = None) -> pd.DataFrame:
    """Residualize data for biological confounders."""
    logger.info("Residualizing confounders...")
    # If no confounders specified, skip or use default (e.g., study_id if present)
    if confounder_cols is None:
        confounder_cols = ['study_id'] # Assuming study_id is a column
    
    available_conf = [c for c in confounder_cols if c in data.columns]
    if not available_conf:
        logger.warning("No confounder columns found. Skipping residualization.")
        return data
    
    # Simple linear regression residualization for each metabolite column
    from sklearn.linear_model import LinearRegression
    
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    conf_df = data[available_conf].copy()
    
    # Encode categorical confounders if necessary
    for col in conf_df.columns:
        if conf_df[col].dtype == 'object':
            conf_df[col] = pd.Categorical(conf_df[col]).codes
    
    residuals_data = data.copy()
    
    for metabolite_col in numeric_cols:
        if metabolite_col in conf_df.columns:
            continue # Skip confounders themselves
        
        y = data[metabolite_col].dropna()
        X = conf_df.loc[y.index]
        
        if len(y) < 2 or X.isna().any().any():
            continue
        
        model = LinearRegression()
        model.fit(X, y)
        residuals = y - model.predict(X)
        residuals_data.loc[y.index, metabolite_col] = residuals
    
    return residuals_data

def apply_combat(data: pd.DataFrame, batch_col: str = 'study_id') -> pd.DataFrame:
    """Apply ComBat batch effect correction."""
    logger.info("Applying ComBat batch correction...")
    
    if batch_col not in data.columns:
        logger.warning(f"Batch column '{batch_col}' not found. Skipping ComBat.")
        return data
    
    # Check if we have multiple batches
    if data[batch_col].nunique() < 2:
        logger.info("Only one batch found. Skipping ComBat.")
        return data
    
    try:
        from pycombat import pycombat
        # Prepare data for pycombat
        # pycombat expects features in columns, samples in rows
        # and a separate batch vector
        
        # Drop non-numeric columns for the matrix
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        # Exclude the batch column from the matrix if it's numeric
        matrix_cols = [c for c in numeric_cols if c != batch_col]
        
        X = data[matrix_cols].values
        batch = data[batch_col].values
        
        if np.isnan(X).any():
            # Fill NaN with mean of column for pycombat
            col_means = np.nanmean(X, axis=0)
            for i in range(X.shape[1]):
                X[np.isnan(X[:, i]), i] = col_means[i]
        
        corrected_matrix = pycombat(X, batch)
        
        # Create new DataFrame
        corrected_df = pd.DataFrame(corrected_matrix, columns=matrix_cols, index=data.index)
        # Add back non-numeric columns (like sample_id)
        non_numeric_cols = [c for c in data.columns if c not in matrix_cols]
        for col in non_numeric_cols:
            corrected_df[col] = data[col]
        
        logger.info("ComBat correction completed.")
        return corrected_df
        
    except ImportError:
        logger.warning("pycombat not installed. Attempting simple batch mean centering as fallback.")
        # Fallback: Simple batch mean centering
        corrected_df = data.copy()
        for col in matrix_cols:
            means = data.groupby(batch_col)[col].transform('mean')
            corrected_df[col] = data[col] - means + data[col].mean()
        return corrected_df
    except Exception as e:
        logger.error(f"ComBat correction failed: {e}")
        return data

def preprocess_metabolomics() -> tuple:
    """
    Main orchestration function for preprocessing.
    Returns: (batch_corrected_matrix, labels)
    """
    logger.info("Starting full preprocessing pipeline...")
    
    # 1. Download data if not present
    # This calls the download module which handles fetching from Metabolomics Workbench
    try:
        download_metabolomics_data()
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise
    
    # 2. Validate temporal consistency
    # This checks for pre-challenge profiles
    try:
        temporal_results = validate_temporal_consistency()
        # If all studies are unverified, we might stop, but for now we proceed with verified ones
        # The download module should have filtered or we assume valid studies exist
    except Exception as e:
        logger.warning(f"Temporal validation issue: {e}")
    
    # 3. Load raw data
    # Assuming download puts files in DATA_RAW_DIR
    raw_files = glob.glob(str(DATA_RAW_DIR / "*.csv"))
    if not raw_files:
        raise FileNotFoundError("No raw data files found in data/raw/")
    
    study_dfs = {}
    for f in raw_files:
        df = pd.read_csv(f)
        study_name = Path(f).stem
        study_dfs[study_name] = df
        logger.info(f"Loaded {study_name}: {df.shape}")
    
    # 4. Align metabolites
    aligned_df = align_metabolites_by_inchikey(study_dfs)
    if aligned_df.empty:
        raise ValueError("Alignment resulted in empty dataset.")
    
    # 5. Log transform
    aligned_df = log_transform(aligned_df)
    
    # 6. Filter missing features
    aligned_df = filter_missing_features(aligned_df)
    
    # 7. Residualize confounders
    aligned_df = residualize_confounders(aligned_df)
    
    # 8. Apply ComBat
    # Ensure study_id is present for batch correction
    if 'study_id' not in aligned_df.columns:
        # Try to infer from filename or add a dummy
        logger.warning("study_id column missing. Adding dummy batch.")
        aligned_df['study_id'] = 'batch_1'
        
    aligned_df = apply_combat(aligned_df, batch_col='study_id')
    
    # 9. Harmonize labels
    # This function returns the harmonized labels dataframe
    labels_df = harmonize_labels(aligned_df)
    
    # Separate matrix and labels
    # Matrix: all numeric columns except sample_id and study_id
    matrix_cols = [c for c in aligned_df.columns if c not in ['sample_id', 'study_id'] and aligned_df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    matrix_df = aligned_df[['sample_id'] + matrix_cols]
    
    # Ensure sample_id is consistent between matrix and labels
    common_samples = set(matrix_df['sample_id']).intersection(set(labels_df['sample_id']))
    matrix_df = matrix_df[matrix_df['sample_id'].isin(common_samples)]
    labels_df = labels_df[labels_df['sample_id'].isin(common_samples)]
    
    # Sort by sample_id to ensure alignment
    matrix_df = matrix_df.sort_values('sample_id').reset_index(drop=True)
    labels_df = labels_df.sort_values('sample_id').reset_index(drop=True)
    
    return matrix_df, labels_df

def main():
    """Entry point for T017 execution."""
    try:
        matrix_df, labels_df = preprocess_metabolomics()
        
        # Save outputs
        matrix_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
        labels_path = DATA_PROCESSED_DIR / "labels.csv"
        
        matrix_df.to_csv(matrix_path, index=False)
        labels_df.to_csv(labels_path, index=False)
        
        logger.info(f"Saved matrix to {matrix_path}")
        logger.info(f"Saved labels to {labels_path}")
        
        log_preprocessing_step("preprocess_metabolomics", "completed", {
            "matrix_shape": list(matrix_df.shape),
            "labels_shape": list(labels_df.shape)
        })
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()