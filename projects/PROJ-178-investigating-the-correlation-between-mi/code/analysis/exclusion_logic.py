import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset() -> pd.DataFrame:
    """
    Load the merged dataset created by T018.
    Expects the file at code/data/processed/mito_aging_dataset.csv
    """
    paths = get_local_paths()
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Ensure T018 (merge_metadata) has completed successfully."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    return df

def apply_exclusion_logic(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Apply conditional exclusion logic per T019:
    1. Exclude samples with missing 'age' from ALL analysis.
    2. Exclude samples with failed haplogroup assignment from haplogroup-specific analysis ONLY,
       but RETAIN them for burden-only analysis if age is present.
    
    Returns:
        full_analysis_df: DataFrame with missing age rows removed (for burden-only analysis).
        haplogroup_analysis_df: DataFrame with missing age AND missing haplogroup rows removed.
        stats: Dictionary with exclusion counts and retention status.
    """
    logger.info("Applying conditional exclusion logic...")
    
    # 1. Identify missing age
    missing_age_mask = df['age'].isna()
    missing_age_count = missing_age_mask.sum()
    
    # 2. Identify missing haplogroup (failed assignment)
    # Assuming 'haplogroup' column exists and NaN or empty string indicates failure
    missing_hg_mask = df['haplogroup'].isna() | (df['haplogroup'] == '')
    missing_hg_count = missing_hg_mask.sum()
    
    # 3. Apply exclusion for ALL analysis (remove missing age)
    full_analysis_df = df[~missing_age_mask].copy()
    retained_for_full = len(full_analysis_df)
    
    # 4. Apply exclusion for haplogroup-specific analysis (remove missing age AND missing haplogroup)
    # We start from the full_analysis_df (since missing age is already excluded)
    # and remove rows where haplogroup is missing.
    haplogroup_analysis_df = full_analysis_df[~missing_hg_mask].copy()
    retained_for_hg = len(haplogroup_analysis_df)
    
    # Calculate stats
    stats = {
        'total_samples_initial': len(df),
        'excluded_missing_age': int(missing_age_count),
        'excluded_missing_haplogroup_only': int(missing_hg_count), # Those missing HG but present age
        'retained_for_full_analysis': int(retained_for_full),
        'retained_for_haplogroup_analysis': int(retained_for_hg),
        'excluded_from_hg_analysis_due_to_missing_hg': int(missing_hg_count), # Subset of missing_age excluded? No, just missing HG
        'notes': [
            "Samples with missing age were excluded from ALL analyses.",
            "Samples with missing haplogroup were excluded ONLY from haplogroup-specific analysis.",
            "Samples with missing haplogroup but valid age are retained in full_analysis_df for burden-only analysis."
        ]
    }
    
    logger.info(f"Exclusion stats: {stats}")
    return full_analysis_df, haplogroup_analysis_df, stats

def write_exclusion_report(stats: dict, output_path: Path) -> None:
    """
    Write the exclusion report to the specified text file.
    Format: Human-readable summary of counts and retention status.
    """
    logger.info(f"Writing exclusion report to {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("EXCLUSION REPORT: Mitochondrial Aging Dataset\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total Samples (Initial):       {stats['total_samples_initial']}\n")
        f.write(f"Excluded (Missing Age):        {stats['excluded_missing_age']}\n")
        f.write(f"Excluded (Missing Haplogroup): {stats['excluded_missing_hg_count']}\n")
        f.write(f"Retained (Full Analysis):      {stats['retained_for_full_analysis']}\n")
        f.write(f"Retained (Haplogroup Analysis):{stats['retained_for_haplogroup_analysis']}\n")
        f.write("\n")
        
        f.write("RETENTION LOGIC\n")
        f.write("-" * 40 + "\n")
        for note in stats['notes']:
            f.write(f"* {note}\n")
        f.write("\n")
        
        f.write("STATUS\n")
        f.write("-" * 40 + "\n")
        f.write("Exclusion logic applied successfully.\n")
        f.write("Two datasets generated:\n")
        f.write("  1. Full Analysis Set (Age present)\n")
        f.write("  2. Haplogroup Analysis Set (Age + Haplogroup present)\n")
        f.write("=" * 60 + "\n")

def main():
    """
    Main entry point for T019 execution.
    Loads processed data, applies exclusion logic, and writes the report.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    paths = get_local_paths()
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    report_path = paths['logs'] / 'exclusion_report.txt'
    
    try:
        # Load data
        df = load_processed_dataset()
        
        # Apply logic
        full_df, hg_df, stats = apply_exclusion_logic(df)
        
        # Write report
        write_exclusion_report(stats, report_path)
        
        # Save the two resulting datasets for downstream tasks (T024, etc.)
        # Although the task only explicitly asks for the report, saving the filtered
        # data is necessary for the pipeline to proceed with the correct subsets.
        # We save them to processed_data with specific names.
        full_output = paths['processed_data'] / 'mito_aging_dataset_full.csv'
        hg_output = paths['processed_data'] / 'mito_aging_dataset_hg.csv'
        
        full_df.to_csv(full_output, index=False)
        hg_df.to_csv(hg_output, index=False)
        
        logger.info(f"Saved full analysis dataset to {full_output}")
        logger.info(f"Saved haplogroup analysis dataset to {hg_output}")
        logger.info(f"Exclusion report written to {report_path}")
        
    except Exception as e:
        logger.error(f"Error in exclusion logic: {e}")
        raise

if __name__ == '__main__':
    main()
