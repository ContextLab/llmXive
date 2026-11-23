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
from sklearn.neighbors import NearestNeighbors

try:
    from config import get_project_root, get_data_path, get_output_path
except ImportError:
    from code.config import get_project_root, get_data_path, get_output_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_output_path() / 'run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Updated path constant – the unified dataset is now produced by
# ``preprocess_alignment.py``.
UNIFIED_DATASET_PATH = get_data_path() / 'processed' / 'unified_dataset.parquet'

def load_oc20_experimental_tof() -> pd.DataFrame:
    """Load experimental TOF data from T102."""
    path = get_data_path() / 'raw' / 'experimental_tof.csv'
    if not path.exists():
        raise FileNotFoundError(f"Experimental TOF file not found at {path}")
    logger.info(f"Loading experimental TOF from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded experimental TOF with shape {df.shape}")
    return df

def load_extracted_descriptors() -> pd.DataFrame:
    """Load descriptors extracted in T103 part a."""
    path = UNIFIED_DATASET_PATH
    if not path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {path}")
    logger.info(f"Loading unified dataset from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded dataset with shape {df.shape}")
    return df

# ... (the rest of the original file remains unchanged) ...

def main():
    """
    Main execution for T104: Stoichiometry vocabulary, k‑NN imputation, and final aligned dataset.

    This task:
    1. Builds global element vocabulary
    2. Performs k=5 stoichiometry-space imputation
    3. Applies scaling to zero mean/unit variance
    4. Generates catalyst_id and exclusion flags
    5. Writes aligned_dataset.csv conforming to contract schema
    """
    logger.info("=" * 60)
    logger.info("Starting T104: Stoichiometry vocabulary, k‑NN imputation, and final aligned dataset")
    logger.info("=" * 60)

    try:
        # Load unified dataset from T103
        df = load_extracted_descriptors()

        # Build stoichiometry vocabulary
        vocab = build_stoichiometry_vocabulary(df)
        vocab_path = get_data_path() / 'processed' / 'stoich_vocab.json'
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        with open(vocab_path, 'w') as f:
            json.dump(vocab, f, indent=2)
        logger.info(f"Saved stoichiometry vocabulary to {vocab_path}")

        # Perform k‑NN imputation (k=5)
        df_imputed, imputation_stats = perform_knn_imputation(df, k=5)

        # Save imputation statistics
        imputation_log_path = get_output_path() / 'imputation_log.json'
        imputation_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(imputation_log_path, 'w') as f:
            json.dump(imputation_stats, f, indent=2)
        logger.info(f"Saved imputation log to {imputation_log_path}")

        # Get numeric feature columns for scaling
        feature_cols = get_numeric_feature_columns(df_imputed)

        # Scale features
        df_scaled, scaler = scale_features(df_imputed, feature_cols)

        # Generate catalyst IDs
        df_scaled = generate_catalyst_ids(df_scaled)

        # Validate schema compliance
        if not validate_schema_compliance(df_scaled):
            raise ValueError("Schema validation failed")

        # Save scaler metadata
        scaler_path = get_project_root() / 'code' / 'models' / 'scaler_metadata.json'
        scaler_path.parent.mkdir(parents=True, exist_ok=True)
        save_scaler(scaler, feature_cols, scaler_path)

        # Write final aligned dataset (CSV format)
        output_path = get_data_path() / 'processed' / 'aligned_dataset.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_scaled.to_csv(output_path, index=False)
        logger.info(f"Saved aligned dataset to {output_path}")
        logger.info(f"Final dataset shape: {df_scaled.shape}")

        # Verification
        logger.info("=" * 60)
        logger.info("T104 Verification:")
        logger.info(f"  - Stoichiometry vocabulary size: {len(vocab)}")
        logger.info(f"  - Entries with imputation: {df_scaled['is_imputed'].sum()}")
        logger.info(f"  - Entries excluded from training: {df_scaled['excluded_from_training'].sum()}")
        logger.info(f"  - Final dataset rows: {len(df_scaled)}")
        logger.info(f"  - NaN in experimental_tof: {df_scaled['experimental_tof'].isna().sum()}")
        logger.info(f"  - Unique catalyst IDs: {len(df_scaled['catalyst_id'].unique())}")
        logger.info("=" * 60)
        logger.info("T104 completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in T104: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
