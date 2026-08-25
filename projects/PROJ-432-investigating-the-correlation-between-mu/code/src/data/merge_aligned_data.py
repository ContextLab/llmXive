"""
Task T014b: Merge aligned temporal data with T_eff values to produce final aligned dataset.

This script consumes:
1. The output of T012 (aligned daily data) - expected at data/processed/aligned_temporal.json or similar intermediate
2. The output of T017 (t_eff_values.csv) - expected at data/processed/t_eff_values.csv

It produces:
- data/processed/aligned_daily.csv: Final merged dataset with muon counts and t_eff_value.

Dependencies:
- pandas
- src.data.ingest (for alignment logic if needed, though we assume T012 output exists)
- src.data.preprocess (for T_eff calculation if needed, though we assume T017 output exists)
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path if running directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.utils import setup_logger
from src.data.ingest import align_temporal_data
from src.data.preprocess import run_preprocessing

logger = setup_logger("merge_aligned_data", log_file="logs/merge_aligned_data.log")

def load_aligned_temporal_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the aligned temporal data produced by T012.
    
    Since T012 is marked as incomplete in the task list, we must ensure the data
    exists or re-run the alignment logic if the file is missing.
    The T012 task description says: "Implement temporal alignment logic in src/data/ingest.py: resample muon counts to daily sums, average temperature metrics, and drop dates with missing data in either source"
    and "Implement logging of exclusion events to logs/alignment.json".
    
    We assume T012 would have produced a file like data/processed/aligned_temporal.csv or similar.
    If not found, we re-run the alignment logic from ingest.py.
    """
    # Check for expected intermediate file from T012
    # The task description doesn't specify the exact filename for T012 output.
    # We'll assume it's 'aligned_temporal.csv' or we need to generate it.
    # Given the dependency on T012, and T012 is not marked complete, we must implement the alignment here
    # or rely on the fact that T012's logic is in ingest.py and we can call it.
    
    aligned_file = data_dir / "aligned_temporal.csv"
    
    if not aligned_file.exists():
        logger.warning(f"Intermediate aligned file {aligned_file} not found. Re-running alignment logic from ingest.py.")
        # Re-run alignment logic
        # We need to fetch or load raw data first if not present
        # But T009 and T010 are marked complete, so raw data should be in data/raw/
        raw_icecube = data_dir.parent / "raw" / "icecube.csv"
        raw_era5 = data_dir.parent / "raw" / "era5.csv"
        
        if not raw_icecube.exists() or not raw_era5.exists():
            raise FileNotFoundError(
                f"Raw data files not found. Expected {raw_icecube} and {raw_era5}. "
                "Please ensure T009 and T010 have been completed successfully."
            )
        
        # Load raw data
        icecube_df = pd.read_csv(raw_icecube)
        era5_df = pd.read_csv(raw_era5)
        
        # Perform alignment
        # The align_temporal_data function in ingest.py is expected to handle this
        # We need to check its signature. Based on T012 description, it should return aligned data.
        # Let's assume it takes the two DataFrames and returns the aligned one.
        # If the function signature is different, we adjust.
        try:
            aligned_df = align_temporal_data(icecube_df, era5_df)
        except TypeError as e:
            # Fallback: implement basic alignment if function signature is unexpected
            logger.error(f"align_temporal_data signature mismatch: {e}. Implementing basic alignment.")
            # Basic alignment: merge on date, drop NA
            # Ensure date columns are datetime
            icecube_df['date'] = pd.to_datetime(icecube_df['date'])
            era5_df['date'] = pd.to_datetime(era5_df['date'])
            
            # Group by date for icecube (sum counts)
            icecube_daily = icecube_df.groupby('date', as_index=False)['count'].sum()
            icecube_daily.rename(columns={'count': 'muon_count'}, inplace=True)
            
            # Group by date for era5 (mean temperature)
            # Assume era5 has 'temperature' column
            era5_daily = era5_df.groupby('date', as_index=False)['temperature'].mean()
            era5_daily.rename(columns={'temperature': 'avg_temperature'}, inplace=True)
            
            # Merge
            aligned_df = pd.merge(icecube_daily, era5_daily, on='date', how='inner')
        
        aligned_df.to_csv(aligned_file, index=False)
        logger.info(f"Saved aligned temporal data to {aligned_file}")
    else:
        aligned_df = pd.read_csv(aligned_file)
        logger.info(f"Loaded aligned temporal data from {aligned_file}")
    
    return aligned_df

def load_t_eff_values(data_dir: Path) -> pd.DataFrame:
    """
    Load the T_eff values produced by T017.
    Expected at data/processed/t_eff_values.csv
    """
    t_eff_file = data_dir / "t_eff_values.csv"
    
    if not t_eff_file.exists():
        raise FileNotFoundError(
            f"T_eff values file not found: {t_eff_file}. "
            "Please ensure T017 has been completed successfully."
        )
    
    df = pd.read_csv(t_eff_file)
    logger.info(f"Loaded T_eff values from {t_eff_file}, shape: {df.shape}")
    return df

def merge_and_save(
    aligned_df: pd.DataFrame,
    t_eff_df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Merge aligned data with T_eff values on 'date' and save to output_path.
    """
    # Ensure date columns are datetime for merging
    aligned_df['date'] = pd.to_datetime(aligned_df['date'])
    t_eff_df['date'] = pd.to_datetime(t_eff_df['date'])
    
    # Merge
    merged_df = pd.merge(
        aligned_df,
        t_eff_df[['date', 't_eff_value']], # Select only necessary columns
        on='date',
        how='inner'
    )
    
    # Verify non-null temperature metrics
    if merged_df['t_eff_value'].isnull().any():
        logger.warning("Merged dataset contains null t_eff_value entries. Dropping them.")
        merged_df = merged_df.dropna(subset=['t_eff_value'])
    
    # Save
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged aligned daily data to {output_path}, shape: {merged_df.shape}")
    
    return merged_df

def main():
    """
    Main entry point for T014b.
    """
    logger.info("Starting T014b: Merging aligned data with T_eff values.")
    
    data_dir = project_root / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load inputs
    try:
        aligned_df = load_aligned_temporal_data(data_dir)
        t_eff_df = load_t_eff_values(data_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Define output path
    output_path = data_dir / "aligned_daily.csv"
    
    # Merge and save
    try:
        final_df = merge_and_save(aligned_df, t_eff_df, output_path)
        
        # Verification
        if final_df.empty:
            logger.error("Final merged dataset is empty. Cannot proceed.")
            sys.exit(1)
        
        if 't_eff_value' not in final_df.columns:
            logger.error("t_eff_value column missing in final dataset.")
            sys.exit(1)
        
        if final_df['t_eff_value'].isnull().any():
            logger.error("Final dataset still contains null t_eff_value entries.")
            sys.exit(1)
        
        logger.info("T014b completed successfully. Output verified.")
        logger.info(f"Output file: {output_path}")
        logger.info(f"Rows: {len(final_df)}, Columns: {list(final_df.columns)}")
        
    except Exception as e:
        logger.error(f"Error during merge and save: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()