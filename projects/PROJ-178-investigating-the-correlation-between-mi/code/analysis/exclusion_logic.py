import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset(filepath: str) -> pd.DataFrame:
    """Load the processed dataset from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {filepath}")
    return pd.read_csv(path)

def apply_exclusion_logic(df: pd.DataFrame, min_haplogroup_rate: float = 0.90) -> tuple[pd.DataFrame, dict]:
    """
    Apply exclusion logic based on age and haplogroup assignment.
    
    Returns:
        tuple: (cleaned_df, exclusion_report)
    """
    report = {
        'total_samples': len(df),
        'missing_age': 0,
        'failed_haplogroup': 0,
        'excluded_for_age': 0,
        'excluded_for_haplogroup': 0,
        'retained_for_burden_only': 0
    }

    # 1. Exclude samples with missing age from ALL analysis
    initial_len = len(df)
    df_age_valid = df.dropna(subset=['age'])
    report['missing_age'] = initial_len - len(df_age_valid)
    report['excluded_for_age'] = report['missing_age']
    logger.info(f"Excluded {report['missing_age']} samples with missing age.")

    # 2. Exclude samples with failed haplogroup from haplogroup-specific analysis ONLY
    #    But RETAIN them for burden-only analysis if age is present.
    #    We will flag them in the dataframe rather than dropping them immediately.
    if 'haplogroup' in df_age_valid.columns:
        # Assume 'Unknown' or NaN indicates failure
        failed_mask = df_age_valid['haplogroup'].isna() | (df_age_valid['haplogroup'] == 'Unknown')
        report['failed_haplogroup'] = failed_mask.sum()
        
        # Create a flag for haplogroup-specific analysis
        df_age_valid['valid_for_haplogroup_analysis'] = ~failed_mask
        
        # Retain all for burden-only (since age is present)
        report['retained_for_burden_only'] = report['failed_haplogroup']
        logger.info(f"Flagged {report['failed_haplogroup']} samples with failed haplogroup (retained for burden analysis).")
    else:
        df_age_valid['valid_for_haplogroup_analysis'] = False
        logger.warning("No haplogroup column found. All samples excluded from haplogroup analysis.")

    return df_age_valid, report

def write_exclusion_report(report: dict, filepath: str):
    """Write the exclusion report to a text file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write("Exclusion Report\n")
        f.write("=" * 30 + "\n")
        for key, value in report.items():
            f.write(f"{key}: {value}\n")
    logger.info(f"Exclusion report written to {filepath}")

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    paths = get_local_paths()
    
    input_file = paths.get('processed_dataset', 'code/data/processed/mito_aging_dataset.csv')
    output_file = paths.get('cleaned_dataset', 'code/data/processed/mito_aging_dataset_clean.csv')
    report_file = 'code/logs/exclusion_report.txt'

    try:
        df = load_processed_dataset(input_file)
        df_clean, report = apply_exclusion_logic(df)
        
        # Save the cleaned dataset (with flags)
        df_clean.to_csv(output_file, index=False)
        logger.info(f"Cleaned dataset saved to {output_file}")
        
        # Write report
        write_exclusion_report(report, report_file)
        
    except Exception as e:
        logger.error(f"Error in exclusion logic: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
