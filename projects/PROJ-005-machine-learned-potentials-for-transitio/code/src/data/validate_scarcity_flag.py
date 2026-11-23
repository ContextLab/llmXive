"""
Task T016c: Validate scarcity flag propagation.

Verifies that `code/data/processed/data_scarcity_flag.json` exists if the reaction count
was below the threshold, and that this flag is correctly referenced in the metadata
of `code/data/processed/graphs.parquet`.

Outputs a validation log to the console and returns a boolean status.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import from existing project modules
from src.utils.logging import get_logger
from src.utils.config import get_project_root, load_config


def load_scarcity_flag() -> Optional[Dict[str, Any]]:
    """Load the data scarcity flag JSON file if it exists."""
    project_root = get_project_root()
    flag_path = project_root / "data" / "processed" / "data_scarcity_flag.json"
    
    if not flag_path.exists():
        return None
    
    with open(flag_path, "r") as f:
        return json.load(f)


def load_graphs_metadata() -> Optional[Dict[str, Any]]:
    """Load the metadata from the processed graphs parquet file."""
    project_root = get_project_root()
    graphs_path = project_root / "data" / "processed" / "graphs.parquet"
    
    if not graphs_path.exists():
        return None
    
    # Parquet files store metadata in the 'schema' or custom key-value pairs
    # We read the file to access its metadata
    try:
        # Read just the metadata without loading the full dataframe if possible
        # pandas read_parquet with columns=None loads metadata
        df = pd.read_parquet(graphs_path)
        if hasattr(df, 'metadata'):
            return df.metadata
        # Fallback: check if 'scarcity_status' was stored in the dataframe columns or index
        # or if it's in the file metadata dict
        if hasattr(df, 'schema'):
            return df.schema.metadata
        return {}
    except Exception as e:
        logging.error(f"Failed to load parquet metadata: {e}")
        return None


def validate_propagation() -> bool:
    """
    Validate that the scarcity flag is correctly propagated.
    
    Logic:
    1. Check if `data_scarcity_flag.json` exists.
    2. If it exists, verify its structure (count, status, threshold).
    3. Check if `graphs.parquet` exists.
    4. Verify that the 'scarcity_status' or equivalent metadata key exists in the parquet file
       and matches the 'status' in the JSON flag.
    5. If the JSON flag does NOT exist, ensure the count was >= threshold (implied by T016b logic).
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger = get_logger("validate_scarcity_flag")
    project_root = get_project_root()
    config = load_config()
    threshold = config.get("THRESHOLD_DATA_SCARCITY", 120)
    
    flag_data = load_scarcity_flag()
    graphs_meta = load_graphs_metadata()
    
    # Case 1: Flag file exists
    if flag_data:
        logger.info("Found data_scarcity_flag.json")
        
        # Validate structure
        required_keys = {"count", "status", "threshold"}
        if not required_keys.issubset(flag_data.keys()):
            logger.error(f"Flag file missing required keys. Found: {flag_data.keys()}")
            return False
        
        if flag_data["status"] != "scarcity":
            logger.warning(f"Flag status is '{flag_data['status']}', expected 'scarcity'.")
        
        # Check propagation to parquet metadata
        if graphs_meta is None:
            logger.error("graphs.parquet not found or could not be read.")
            return False
        
        # Check for metadata key. Parquet metadata is often in df.attrs or custom schema metadata.
        # We assume the ingestion script stored 'scarcity_status' in the dataframe's custom metadata
        # or as a column. Let's check both.
        
        # 1. Check dataframe columns (if it was saved as a column)
        # 2. Check custom metadata dict
        
        metadata_status = None
        
        # Try to access via pandas custom metadata (stored in schema metadata usually)
        if hasattr(graphs_meta, 'get'):
            metadata_status = graphs_meta.get(b'scarcity_status', graphs_meta.get('scarcity_status'))
        
        # If not in schema metadata, check if it's a column in the dataframe (re-read to check columns)
        if metadata_status is None:
            try:
                df = pd.read_parquet(project_root / "data" / "processed" / "graphs.parquet")
                if "scarcity_status" in df.columns:
                    # Check the first non-null value
                    metadata_status = df["scarcity_status"].dropna().iloc[0] if not df["scarcity_status"].dropna().empty else None
            except Exception as e:
                logger.error(f"Could not verify column scarcity_status: {e}")
        
        if metadata_status is None:
            logger.error("Could not find 'scarcity_status' in graphs.parquet metadata or columns.")
            return False
        
        if str(metadata_status) != flag_data["status"]:
            logger.error(f"Metadata mismatch: Flag says '{flag_data['status']}', Parquet says '{metadata_status}'.")
            return False
        
        logger.info(f"Validation passed: Flag '{flag_data['status']}' correctly propagated to parquet.")
        return True

    else:
        # Case 2: Flag file does NOT exist
        # This implies count >= threshold. We can't strictly verify the count without re-running T016,
        # but we can verify that the parquet file does NOT have a scarcity flag set, or has a 'normal' status.
        logger.info("No data_scarcity_flag.json found. Verifying parquet is not marked as scarcity.")
        
        if graphs_meta is None:
            # If parquet doesn't exist either, that's a separate error (T017c issue), 
            # but for T016c specifically, we just check flag propagation.
            # If no flag file, and no parquet, we assume the pipeline hasn't reached graph generation yet.
            logger.warning("No flag file and no graphs.parquet found. Validation inconclusive.")
            return False
        
        # Check if parquet has a scarcity status set
        metadata_status = None
        if hasattr(graphs_meta, 'get'):
            metadata_status = graphs_meta.get(b'scarcity_status', graphs_meta.get('scarcity_status'))
        
        if metadata_status is None:
            try:
                df = pd.read_parquet(project_root / "data" / "processed" / "graphs.parquet")
                if "scarcity_status" in df.columns:
                    metadata_status = df["scarcity_status"].dropna().iloc[0] if not df["scarcity_status"].dropna().empty else None
            except Exception:
                pass
        
        if metadata_status and str(metadata_status) == "scarcity":
            logger.error("Flag file missing but parquet indicates scarcity. Inconsistency detected.")
            return False
        
        logger.info("Validation passed: No scarcity flag present, consistent with high count.")
        return True


def main():
    """Entry point for T016c."""
    logger = get_logger("validate_scarcity_flag")
    logger.info("Starting T016c: Validate scarcity flag propagation.")
    
    success = validate_propagation()
    
    if success:
        logger.info("T016c: VALIDATION SUCCESSFUL")
        sys.exit(0)
    else:
        logger.error("T016c: VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
