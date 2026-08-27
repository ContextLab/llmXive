import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset() -> pd.DataFrame:
    """
    Loads the merged dataset from the processed directory.
    Expects `code/data/processed/mito_aging_dataset.csv` to exist.
    """
    paths = get_local_paths()
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Run T018 (merge_metadata) and T020 (write_dataset) first."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['sample_id', 'age', 'haplogroup', 'heteroplasmy_burden']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    return df

def apply_exclusion_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implements conditional exclusion logic:
    1. Exclude samples with missing age from ALL analysis.
    2. Exclude samples with failed haplogroup assignment (NaN/None/empty string)
       from haplogroup-specific analysis ONLY.
       - However, RETAIN them for burden-only analysis if age is present.
       
    Returns a tuple: (df_all_analysis, df_haplogroup_analysis)
    """
    if df.empty:
        logger.warning("Input dataset is empty. Returning empty DataFrames.")
        return df.copy(), df.copy()

    # Track original counts
    total_samples = len(df)
    logger.info(f"Starting exclusion logic on {total_samples} samples.")

    # 1. Identify samples with missing age
    # Handle NaN, None, or potentially string 'nan'/'None'
    mask_age_missing = df['age'].isna()
    if df['age'].dtype == object:
        mask_age_missing = mask_age_missing | df['age'].astype(str).isin(['nan', 'None', ''])
    
    samples_missing_age = mask_age_missing.sum()
    logger.info(f"Found {samples_missing_age} samples with missing age.")

    # Filter for ALL analysis: Must have age
    df_all_analysis = df[~mask_age_missing].copy()
    samples_after_age_filter = len(df_all_analysis)
    logger.info(f"Samples remaining after age filter: {samples_after_age_filter}")

    # 2. Identify samples with failed haplogroup assignment
    # Only relevant for the 'haplogroup-specific' analysis subset
    # We apply this filter to the 'df_all_analysis' set
    if df_all_analysis.empty:
        return df_all_analysis, df_all_analysis

    mask_haplogroup_missing = df_all_analysis['haplogroup'].isna()
    if df_all_analysis['haplogroup'].dtype == object:
        mask_haplogroup_missing = mask_haplogroup_missing | df_all_analysis['haplogroup'].astype(str).isin(['nan', 'None', '', 'NA', 'N/A'])
    
    samples_missing_haplogroup = mask_haplogroup_missing.sum()
    logger.info(f"Found {samples_missing_haplogroup} samples with missing/failed haplogroup in the age-validated set.")

    # Filter for haplogroup-specific analysis: Must have age AND haplogroup
    df_haplogroup_analysis = df_all_analysis[~mask_haplogroup_missing].copy()
    samples_after_hg_filter = len(df_haplogroup_analysis)
    logger.info(f"Samples remaining for haplogroup analysis: {samples_after_hg_filter}")

    return df_all_analysis, df_haplogroup_analysis

def write_exclusion_report(df_all: pd.DataFrame, df_hg: pd.DataFrame, original_df: pd.DataFrame) -> Path:
    """
    Logs exclusion counts and retention status to `code/logs/exclusion_report.txt`.
    """
    paths = get_local_paths()
    log_dir = paths['logs']
    log_dir.mkdir(parents=True, exist_ok=True)
    report_path = log_dir / 'exclusion_report.txt'

    total_original = len(original_df)
    total_age_valid = len(df_all)
    total_hg_valid = len(df_hg)

    excluded_age = total_original - total_age_valid
    excluded_hg = total_age_valid - total_hg_valid

    with open(report_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("EXCLUSION LOG: Mitochondrial Aging Correlation Study\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total samples in merged dataset: {total_original}\n\n")
        
        f.write("--- Step 1: Age Validation (Critical) ---\n")
        f.write(f"Samples excluded (missing age): {excluded_age}\n")
        f.write(f"Samples retained for ALL analysis: {total_age_valid}\n")
        f.write(f"Exclusion Rate (Age): {(excluded_age/total_original*100):.2f}%\n\n")
        
        f.write("--- Step 2: Haplogroup Validation (Conditional) ---\n")
        f.write(f"Samples excluded from HG-analysis (missing HG): {excluded_hg}\n")
        f.write(f"Samples retained for HG-specific analysis: {total_hg_valid}\n")
        f.write(f"Note: Samples with missing HG but valid age are RETAINED for burden-only analysis.\n\n")
        
        f.write("--- Summary ---\n")
        f.write(f"Final dataset for full modeling (Age + HG): {total_hg_valid}\n")
        f.write(f"Dataset for burden-only analysis (Age only): {total_age_valid}\n")
        f.write("=" * 60 + "\n")

    logger.info(f"Exclusion report written to {report_path}")
    return report_path

def main():
    """
    Entry point for the exclusion logic task.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code/logs/exclusion_logic.log')
        ]
    )

    try:
        # Load the merged dataset (produced by T018/T020)
        df = load_processed_dataset()
        
        # Apply exclusion logic
        df_all, df_hg = apply_exclusion_logic(df)
        
        # Write report
        write_exclusion_report(df_all, df_hg, df)
        
        logger.info("Exclusion logic completed successfully.")
        
        # Optional: Save the filtered datasets for downstream tasks if needed
        # The main pipeline usually passes these DataFrames directly, 
        # but saving them ensures reproducibility if the script is run standalone.
        paths = get_local_paths()
        df_all.to_csv(paths['processed_data'] / 'mito_aging_dataset_all_analysis.csv', index=False)
        df_hg.to_csv(paths['processed_data'] / 'mito_aging_dataset_hg_analysis.csv', index=False)
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during exclusion logic: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
