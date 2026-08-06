import os
import sys
import json
import logging
import hashlib
import h5py
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from config import get_project_root, get_data_path, get_output_path
from logging_config import setup_logging, get_logger
from utils.validation import validate_no_null_targets

# Initialize logging
setup_logging()
logger = get_logger(__name__)

def parse_oc20_to_dataframe(file_path: str) -> pd.DataFrame:
    """
    Load OC20 H5 file and parse into a DataFrame with required columns.
    
    Args:
        file_path: Path to the OC20 H5 file (e.g., data/raw/oc20_sample.h5)
        
    Returns:
        DataFrame with columns: composition, surface_facet, experimental_tof, 
        d_band_center, adsorption_energy
    """
    logger.info(f"Loading OC20 data from {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    try:
        with h5py.File(file_path, 'r') as f:
            # Inspect structure
            logger.info(f"H5 keys: {list(f.keys())}")
            
            # Assuming standard OC20 structure: f['data'] or similar
            # Adjust based on actual dataset schema if needed
            if 'data' in f:
                data_group = f['data']
            else:
                # Fallback: try root level if 'data' group doesn't exist
                data_group = f
            
            # Extract arrays - adjust keys based on actual dataset
            # Common OC20 keys: 'sid', 'fid', 'atoms', 'energy', 'forces', etc.
            # For this implementation, we assume specific columns exist or can be derived
            
            # Attempt to load required fields
            try:
                # Composition (might be derived from atoms or stored directly)
                if 'composition' in data_group:
                    composition = data_group['composition'][:]
                else:
                    # Fallback: derive from atoms if available
                    if 'atoms' in data_group:
                        # This is a placeholder; real parsing depends on OC20 schema
                        logger.warning("Composition not found directly; attempting derivation")
                        composition = ["Unknown"] * len(data_group['energy'])
                    else:
                        logger.error("Neither 'composition' nor 'atoms' found in dataset")
                        sys.exit(1)
                
                # Surface facet
                if 'surface_facet' in data_group:
                    surface_facet = data_group['surface_facet'][:]
                else:
                    surface_facet = ["Unknown"] * len(composition)
                
                # Experimental TOF (Target Variable)
                if 'experimental_tof' in data_group:
                    experimental_tof = data_group['experimental_tof'][:]
                else:
                    # If not present, initialize with NaN to be handled later
                    experimental_tof = [float('nan')] * len(composition)
                
                # d_band_center
                if 'd_band_center' in data_group:
                    d_band_center = data_group['d_band_center'][:]
                else:
                    d_band_center = [float('nan')] * len(composition)
                
                # adsorption_energy
                if 'adsorption_energy' in data_group:
                    adsorption_energy = data_group['adsorption_energy'][:]
                else:
                    adsorption_energy = [float('nan')] * len(composition)
                
                # Ensure all arrays have same length
                n_samples = len(composition)
                if not (len(surface_facet) == len(experimental_tof) == 
                        len(d_band_center) == len(adsorption_energy) == n_samples):
                    logger.error("Inconsistent array lengths in dataset")
                    sys.exit(1)
                        
            except KeyError as e:
                logger.error(f"Missing expected key in dataset: {e}")
                sys.exit(1)
                
            df = pd.DataFrame({
                'composition': composition,
                'surface_facet': surface_facet,
                'experimental_tof': experimental_tof,
                'd_band_center': d_band_center,
                'adsorption_energy': adsorption_energy
            })
            
            logger.info(f"Parsed {len(df)} entries from OC20")
            return df
            
    except Exception as e:
        logger.error(f"Error reading H5 file: {e}")
        sys.exit(1)

def construct_unified_dataframe(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Construct the unified DataFrame by generating entry_ids and preparing data.
    
    Args:
        df: Input DataFrame from parse_oc20_to_dataframe
        output_path: Path to save the unified DataFrame (intermediate)
        
    Returns:
        Unified DataFrame with entry_id column
    """
    logger.info("Constructing unified DataFrame with entry IDs")
    
    # Generate unique entry_id by hashing composition + surface_facet
    def generate_entry_id(row):
        key = f"{row['composition']}{row['surface_facet']}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    df['entry_id'] = df.apply(generate_entry_id, axis=1)
    
    # Save intermediate unified dataframe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved unified DataFrame to {output_path}")
    
    return df

def retrieve_target_variable(df: pd.DataFrame, target_column: str = 'experimental_tof') -> Tuple[pd.DataFrame, List[str]]:
    """
    Retrieve target variable from aligned data and log missing values.
    
    Args:
        df: The unified DataFrame containing the target variable
        target_column: Name of the target column (default: 'experimental_tof')
        
    Returns:
        Tuple of (DataFrame with target retrieved, list of entry_ids with missing targets)
    """
    logger.info(f"Retrieving target variable: {target_column}")
    
    if target_column not in df.columns:
        logger.error(f"Target column '{target_column}' not found in DataFrame")
        sys.exit(1)
    
    # Identify missing target values
    missing_mask = df[target_column].isna()
    missing_entry_ids = df.loc[missing_mask, 'entry_id'].tolist()
    
    if missing_entry_ids:
        logger.warning(f"Found {len(missing_entry_ids)} entries with missing {target_column} values")
        logger.warning("These entries will be excluded from subsequent training steps")
        
        # Log the missing entry IDs for audit
        missing_log_path = get_output_path("missing_target_entries.json")
        os.makedirs(os.path.dirname(missing_log_path), exist_ok=True)
        
        missing_data = {
            "target_column": target_column,
            "count": len(missing_entry_ids),
            "entry_ids": missing_entry_ids
        }
        
        with open(missing_log_path, 'w') as f:
            json.dump(missing_data, f, indent=2)
        
        logger.info(f"Logged missing target entries to {missing_log_path}")
    else:
        logger.info(f"All {len(df)} entries have valid {target_column} values")
    
    return df, missing_entry_ids

def main():
    """
    Main execution flow for T015: Retrieve target variable and log missing values.
    """
    project_root = get_project_root()
    data_path = get_data_path()
    output_path = get_output_path()
    
    # Define paths
    raw_data_file = os.path.join(data_path, "raw", "oc20_sample.h5")
    unified_csv = os.path.join(data_path, "processed", "unified_dataframe.csv")
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(unified_csv), exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Step 1: Parse OC20 to DataFrame
    if not os.path.exists(raw_data_file):
        logger.error(f"Raw data file not found: {raw_data_file}")
        logger.error("Please ensure T010 (download_data.py) has been executed successfully.")
        sys.exit(1)
    
    df_raw = parse_oc20_to_dataframe(raw_data_file)
    
    # Step 2: Construct unified DataFrame (T013b dependency)
    df_unified = construct_unified_dataframe(df_raw, unified_csv)
    
    # Step 3: Retrieve target variable (T015 core logic)
    df_final, missing_ids = retrieve_target_variable(df_unified)
    
    # Save the final aligned dataset (intermediate, before imputation)
    final_csv = os.path.join(data_path, "processed", "aligned_data_pre_imputation.csv")
    df_final.to_csv(final_csv, index=False)
    logger.info(f"Saved aligned data (pre-imputation) to {final_csv}")
    
    logger.info("T015 completed successfully.")
    logger.info(f"Total entries: {len(df_final)}")
    logger.info(f"Entries with missing target: {len(missing_ids)}")

if __name__ == "__main__":
    main()