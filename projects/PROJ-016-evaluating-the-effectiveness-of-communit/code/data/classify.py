import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

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
    Expected file: data/processed/cbnrm_proxy_metadata.json (Primary)
    Fallback: data/processed/cbnrm_proxy_metadata_secondary.json (Secondary)
    Fallback: data/processed/cbnrm_proxy_metadata_tertiary.json (Tertiary)
    """
    # Priority order for metadata
    metadata_paths = [
        PROCESSED_DATA_DIR / "cbnrm_proxy_metadata.json",
        PROCESSED_DATA_DIR / "cbnrm_proxy_metadata_secondary.json",
        PROCESSED_DATA_DIR / "cbnrm_proxy_metadata_tertiary.json"
    ]

    for path in metadata_paths:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                if data:
                    # Determine source based on filename
                    source = "primary"
                    if "secondary" in path.name:
                        source = "secondary"
                    elif "tertiary" in path.name:
                        source = "tertiary"
                    
                    # Ensure 'threshold' exists, add default if missing (T014 requirement)
                    if 'threshold' not in data:
                        logger.warning(f"Threshold missing in {path.name}, using default 0.5")
                        data['threshold'] = 0.5
                    
                    data['proxy_source'] = source
                    return data
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {path.name}: {e}. Trying next source.")
                continue

    logger.error("CBNRM Proxy metadata missing in all expected locations. Cannot derive regime_type.")
    raise FileNotFoundError("CBNRM Proxy metadata missing in all expected locations. Cannot derive regime_type.")

def load_validation_results() -> Dict[str, Any]:
    """
    Load proxy validation results from the processed directory.
    Expected file: data/processed/proxy_validation.json
    """
    validation_path = PROCESSED_DATA_DIR / "proxy_validation.json"
    
    if not validation_path.exists():
        logger.warning(f"Proxy validation results missing: {validation_path}. Proceeding without exclusion list.")
        return {"excluded_countries": [], "proxy_source": "unknown"}
    
    try:
        with open(validation_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in proxy validation results: {e}. Proceeding without exclusion list.")
        return {"excluded_countries": [], "proxy_source": "unknown"}

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

def validate_proxy_variance() -> Dict[str, Any]:
    """
    T009d: Validate Proxy Variance.
    Logic:
    1. Load the primary proxy file (or secondary/tertiary if primary failed).
    2. If file missing/empty, log warning and return empty list.
    3. If file exists, calculate variance of the proxy for each country.
    4. Output: Save list of excluded country codes (if any) to data/processed/proxy_validation.json.
       Note: This task does NOT exclude countries from the dataset; it only reports variance issues for logging.
    """
    logger.info("Starting T009d: Proxy Variance Validation")
    
    # Determine which proxy file to load based on priority
    proxy_files = [
        ("primary", RAW_DATA_DIR / "cbnrm_proxy_primary.csv"),
        ("secondary", RAW_DATA_DIR / "cbnrm_proxy_secondary.csv"),
        ("tertiary", RAW_DATA_DIR / "cbnrm_proxy_tertiary.csv")
    ]
    
    loaded_source = None
    df = None
    
    for source, path in proxy_files:
        if path.exists():
            try:
                df = pd.read_csv(path)
                if not df.empty:
                    loaded_source = source
                    break
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}. Trying next source.")
                continue
    
    if df is None or df.empty:
        logger.warning("No valid proxy data found for variance validation. Producing empty list.")
        result = {
            "excluded_countries": [],
            "proxy_source": "none"
        }
    else:
        # Calculate variance per country
        # Assuming 'country_code' and 'value' (or similar) columns exist.
        # Standardizing column names if necessary based on common patterns.
        if 'country_code' not in df.columns:
            # Try to find a column that looks like a country code
            code_cols = [c for c in df.columns if 'code' in c.lower() or 'country' in c.lower()]
            if code_cols:
                df = df.rename(columns={code_cols[0]: 'country_code'})
            else:
                logger.error("Could not identify country code column in proxy data.")
                result = {"excluded_countries": [], "proxy_source": loaded_source}
        
        if 'value' not in df.columns:
            # Try to find a column that looks like the value
            val_cols = [c for c in df.columns if 'value' in c.lower() or 'area' in c.lower() or 'share' in c.lower()]
            if val_cols:
                df = df.rename(columns={val_cols[0]: 'value'})
            else:
                logger.error("Could not identify value column in proxy data.")
                result = {"excluded_countries": [], "proxy_source": loaded_source}
        
        if 'country_code' in df.columns and 'value' in df.columns:
            # Group by country and calculate variance
            country_variances = df.groupby('country_code')['value'].var()
            
            # Identify countries with zero variance (or very close to it)
            # A variance of 0 implies the value is constant over time for that country.
            # We flag these for logging purposes as per task description.
            # Threshold for "zero" variance to handle floating point issues
            zero_var_threshold = 1e-9
            excluded = country_variances[country_variances <= zero_var_threshold].index.tolist()
            
            logger.info(f"Found {len(excluded)} countries with near-zero variance in {loaded_source} proxy.")
            
            result = {
                "excluded_countries": excluded,
                "proxy_source": loaded_source
            }
        else:
            result = {"excluded_countries": [], "proxy_source": loaded_source}
    
    # Save result to proxy_validation.json
    output_path = PROCESSED_DATA_DIR / "proxy_validation.json"
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Saved proxy validation results to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save proxy validation results: {e}")
        sys.exit(1)
    
    return result

def main():
    """
    Main execution for T009d: Validate Proxy.
    Also serves as T014: Regime Classification if called with specific logic, 
    but primarily focused on T009d validation here.
    """
    # Step 1: Validate Proxy Variance (T009d)
    validation_result = validate_proxy_variance()
    
    # Step 2: If validation passed and we have a source, proceed to classification (T014 logic)
    # This ensures the pipeline continues even if T009d finds no exclusions.
    if validation_result.get("proxy_source") != "none":
        logger.info("Proceeding to Regime Classification (T014) after validation.")
        
        # Load Metadata (now that we know a source exists)
        try:
            metadata = load_metadata()
        except (FileNotFoundError, ValueError) as e:
            logger.critical(str(e))
            sys.exit(1)
        
        # Load Validation Results (just read back what we wrote)
        validation_data = load_validation_results()
        excluded_countries = validation_data.get('excluded_countries', [])
        
        if excluded_countries:
            logger.info(f"Note: {len(excluded_countries)} countries have zero variance (logged only).")
        
        # Load Merged Panel
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
        
        # Apply Classification
        df_classified = apply_classification(df, metadata)
        
        # Save Classified Panel
        output_path = PROCESSED_DATA_DIR / "classified_panel.csv"
        try:
            df_classified.to_csv(output_path, index=False)
            logger.info(f"Successfully saved classified panel to {output_path}")
            logger.info(f"Total rows processed: {len(df_classified)}")
            if 'regime_type' in df_classified.columns:
                logger.info(f"Rows with regime_type=1 (CBNRM): {df_classified['regime_type'].sum()}")
                logger.info(f"Rows with regime_type=0 (State-led): {(df_classified['regime_type'] == 0).sum()}")
        except Exception as e:
            logger.error(f"Failed to save classified panel: {e}")
            sys.exit(1)
    
    logger.info("T009d/T014 completed successfully.")

if __name__ == "__main__":
    main()