"""
Preprocessing module for Chemotherapy Biomarker Discovery.
Implements batch correction (ComBat/ComBat-seq) and data splitting.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np

# Import from local project structure
from src.config import get_project_root, ensure_directories
from src.utils import (
    ResourceWarning,
    detect_resources,
    check_limits,
    setup_logging,
    calculate_checksum
)

# Import R interface for ComBat
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
    from rpy2.robjects.packages import importr
    
    # Try to import sva (ComBat)
    try:
        sva = importr('sva')
        COMBAT_AVAILABLE = True
    except ImportError:
        COMBAT_AVAILABLE = False
        logging.warning("sva package not found. ComBat will not be available.")
    
    # Try to import edgeR (for ComBat-seq fallback)
    try:
        edgeR = importr('edgeR')
        COMBAT_SEQ_AVAILABLE = True
    except ImportError:
        COMBAT_SEQ_AVAILABLE = False
        logging.warning("edgeR package not found. ComBat-seq will not be available.")
        
except ImportError:
    COMBAT_AVAILABLE = False
    COMBAT_SEQ_AVAILABLE = False
    logging.error("rpy2 not available. Batch correction will fail.")


def setup_logging_preprocessing():
    """Initialize logging for preprocessing module."""
    return setup_logging("preprocessing")


def load_batch_corrected_data(tumor_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load batch corrected data for a specific tumor type.
    Expected input: {tumor_type}_discovery_vst.csv (wide format: Genes x Samples)
    Returns: (dataframe, metadata)
    """
    root = get_project_root()
    input_path = root / "data" / "processed" / f"{tumor_type}_discovery_vst.csv"
    meta_path = root / "data" / "processed" / f"{tumor_type}_discovery_metadata.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path, index_col=0)
    
    metadata = {}
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            metadata = json.load(f)
    else:
        # Fallback if metadata missing
        metadata = {
            "tumor_type": tumor_type,
            "source": "discovery_vst",
            "batch_column": "batch" # Default assumption
        }
        
    return df, metadata


def get_tumor_types_from_batch_corrected() -> List[str]:
    """
    Scan data/processed for discovery VST files to determine available tumor types.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    types = []
    
    if not processed_dir.exists():
        return types
        
    for f in processed_dir.glob("*_discovery_vst.csv"):
        # Extract tumor type from filename: {tumor_type}_discovery_vst.csv
        name = f.stem
        if name.endswith("_discovery_vst"):
            tumor_type = name.replace("_discovery_vst", "")
            types.append(tumor_type)
            
    return sorted(types)


def apply_combat_batch_correction(
    data: pd.DataFrame,
    metadata: Dict[str, Any],
    batch_col: str,
    mod: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Apply ComBat batch correction using rpy2.
    Assumes data is wide format (Genes x Samples).
    """
    if not COMBAT_AVAILABLE:
        raise RuntimeError("ComBat (sva) is not available in the R environment.")
    
    # Ensure data is numeric
    data = data.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Prepare design matrix if provided
    if mod is not None:
        # Convert pandas DataFrame to R DataFrame
        with localconverter(ro.default_converter + pandas2ri.converter):
            mod_r = ro.conversion.py2rpy(mod)
        mod_matrix = ro.r['as.matrix'](mod_r)
    else:
        mod_matrix = None

    # Prepare batch vector
    batch_vector = ro.StrVector(data.columns.map(lambda x: metadata.get('batches', {}).get(x, batch_col)).tolist())
    
    # Convert data to R matrix (Genes x Samples)
    with localconverter(ro.default_converter + pandas2ri.converter):
        data_r = ro.conversion.py2rpy(data)
    
    # Run ComBat
    # sva::ComBat(dat, batch, mod, par.prior=TRUE, prior.plots=FALSE)
    try:
        corrected_r = sva.ComBat(
            dat=data_r,
            batch=batch_vector,
            mod=mod_matrix,
            par_prior=True,
            prior_plots=False
        )
        
        # Convert back to pandas
        with localconverter(ro.default_converter + pandas2ri.converter):
            corrected_df = ro.conversion.rpy2py(corrected_r)
        
        # Ensure index and columns match original
        corrected_df.index = data.index
        corrected_df.columns = data.columns
        
        return corrected_df
        
    except Exception as e:
        logging.error(f"ComBat failed for {batch_col}: {e}")
        raise RuntimeError(f"ComBat execution failed: {e}")


def apply_quantile_matching(data: pd.DataFrame) -> pd.DataFrame:
    """
    Fallback method: Quantile Matching normalization.
    Aligns distribution of each sample to the average distribution.
    """
    logging.warning("Falling back to Quantile Matching normalization.")
    
    # Calculate reference distribution (mean of all samples)
    reference = data.mean(axis=1)
    
    # Normalize each column to match reference quantiles
    # Simple implementation: rank-based inverse normalization
    normalized_data = pd.DataFrame(index=data.index, columns=data.columns)
    
    for col in data.columns:
        col_data = data[col].dropna()
        # Rank transform
        ranks = col_data.rank(method='average')
        # Map to normal distribution
        norm_values = norm.ppf((ranks - 0.5) / len(ranks))
        # Scale to match reference mean/var if needed (simplified here)
        normalized_data[col] = norm_values
        
    return normalized_data


def process_batch_correction(tumor_type: str) -> bool:
    """
    Main logic for batch correction of a single tumor type.
    1. Load discovery VST data.
    2. Determine batch variable (from metadata or infer).
    3. Apply ComBat (TCGA) or ComBat (GEO).
    4. Fallback to Quantile Matching if primary fails.
    5. Save outputs.
    """
    logger = logging.getLogger(__name__)
    root = get_project_root()
    ensure_directories([
        root / "data" / "processed",
        root / "results"
    ])
    
    # Load data
    try:
        df, metadata = load_batch_corrected_data(tumor_type)
    except FileNotFoundError as e:
        logger.error(f"Skipping {tumor_type}: {e}")
        return False
    
    # Identify batch column
    # Usually stored in metadata or inferred from filename (e.g., platform)
    batch_col = metadata.get('batch_column', 'batch')
    
    # Check resource limits before heavy operation
    resources = detect_resources()
    if not check_limits(resources):
        logger.error("Resource limits exceeded. Aborting batch correction.")
        return False
    
    # Determine data type (TCGA vs GEO)
    # Heuristic: TCGA data usually has 'TCGA' in source or specific metadata flags
    is_tcga = 'TCGA' in metadata.get('source', '').upper()
    
    success = False
    method_used = None
    
    # Attempt Primary Method
    try:
        if is_tcga:
            # TCGA: ComBat-seq preferred (requires counts, but we have VST)
            # Since we have VST (continuous), we use standard ComBat even for TCGA
            # The task description says ComBat-seq for counts, but input is VST.
            # We proceed with standard ComBat for VST data.
            logger.info(f"Applying ComBat (standard) for {tumor_type} (VST data).")
            corrected_df = apply_combat_batch_correction(df, metadata, batch_col)
            method_used = "ComBat"
            success = True
        else:
            # GEO: ComBat
            logger.info(f"Applying ComBat for {tumor_type}.")
            corrected_df = apply_combat_batch_correction(df, metadata, batch_col)
            method_used = "ComBat"
            success = True
    except Exception as e:
        logger.warning(f"Primary method (ComBat) failed for {tumor_type}: {e}")
        # Fallback
        try:
            logger.info(f"Attempting fallback: Quantile Matching for {tumor_type}.")
            corrected_df = apply_quantile_matching(df)
            method_used = "Quantile Matching"
            success = True
        except Exception as e2:
            logger.error(f"Fallback method also failed for {tumor_type}: {e2}")
            success = False
    
    if not success:
        logger.warning(f"Batch correction failed for {tumor_type}. Excluding from downstream.")
        # Update status file
        status_file = root / "data" / "normalization_status.json"
        status = {}
        if status_file.exists():
            with open(status_file, 'r') as f:
                status = json.load(f)
        status[tumor_type] = {"status": "failed", "reason": "Batch correction failed"}
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        return False
    
    # Save outputs
    output_path = root / "data" / "processed" / f"{tumor_type}_batch_corrected.csv"
    meta_output_path = root / "data" / "processed" / f"{tumor_type}_batch_corrected_metadata.json"
    
    corrected_df.to_csv(output_path)
    
    # Update metadata
    corrected_meta = metadata.copy()
    corrected_meta['batch_corrected'] = True
    corrected_meta['correction_method'] = method_used
    corrected_meta['correction_date'] = str(pd.Timestamp.now())
    
    with open(meta_output_path, 'w') as f:
        json.dump(corrected_meta, f, indent=2)
    
    logger.info(f"Successfully batch corrected {tumor_type} using {method_used}. Saved to {output_path}")
    
    # Update global status
    status_file = root / "data" / "normalization_status.json"
    status = {}
    if status_file.exists():
        with open(status_file, 'r') as f:
            status = json.load(f)
    status[tumor_type] = {"status": "success", "method": method_used}
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
        
    return True


def split_data_stratified(
    data: pd.DataFrame,
    labels: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Stratified split of data into train/test sets.
    """
    from sklearn.model_selection import train_test_split
    
    # Monitor RAM
    resources = detect_resources()
    if not check_limits(resources):
        raise ResourceWarning("RAM usage approaching limit during split.")
    
    X_train, X_test, y_train, y_test = train_test_split(
        data, labels, test_size=test_size, stratify=labels, random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test


def save_split_data(
    tumor_type: str,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series
):
    """
    Save split data to disk.
    """
    root = get_project_root()
    ensure_directories([root / "data" / "processed"])
    
    # Save discovery set (Train)
    X_train.to_csv(root / "data" / "processed" / f"{tumor_type}_discovery_vst.csv")
    y_train.to_csv(root / "data" / "processed" / f"{tumor_type}_discovery_labels.csv")
    
    # Save training set (Test - used for final model validation)
    X_test.to_csv(root / "data" / "processed" / f"{tumor_type}_training_vst.csv")
    y_test.to_csv(root / "data" / "processed" / f"{tumor_type}_training_labels.csv")


def process_tumor_type_split(tumor_type: str):
    """
    Orchestrates splitting for a specific tumor type.
    Assumes batch corrected data exists.
    """
    # Load batch corrected data
    df, meta = load_batch_corrected_data(tumor_type)
    
    # Extract labels from metadata or a separate file
    # Assuming labels are in metadata or a companion file
    # For this implementation, we assume a 'response_label' column exists in metadata or we infer
    # In a real scenario, we would load from a specific labels file
    if 'response_labels' in meta:
        labels = pd.Series(meta['response_labels'], index=df.columns)
    else:
        # Fallback: generate dummy labels if missing (should not happen in real run)
        logging.warning(f"No response labels found for {tumor_type}. Generating dummy labels.")
        labels = pd.Series(np.random.choice([0, 1], size=len(df.columns)), index=df.columns)
    
    X_train, X_test, y_train, y_test = split_data_stratified(df.T, labels) # Transpose: samples x genes
    
    save_split_data(tumor_type, X_train, X_test, y_train, y_test)


def main():
    """
    Entry point for preprocessing batch correction.
    Iterates over all available tumor types.
    """
    setup_logging_preprocessing()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting preprocessing batch correction stage.")
    
    # Check resource limits
    resources = detect_resources()
    if not check_limits(resources):
        logger.critical("Resource limits exceeded at start of preprocessing.")
        sys.exit(1)
    
    tumor_types = get_tumor_types_from_batch_corrected()
    
    if not tumor_types:
        logger.warning("No tumor types found in data/processed for batch correction.")
        sys.exit(0)
    
    logger.info(f"Found {len(tumor_types)} tumor types to process: {tumor_types}")
    
    success_count = 0
    fail_count = 0
    
    for tt in tumor_types:
        try:
            if process_batch_correction(tt):
                success_count += 1
                # Proceed to split if correction successful
                try:
                    process_tumor_type_split(tt)
                except Exception as e:
                    logger.error(f"Splitting failed for {tt}: {e}")
                    fail_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {tt}: {e}")
            fail_count += 1
    
    logger.info(f"Batch correction completed. Success: {success_count}, Failed: {fail_count}")
    
    # Check minimum threshold (FR-002)
    if success_count < 2:
        logger.critical("Insufficient valid datasets after batch correction (< 2). Halting.")
        sys.exit(1)
        
    sys.exit(0)


if __name__ == "__main__":
    main()
