import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset() -> pd.DataFrame:
    """
    Load the merged processed dataset from code/data/processed/mito_aging_dataset.csv.
    """
    paths = get_local_paths()
    input_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Ensure T018 (merge_metadata) and T020 (write_dataset) have completed successfully."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    return df

def apply_exclusion_logic(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Apply conditional exclusion logic based on age and haplogroup assignment status.
    
    Rules:
    1. Exclude samples with missing 'age' from ALL analysis.
    2. Exclude samples with failed haplogroup assignment from haplogroup-specific analysis ONLY.
       Retain them for burden-only analysis if age is present.
    
    Returns:
        tuple: (full_analysis_df, haplogroup_analysis_df, exclusion_stats)
    """
    logger.info("Applying exclusion logic for age and haplogroup assignment")
    
    # Track counts
    total_samples = len(df)
    missing_age_count = 0
    failed_haplogroup_count = 0
    
    # 1. Identify samples with missing age (NaN or None)
    # Assuming 'age' column exists and is numeric. 
    missing_age_mask = df['age'].isna()
    missing_age_count = missing_age_mask.sum()
    
    # Create a mask for samples eligible for ANY analysis (must have age)
    has_age_mask = ~missing_age_mask
    
    # 2. Identify samples with failed haplogroup assignment
    # Assuming 'haplogroup' column exists. Failed assignment is typically NaN, 'UNK', or 'Failed'.
    # We treat NaN and any string indicating failure (e.g., 'UNK') as failed.
    # Let's assume 'UNK' or NaN indicates failure based on typical haplogrep2 output.
    failed_haplogroup_mask = df['haplogroup'].isna() | (df['haplogroup'] == 'UNK')
    failed_haplogroup_count = failed_haplogroup_mask.sum()
    
    # --- Dataset 1: Full Analysis (Burden only, requires Age) ---
    # Retain samples that have age, regardless of haplogroup status.
    full_analysis_df = df[has_age_mask].copy()
    logger.info(f"Full analysis dataset: {len(full_analysis_df)} samples (excluded {missing_age_count} with missing age)")
    
    # --- Dataset 2: Haplogroup-Specific Analysis ---
    # Retain samples that have age AND successful haplogroup assignment.
    haplogroup_analysis_df = df[has_age_mask & ~failed_haplogroup_mask].copy()
    logger.info(f"Haplogroup analysis dataset: {len(haplogroup_analysis_df)} samples "
                f"(excluded {failed_haplogroup_count} with failed haplogroup assignment)")
    
    # Compile exclusion statistics
    exclusion_stats = {
        'total_samples': total_samples,
        'missing_age_count': int(missing_age_count),
        'failed_haplogroup_count': int(failed_haplogroup_count),
        'full_analysis_count': int(len(full_analysis_df)),
        'haplogroup_analysis_count': int(len(haplogroup_analysis_df)),
        'retained_for_burden_only': int(len(full_analysis_df) - len(haplogroup_analysis_df))
    }
    
    return full_analysis_df, haplogroup_analysis_df, exclusion_stats

def write_exclusion_report(stats: dict, output_path: Path) -> None:
    """
    Write the exclusion report to a text file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "Exclusion Report: Mitochondrial Aging Correlation Analysis",
        "=" * 60,
        f"Total Samples Input: {stats['total_samples']}",
        "",
        "Exclusion Criteria Applied:",
        f"  1. Missing Age: {stats['missing_age_count']} samples excluded from ALL analysis.",
        f"  2. Failed Haplogroup Assignment: {stats['failed_haplogroup_count']} samples excluded from haplogroup-specific analysis.",
        "",
        "Resulting Datasets:",
        f"  - Full Analysis (Burden + Confounders): {stats['full_analysis_count']} samples",
        f"  - Haplogroup-Specific Analysis: {stats['haplogroup_analysis_count']} samples",
        "",
        "Retention Details:",
        f"  - Samples retained for burden-only analysis (missing haplogroup but have age): {stats['retained_for_burden_only']}",
        "",
        "Note: Samples excluded due to missing age are not present in either dataset.",
        "Samples excluded due to failed haplogroup are present in Full Analysis but not Haplogroup-Specific Analysis."
    ]
    
    report_text = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Exclusion report written to {output_path}")

def main():
    """
    Main entry point for the exclusion logic script.
    Loads the processed dataset, applies exclusion logic, and writes the report.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_local_paths()['logs'] / 'exclusion_logic.log')
        ]
    )
    
    try:
        # Load data
        df = load_processed_dataset()
        
        # Apply logic
        full_df, haplo_df, stats = apply_exclusion_logic(df)
        
        # Write report
        paths = get_local_paths()
        report_path = paths['logs'] / 'exclusion_report.txt'
        write_exclusion_report(stats, report_path)
        
        # Optional: Save the filtered datasets if needed downstream
        # The task description focuses on the report, but saving the filtered data
        # is often useful for downstream steps (US2, US3).
        # We will save them to processed_data with clear names.
        full_output_path = paths['processed_data'] / 'mito_aging_dataset_full_analysis.csv'
        haplo_output_path = paths['processed_data'] / 'mito_aging_dataset_haplogroup_analysis.csv'
        
        full_df.to_csv(full_output_path, index=False)
        haplo_df.to_csv(haplo_output_path, index=False)
        
        logger.info(f"Filtered datasets saved: {full_output_path}, {haplo_output_path}")
        
        print(f"Exclusion logic completed successfully.")
        print(f"Full Analysis Samples: {stats['full_analysis_count']}")
        print(f"Haplogroup Analysis Samples: {stats['haplogroup_analysis_count']}")
        
    except Exception as e:
        logger.error(f"Exclusion logic failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
