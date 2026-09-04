import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from logging_config import get_logger
from utils import check_disk_usage, load_matrix_from_parquet
from error_handling import raise_storage_limit_error, StorageLimitExceededError

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
STORAGE_LIMIT_GB = 14.0
SAFETY_THRESHOLD_GB = 12.0

def ensure_directories():
    """Create necessary directory structure."""
    for directory in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def check_raw_nifti_presence() -> bool:
    """Check if raw NIfTI files exist in the raw directory."""
    if not RAW_DIR.exists():
        return False
    nifti_files = list(RAW_DIR.glob("*.nii.gz")) + list(RAW_DIR.glob("*.nii"))
    return len(nifti_files) > 0

def fetch_precomputed_data() -> Dict[str, Any]:
    """
    Fetch pre-computed SC/FC matrices from the verified HuggingFace dataset.
    Returns a dictionary mapping subject_id to (sc_matrix, fc_matrix).
    """
    try:
        from datasets import load_dataset
        logger.info("Loading pre-computed matrices from HuggingFace...")
        # Verified source from task description
        dataset = load_dataset("openneuro-pub/ds000224-parquet", split="train")
        
        if "structural_matrix" not in dataset.column_names or "functional_matrix" not in dataset.column_names:
            logger.error("Dataset missing required columns: structural_matrix, functional_matrix")
            raise ValueError("Data Gap: Required columns missing in dataset.")

        data_map = {}
        for row in dataset:
            sid = row.get("subject_id")
            if not sid:
                continue
            sc = row.get("structural_matrix")
            fc = row.get("functional_matrix")
            if sc is not None and fc is not None:
                data_map[sid] = (sc, fc)
        
        logger.info(f"Successfully loaded {len(data_map)} subjects from pre-computed source.")
        return data_map
    except Exception as e:
        logger.error(f"Failed to fetch pre-computed data: {e}")
        raise

def validate_subject_data(data_map: Dict[str, Any]) -> List[str]:
    """
    Validate that all matrices are 400x400 and contain no NaNs.
    Returns a list of valid subject IDs.
    """
    valid_subjects = []
    for sid, (sc, fc) in data_map.items():
        try:
            # Basic shape check assuming list-of-lists or similar structure
            if hasattr(sc, 'shape'):
                if sc.shape != (400, 400):
                    logger.warning(f"Subject {sid}: SC shape mismatch {sc.shape}, skipping.")
                    continue
                if hasattr(fc, 'shape') and fc.shape != (400, 400):
                    logger.warning(f"Subject {sid}: FC shape mismatch {fc.shape}, skipping.")
                    continue
            # Check for NaNs if numpy array
            import numpy as np
            if isinstance(sc, np.ndarray):
                if np.isnan(sc).any():
                    logger.warning(f"Subject {sid}: SC contains NaNs, skipping.")
                    continue
            if isinstance(fc, np.ndarray):
                if np.isnan(fc).any():
                    logger.warning(f"Subject {sid}: FC contains NaNs, skipping.")
                    continue
            
            valid_subjects.append(sid)
        except Exception as e:
            logger.warning(f"Subject {sid} validation failed: {e}, skipping.")
    
    return valid_subjects

def save_sample_data(data_map: Dict[str, Any], valid_subjects: List[str]):
    """Save validated matrices to the processed directory."""
    import numpy as np
    for sid in valid_subjects:
        sc, fc = data_map[sid]
        # Ensure numpy arrays for saving
        if not isinstance(sc, np.ndarray):
            sc = np.array(sc)
        if not isinstance(fc, np.ndarray):
            fc = np.array(fc)
        
        sc_path = PROCESSED_DIR / f"sc_{sid}.npy"
        fc_path = PROCESSED_DIR / f"fc_{sid}.npy"
        
        np.save(sc_path, sc)
        np.save(fc_path, fc)
        logger.info(f"Saved matrices for subject {sid}")

def cleanup_raw_files():
    """
    Implement storage cleanup logic to remove raw files after processing.
    This ensures we stay within the 14 GB limit by freeing space used by
    raw NIfTI files once they have been processed into matrices.
    """
    if not RAW_DIR.exists():
        logger.info("Raw directory does not exist, nothing to clean.")
        return

    # Check current disk usage before cleanup
    current_usage_gb = check_disk_usage()
    logger.info(f"Disk usage before cleanup: {current_usage_gb:.2f} GB")

    if current_usage_gb < SAFETY_THRESHOLD_GB:
        logger.info(f"Disk usage ({current_usage_gb:.2f} GB) is below safety threshold ({SAFETY_THRESHOLD_GB} GB). Skipping cleanup.")
        return

    logger.info(f"Disk usage ({current_usage_gb:.2f} GB) exceeds safety threshold ({SAFETY_THRESHOLD_GB} GB). Initiating cleanup of raw files.")
    
    raw_files = list(RAW_DIR.glob("*"))
    if not raw_files:
        logger.info("No raw files found to delete.")
        return

    deleted_count = 0
    deleted_size = 0
    for file_path in raw_files:
        try:
            if file_path.is_file():
                size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                deleted_size += size
                logger.debug(f"Deleted raw file: {file_path.name} ({size / (1024*1024):.2f} MB)")
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                # Approximate size for directories (simplified)
                for root, dirs, files in os.walk(file_path):
                    for f in files:
                        fp = Path(root) / f
                        deleted_size += fp.stat().st_size
                deleted_count += 1
                logger.debug(f"Deleted raw directory: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
    
    logger.info(f"Cleanup complete: Deleted {deleted_count} items, freed {deleted_size / (1024*1024*1024):.2f} GB.")

    # Verify disk usage after cleanup
    final_usage_gb = check_disk_usage()
    logger.info(f"Disk usage after cleanup: {final_usage_gb:.2f} GB")
    
    if final_usage_gb >= STORAGE_LIMIT_GB:
        logger.error(f"Disk usage ({final_usage_gb:.2f} GB) still exceeds limit ({STORAGE_LIMIT_GB} GB) after cleanup.")
        raise StorageLimitExceededError(f"Storage limit exceeded even after cleanup. Current: {final_usage_gb:.2f} GB, Limit: {STORAGE_LIMIT_GB} GB")

def main():
    """Main entry point for data download and processing pipeline."""
    logger.info("Starting data download and processing pipeline.")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check disk usage at start
    initial_usage = check_disk_usage()
    if initial_usage >= STORAGE_LIMIT_GB:
        raise StorageLimitExceededError(f"Initial disk usage ({initial_usage:.2f} GB) exceeds limit ({STORAGE_LIMIT_GB} GB).")

    # Determine data source
    has_raw = check_raw_nifti_presence()
    data_map = {}
    
    if has_raw:
        logger.warning("Raw NIfTI files detected. Raw processing (T012b) should have run. Attempting to load processed matrices.")
        # In a real pipeline, T012b would generate these. For this task, we assume
        # T012b ran and generated .npy files in PROCESSED_DIR, or we rely on pre-computed.
        # Since T012b is marked as failed in the prompt history, we prioritize the pre-computed path
        # if raw processing artifacts are not found, but the logic here is for cleanup.
        pass
    
    # Fetch pre-computed data (Primary path per T012)
    try:
        data_map = fetch_precomputed_data()
    except Exception as e:
        logger.critical(f"Pre-computed data fetch failed: {e}")
        raise

    if not data_map:
        logger.error("No data found in pre-computed source.")
        raise ValueError("Data Gap: No valid data found in pre-computed source.")

    # Validate
    valid_subjects = validate_subject_data(data_map)
    if len(valid_subjects) < 10:
        logger.error(f"Not enough valid subjects ({len(valid_subjects)} < 10).")
        raise ValueError("Data Gap: Insufficient valid subjects.")

    # Save processed data
    save_sample_data(data_map, valid_subjects)
    
    # Perform cleanup of raw files if disk usage is high
    # This is the core of T016
    cleanup_raw_files()
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()