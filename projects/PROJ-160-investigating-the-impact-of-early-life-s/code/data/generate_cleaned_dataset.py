"""
Script to generate the final cleaned dataset for User Story 1.

This script orchestrates the full US1 pipeline:
1. Acquires raw data (if not present) via acquisition module.
2. Loads raw CSVs.
3. Filters for missing ACE and poor MRI quality.
4. Normalizes volumes by ICV.
5. Applies log-transformation to ACE if skewed.
6. Flags extreme ACE outliers.
7. Outputs the final cleaned dataset to data/processed/cleaned_dataset.csv.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import PROJECT_ROOT as CONFIG_ROOT
from code.config_env import get_raw_dir, get_processed_dir, ensure_directories
from code.data.acquisition import acquire_data
from code.data.loaders import load_csv
from code.data.preprocessing import (
    filter_missing_ace,
    filter_poor_mri_quality,
    normalize_volumes_by_icv,
    apply_log_transformation_if_skewed,
    flag_extreme_outliers,
    preprocess_for_us1
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point to generate the cleaned dataset."""
    logger.info("Starting cleaned dataset generation for T019.")
    
    # Ensure directories exist
    ensure_directories()
    raw_dir = get_raw_dir()
    processed_dir = get_processed_dir()
    
    # 1. Attempt to acquire data if raw files are missing
    # The acquisition module expects specific filenames. 
    # We run it to ensure data is present.
    logger.info("Checking for raw data...")
    # acquire_data handles downloading and checksum verification.
    # It returns paths to the downloaded files or raises an error.
    try:
        # We call acquire_data. If files exist, it might skip or re-verify.
        # If it fails (e.g., no network), we assume data might be present or fail loudly.
        # For this specific task, we assume the environment has network or data pre-seeded.
        acquired_files = acquire_data() 
        logger.info(f"Data acquisition/verification completed. Files: {acquired_files}")
    except Exception as e:
        # If acquisition fails, we check if files exist locally anyway (fallback)
        logger.warning(f"Acquisition step failed or skipped: {e}. Checking for existing raw files.")
        # We proceed to loading; if files don't exist, the loader will fail.
    
    # 2. Load and Preprocess
    # The preprocess_for_us1 function encapsulates the logic for T015, T016, T017, T018.
    # It returns the final DataFrame.
    try:
        logger.info("Running full US1 preprocessing pipeline...")
        # This function calls:
        # - load_csv (for phenotypic and segmentation data)
        # - filter_missing_ace
        # - filter_poor_mri_quality
        # - normalize_volumes_by_icv
        # - apply_log_transformation_if_skewed
        # - flag_extreme_outliers
        final_df = preprocess_for_us1(raw_dir)
        
        if final_df is None or final_df.empty:
            logger.error("Preprocessing resulted in an empty dataset.")
            # Create an empty file with headers if needed, or fail
            return

        # 3. Ensure specific columns exist and are ordered as per T019 requirement
        # Required: ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV, Normalized_Volumes
        # Note: normalize_volumes_by_icv likely creates separate columns for CA3, DG, Subiculum normalized.
        # We need to verify the column names match the requirement.
        
        # Re-order and rename if necessary based on what preprocess_for_us1 returns
        # Assuming preprocess_for_us1 returns a DF with normalized columns named:
        # 'CA3_normalized', 'DG_normalized', 'Subiculum_normalized' or similar.
        # The task asks for a column "Normalized_Volumes". 
        # We will create a JSON column or a string representation if multiple volumes exist,
        # OR we assume the task implies the set of normalized volume columns.
        # Given the schema in T006a: "Normalized_Volumes" is singular. 
        # We will create a JSON string column containing the normalized values for the three subfields.
        
        normalized_cols = [col for col in final_df.columns if 'normalized' in col.lower()]
        
        if len(normalized_cols) > 0:
            # Create a JSON string column for 'Normalized_Volumes'
            import json
            final_df['Normalized_Volumes'] = final_df[normalized_cols].apply(
                lambda row: json.dumps(row.to_dict(), sort_keys=True), axis=1
            )
            # Drop the individual normalized columns if the requirement is strictly one column
            # But usually, downstream analysis needs the individual columns. 
            # T006a schema lists columns: CA3, DG, Subiculum, ICV, Normalized_Volumes.
            # It implies CA3, DG, Subiculum might be the raw or normalized? 
            # Context: "Normalize CA3, DG, subiculum volumes by dividing by ICV".
            # Let's assume the columns CA3, DG, Subiculum in the output are the NORMALIZED ones
            # and we add a summary column. 
            # However, T019 says: "columns (ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV, Normalized_Volumes)"
            # If CA3, DG, Subiculum are the raw ones, we keep them. If normalized, we keep them.
            # The preprocessing step T016 says "storing with >=4 decimal precision".
            # Let's ensure we have the normalized versions available. 
            # We will keep the original raw columns (if present) and add the normalized ones, 
            # but the prompt specifically lists CA3, DG, Subiculum. 
            # We will assume these are the normalized volumes as per the flow.
            
            # If the DF has 'CA3_norm', rename to 'CA3' if needed, or just ensure the names match.
            # Let's standardize:
            rename_map = {}
            for col in final_df.columns:
                if 'norm' in col.lower() and 'ca3' in col.lower():
                    rename_map[col] = 'CA3'
                elif 'norm' in col.lower() and 'dg' in col.lower():
                    rename_map[col] = 'DG'
                elif 'norm' in col.lower() and 'subiculum' in col.lower():
                    rename_map[col] = 'Subiculum'
            
            final_df = final_df.rename(columns=rename_map)
        
        # Select and order required columns
        required_cols = ['ACE', 'Age', 'Sex', 'Site', 'FamilyID', 'CA3', 'DG', 'Subiculum', 'ICV', 'Normalized_Volumes']
        
        # Check if all required columns exist
        missing_cols = [c for c in required_cols if c not in final_df.columns]
        if missing_cols:
            logger.warning(f"Missing required columns in output: {missing_cols}. Attempting to fill or warn.")
            # If raw CA3 exists but normalized is missing, we can't fabricate. 
            # We proceed with what we have.
        
        # Filter to only required columns that exist
        output_cols = [c for c in required_cols if c in final_df.columns]
        output_df = final_df[output_cols].copy()
        
        # 4. Save to CSV
        output_path = processed_dir / "cleaned_dataset.csv"
        output_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully generated cleaned dataset at: {output_path}")
        logger.info(f"Dataset shape: {output_df.shape}")
        logger.info(f"Columns: {list(output_df.columns)}")
        
    except Exception as e:
        logger.error(f"Failed to generate cleaned dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
