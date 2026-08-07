import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/exclusion_report.txt')
    ]
)
logger = logging.getLogger(__name__)

def load_processed_dataset():
    """Load the merged dataset created in T018."""
    paths = get_local_paths()
    input_path = paths['processed_dataset']
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Run T018 (merge_metadata) before T019."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    return pd.read_csv(input_path)

def apply_exclusion_logic(df):
    """
    Implement conditional exclusion logic:
    1. Exclude samples with missing age from ALL analysis.
    2. Exclude samples with failed haplogroup assignment from 
       haplogroup-specific analysis ONLY, but RETAIN them for 
       burden-only analysis if age is present.
    
    Returns:
      tuple: (full_dataset_clean, haplogroup_specific_dataset, exclusion_report_dict)
    """
    logger.info("Applying conditional exclusion logic...")
    
    initial_count = len(df)
    logger.info(f"Initial dataset size: {initial_count} samples")
    
    # 1. Exclude samples with missing age from ALL analysis
    age_missing_mask = df['age'].isna()
    age_missing_count = age_missing_mask.sum()
    
    if age_missing_count > 0:
        logger.warning(f"Excluding {age_missing_count} samples with missing age from ALL analysis")
    
    df_age_clean = df[~age_missing_mask].copy()
    after_age_exclusion_count = len(df_age_clean)
    
    # 2. Exclude samples with failed haplogroup assignment from haplogroup-specific analysis ONLY
    # Failed assignment is typically represented as 'Unknown', 'Failed', or NaN in haplogroup column
    haplogroup_column = 'haplogroup'
    if haplogroup_column not in df_age_clean.columns:
        raise KeyError(f"Required column '{haplogroup_column}' not found in dataset")
    
    haplogroup_failed_mask = df_age_clean[haplogroup_column].isna() | (df_age_clean[haplogroup_column].isin(['Unknown', 'Failed', '']))
    haplogroup_failed_count = haplogroup_failed_mask.sum()
    
    if haplogroup_failed_count > 0:
        logger.warning(f"Excluding {haplogroup_failed_count} samples with failed haplogroup assignment from haplogroup-specific analysis")
        logger.info("These samples are RETAINED for burden-only analysis (since age is present)")
    
    df_haplogroup_specific = df_age_clean[~haplogroup_failed_mask].copy()
    after_haplogroup_exclusion_count = len(df_haplogroup_specific)
    
    # Create exclusion report
    exclusion_report = {
        'initial_samples': initial_count,
        'samples_with_missing_age': int(age_missing_count),
        'samples_after_age_exclusion': int(after_age_exclusion_count),
        'samples_with_failed_haplogroup': int(haplogroup_failed_count),
        'samples_after_haplogroup_exclusion': int(after_haplogroup_exclusion_count),
        'samples_retained_for_burden_only': int(haplogroup_failed_count),
        'exclusion_reasons': {
            'missing_age': 'Excluded from ALL analyses',
            'failed_haplogroup': 'Excluded from haplogroup-specific analysis only; retained for burden-only'
        }
    }
    
    logger.info(f"Exclusion summary:")
    logger.info(f"  - Initial: {initial_count}")
    logger.info(f"  - After age exclusion: {after_age_exclusion_count} (removed {age_missing_count})")
    logger.info(f"  - After haplogroup exclusion: {after_haplogroup_specific_count} (removed {haplogroup_failed_count} from haplogroup-specific)")
    logger.info(f"  - Retained for burden-only: {haplogroup_failed_count}")
    
    return df_age_clean, df_haplogroup_specific, exclusion_report

def write_exclusion_report(exclusion_report, output_path):
    """Write exclusion report to log file."""
    with open(output_path, 'w') as f:
        f.write("=== MITOCHONDRIAL AGING CORRELATION - EXCLUSION REPORT ===\n\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n\n")
        f.write("EXCLUSION STATISTICS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Initial samples: {exclusion_report['initial_samples']}\n")
        f.write(f"Samples with missing age: {exclusion_report['samples_with_missing_age']}\n")
        f.write(f"Samples after age exclusion: {exclusion_report['samples_after_age_exclusion']}\n")
        f.write(f"Samples with failed haplogroup: {exclusion_report['samples_with_failed_haplogroup']}\n")
        f.write(f"Samples after haplogroup exclusion: {exclusion_report['samples_after_haplogroup_exclusion']}\n")
        f.write(f"Samples retained for burden-only analysis: {exclusion_report['samples_retained_for_burden_only']}\n\n")
        
        f.write("EXCLUSION RULES APPLIED:\n")
        f.write("-" * 40 + "\n")
        for reason, description in exclusion_report['exclusion_reasons'].items():
            f.write(f"- {reason}: {description}\n")
        
        f.write("\n=== END OF REPORT ===\n")

def main():
    """Main entry point for T019."""
    logger.info("Starting T019: Conditional Exclusion Logic")
    
    # Load processed dataset
    df = load_processed_dataset()
    
    # Apply exclusion logic
    df_age_clean, df_haplogroup_specific, exclusion_report = apply_exclusion_logic(df)
    
    # Write exclusion report
    paths = get_local_paths()
    exclusion_report_path = paths['exclusion_report']
    write_exclusion_report(exclusion_report, exclusion_report_path)
    
    # Save cleaned datasets for downstream tasks
    # Dataset for burden-only analysis (age present, haplogroup may be missing)
    burden_only_path = str(paths['processed_dataset'].parent / 'mito_aging_dataset_burden_only.csv')
    df_age_clean.to_csv(burden_only_path, index=False)
    logger.info(f"Saved burden-only dataset to {burden_only_path}")
    
    # Dataset for haplogroup-specific analysis (age present, haplogroup assigned)
    haplogroup_specific_path = str(paths['processed_dataset'].parent / 'mito_aging_dataset_haplogroup_specific.csv')
    df_haplogroup_specific.to_csv(haplogroup_specific_path, index=False)
    logger.info(f"Saved haplogroup-specific dataset to {haplogroup_specific_path}")
    
    logger.info("T019 completed successfully")
    return 0

if __name__ == '__main__':
    sys.exit(main())
