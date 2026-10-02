import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from logging_config import get_logger

# Configuration paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def load_metadata() -> Dict[str, Any]:
    """
    Load CBNRM proxy metadata from the processed directory.
    Expected file: data/processed/cbnrm_proxy_metadata.json
    """
    metadata_path = PROCESSED_DATA_DIR / "cbnrm_proxy_metadata.json"
    
    if not metadata_path.exists():
        logger.error(f"CBNRM Proxy metadata missing: {metadata_path}. Cannot derive regime_type.")
        raise FileNotFoundError(f"CBNRM Proxy metadata missing. Cannot derive regime_type.")
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        if not data:
            logger.error("CBNRM Proxy metadata is empty. Cannot derive regime_type.")
            raise ValueError("CBNRM Proxy metadata missing. Cannot derive regime_type.")
        
        # Validate required fields
        if 'threshold' not in data:
            logger.error("Threshold not found in CBNRM Proxy metadata. Cannot derive regime_type.")
            raise ValueError("CBNRM Proxy metadata missing. Cannot derive regime_type.")
        
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in CBNRM Proxy metadata: {e}")
        raise

def load_validation_results() -> Dict[str, Any]:
    """
    Load proxy validation results from the processed directory.
    Expected file: data/processed/proxy_validation.json
    """
    validation_path = PROCESSED_DATA_DIR / "proxy_validation.json"
    
    if not validation_path.exists():
        logger.warning(f"Proxy validation results missing: {validation_path}. Proceeding without exclusion list.")
        return {"excluded_countries": []}
    
    try:
        with open(validation_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in proxy validation results: {e}. Proceeding without exclusion list.")
        return {"excluded_countries": []}

def classify_regime(proxy_value: float, threshold: float) -> int:
    """
    Classify regime type based on proxy value and threshold.
    Logic: If proxy_value > threshold, set regime_type=1 (CBNRM), else 0 (State-led).
    """
    if pd.isna(proxy_value):
        return None
    return 1 if proxy_value > threshold else 0

def apply_classification(df: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply regime classification to the dataframe.
    Expects 'proxy_value' column to exist.
    """
    threshold = metadata['threshold']
    
    # Handle potential missing proxy values
    df['regime_type'] = df['proxy_value'].apply(lambda x: classify_regime(x, threshold))
    
    return df

def main():
    """
    Main execution for T014: Regime Classification.
    1. Load metadata (fail loud if missing).
    2. Load validation results (warn if missing).
    3. Load merged panel data.
    4. Apply classification.
    5. Save classified panel.
    """
    logger.info("Starting T014: Regime Classification")
    
    # Step 1: Load Metadata (Fail Loud)
    try:
        metadata = load_metadata()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Step 2: Load Validation Results
    validation_data = load_validation_results()
    excluded_countries = validation_data.get('excluded_countries', [])
    
    if excluded_countries:
        logger.info(f"Excluding {len(excluded_countries)} countries based on validation: {excluded_countries}")
    
    # Step 3: Load Merged Panel
    merged_panel_path = PROCESSED_DATA_DIR / "merged_panel.csv"
    if not merged_panel_path.exists():
        logger.error(f"Merged panel not found: {merged_panel_path}. T013 must run first.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(merged_panel_path)
    except Exception as e:
        logger.error(f"Failed to load merged panel: {e}")
        sys.exit(1)
    
    # Check for required columns
    required_cols = ['proxy_value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in merged panel: {missing_cols}")
        sys.exit(1)
    
    # Step 4: Apply Classification
    df_classified = apply_classification(df, metadata)
    
    # Step 5: Save Classified Panel
    output_path = PROCESSED_DATA_DIR / "classified_panel.csv"
    try:
        df_classified.to_csv(output_path, index=False)
        logger.info(f"Successfully saved classified panel to {output_path}")
        logger.info(f"Total rows processed: {len(df_classified)}")
        logger.info(f"Rows with regime_type=1 (CBNRM): {df_classified['regime_type'].sum()}")
        logger.info(f"Rows with regime_type=0 (State-led): {(df_classified['regime_type'] == 0).sum()}")
    except Exception as e:
        logger.error(f"Failed to save classified panel: {e}")
        sys.exit(1)
    
    logger.info("T014 completed successfully.")

if __name__ == "__main__":
    main()
