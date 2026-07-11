"""
Module to assemble feature vectors from computed graph metrics and save to CSV.

This task (T022) aggregates the results from T019 (global metrics), T020 (regional centrality),
and T021 (collinearity handling) to produce the primary feature set `data/processed/features.csv`.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from graph_metrics.calculator import (
    load_connectivity_matrix,
    compute_global_efficiency,
    compute_local_efficiency,
    compute_modularity,
    compute_betweenness_centrality,
    extract_regional_centrality,
    extract_features_for_subject,
    run_collinearity_check_and_reduction
)
from preprocessing.motion_flagging import get_all_subject_ids

logger = logging.getLogger(__name__)

# Configuration paths
PROCESSED_DIR = "data/processed"
METADATA_DIR = "data/metadata"
OUTPUT_FILE = "data/processed/features.csv"
SUBJECT_STATUS_FILE = "data/metadata/subject_status.csv"
LABELS_FILE = "data/metadata/subject_labels.csv"

def load_subject_status():
    """Load the subject status DataFrame to filter out excluded subjects."""
    status_path = Path(PROCESSED_DIR).parent / METADATA_DIR / SUBJECT_STATUS_FILE
    if not status_path.exists():
        logger.warning(f"Subject status file not found at {status_path}. Proceeding with all subjects.")
        return None
    
    df = pd.read_csv(status_path)
    # Filter for subjects that are NOT excluded
    # Assuming 'excluded' column exists and is boolean or 1/0
    if 'excluded' in df.columns:
        valid_subjects = df[df['excluded'] == False]['subject_id'].tolist()
    elif 'status' in df.columns:
        valid_subjects = df[df['status'] == 'included']['subject_id'].tolist()
    else:
        logger.warning("Could not determine inclusion status from subject_status.csv. Using all subjects.")
        return None
    
    return valid_subjects

def load_labels():
    """Load subject labels (0/1 for diagnosis) to append to features."""
    labels_path = Path(PROCESSED_DIR).parent / METADATA_DIR / LABELS_FILE
    if not labels_path.exists():
        logger.warning(f"Labels file not found at {labels_path}. Diagnosis column will be empty.")
        return {}
    
    df = pd.read_csv(labels_path)
    # Assume columns: subject_id, diagnosis (or label)
    if 'diagnosis' in df.columns:
        return dict(zip(df['subject_id'], df['diagnosis']))
    elif 'label' in df.columns:
        return dict(zip(df['subject_id'], df['label']))
    else:
        logger.warning("Labels file exists but no 'diagnosis' or 'label' column found.")
        return {}

def assemble_features():
    """
    Main function to assemble feature vectors for all valid subjects.
    1. Identify valid subjects (not excluded by motion).
    2. Load connectivity matrices for each.
    3. Compute metrics (reusing T019-T021 logic).
    4. Handle collinearity (T021).
    5. Assemble into DataFrame and save to data/processed/features.csv.
    """
    logger.info("Starting feature vector assembly (T022)...")
    
    # Ensure output directory exists
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Get valid subjects
    valid_subjects = load_subject_status()
    if valid_subjects is None:
        # Fallback: get all subjects from parcellation if status file missing
        valid_subjects = get_all_subject_ids()
        logger.info(f"Using all available subjects: {len(valid_subjects)}")
    else:
        logger.info(f"Using {len(valid_subjects)} subjects (excluding flagged ones).")

    if not valid_subjects:
        logger.error("No valid subjects found. Aborting feature assembly.")
        return False

    # 2. Load labels
    labels = load_labels()

    # 3. Iterate and compute
    feature_rows = []
    
    for subject_id in valid_subjects:
        try:
            # Load matrix (assumes T013/T016 produced data/processed/<id>_matrix.npy or .csv)
            # The calculator expects the matrix path or subject ID to locate it.
            # We assume the standard naming convention: data/processed/sub-<id>_matrix.npy
            matrix_path = Path(PROCESSED_DIR) / f"{subject_id}_matrix.npy"
            if not matrix_path.exists():
                # Try alternative naming if standard fails
                matrix_path = Path(PROCESSED_DIR) / f"sub-{subject_id}_matrix.npy"
            
            if not matrix_path.exists():
                logger.warning(f"Matrix not found for {subject_id}. Skipping.")
                continue

            matrix = load_connectivity_matrix(str(matrix_path))
            
            if matrix is None or matrix.size == 0:
                logger.warning(f"Invalid matrix for {subject_id}. Skipping.")
                continue

            # Compute metrics using the pipeline functions from calculator.py
            # extract_features_for_subject returns a dict of metrics
            metrics = extract_features_for_subject(matrix, subject_id)
            
            if metrics is None:
                logger.warning(f"Feature extraction failed for {subject_id}. Skipping.")
                continue

            # Add label if available
            if subject_id in labels:
                metrics['diagnosis'] = labels[subject_id]
            else:
                metrics['diagnosis'] = np.nan

            feature_rows.append(metrics)
            
        except Exception as e:
            logger.error(f"Error processing subject {subject_id}: {e}", exc_info=True)
            continue

    if not feature_rows:
        logger.error("No features were successfully extracted.")
        return False

    # 4. Create DataFrame
    df_features = pd.DataFrame(feature_rows)
    
    # 5. Handle Collinearity (T021)
    # The calculator has a function to check and reduce collinearity.
    # We apply it here to the assembled dataframe if requested by config,
    # or simply ensure the raw features are saved as the primary output.
    # Per T022 description, we save the PRIMARY feature set. 
    # T021 might have already flagged/reduced, but we ensure consistency.
    
    # Check if collinearity reduction is needed/applicable
    # For this task, we assume the 'extract_features_for_subject' returns the 
    # metrics as computed. If T021 logic requires PCA, it should be applied here
    # if the 'check_collinearity' function indicates it.
    # However, T021 says "if found, apply PCA... OR drop features". 
    # We will perform the check on the assembled DF.
    
    collinearity_log_path = Path(PROCESSED_DIR).parent / METADATA_DIR / "collinearity_log.txt"
    
    # Simple check: if any correlation > 0.8 among numeric features (excluding ID/label)
    numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        # Check correlations
        corr_matrix = df_features[numeric_cols].corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.8)]
        
        if to_drop:
            logger.warning(f"Collinearity detected. Dropping features: {to_drop}")
            with open(collinearity_log_path, 'w') as f:
                f.write(f"Collinearity detected (r > 0.8). Dropping features: {to_drop}\n")
            df_features = df_features.drop(columns=to_drop)
        else:
            # If no high collinearity, log that check was passed
            with open(collinearity_log_path, 'w') as f:
                f.write("Collinearity check passed (no r > 0.8 found).\n")
    else:
        with open(collinearity_log_path, 'w') as f:
            f.write("Insufficient features for collinearity check.\n")

    # 6. Save to CSV
    df_features.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Feature vector assembly complete. Saved {len(df_features)} rows to {OUTPUT_FILE}")
    logger.info(f"Columns: {list(df_features.columns)}")
    
    return True

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    success = assemble_features()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
