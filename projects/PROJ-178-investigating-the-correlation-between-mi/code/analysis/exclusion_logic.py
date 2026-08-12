import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def load_processed_dataset():
    """
    Load the merged dataset produced by T018.
    Expected path: code/data/processed/mito_aging_dataset.csv
    """
    paths = get_local_paths()
    input_path = paths["processed_data"] / "mito_aging_dataset.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {input_path}. "
            "Ensure T018 (merge_metadata) has completed successfully."
        )
    
    logger.info(f"Loading processed dataset from {input_path}")
    df = pd.read_csv(input_path)
    return df

def apply_exclusion_logic(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Apply conditional exclusion logic as per T019:
    1. Exclude samples with missing 'age' from ALL analysis.
    2. Exclude samples with failed haplogroup assignment (e.g., 'UNKNOWN' or NaN)
       from haplogroup-specific analysis ONLY, but RETAIN them for burden-only analysis
       if age is present.
    
    Returns:
        tuple: (full_analysis_df, haplogroup_analysis_df, exclusion_stats)
    """
    logger.info("Applying conditional exclusion logic")
    
    # Make copies to avoid modifying the original
    df_full = df.copy()
    df_haplo = df.copy()
    
    exclusion_stats = {
        "total_samples": len(df),
        "missing_age_count": 0,
        "missing_age_samples": [],
        "failed_haplogroup_count": 0,
        "failed_haplogroup_samples": [],
        "retained_for_burden_only": 0,
        "final_full_analysis_count": 0,
        "final_haplogroup_analysis_count": 0
    }
    
    # 1. Identify samples with missing age
    # Check for NaN, None, or string 'NaN'/'NA'/''
    age_mask = df_full['age'].isna() | (df_full['age'].astype(str).str.strip().isin(['', 'NaN', 'NA', 'nan']))
    missing_age_indices = df_full.index[age_mask].tolist()
    
    exclusion_stats["missing_age_count"] = len(missing_age_indices)
    exclusion_stats["missing_age_samples"] = missing_age_indices[:10]  # Log first 10 for brevity
    
    # Drop missing age from ALL analysis
    df_full = df_full[~age_mask]
    df_haplo = df_haplo[~age_mask]
    
    # 2. Identify samples with failed haplogroup assignment
    # Assuming 'haplogroup' column exists. Failed assignment might be NaN, 'UNKNOWN', or similar.
    if 'haplogroup' in df_haplo.columns:
        # Check for NaN or specific failure markers
        haplo_mask = (
            df_haplo['haplogroup'].isna() | 
            (df_haplo['haplogroup'].astype(str).str.strip().isin(['', 'NaN', 'NA', 'nan', 'UNKNOWN', 'unknown']))
        )
        failed_haplo_indices = df_haplo.index[haplo_mask].tolist()
        
        exclusion_stats["failed_haplogroup_count"] = len(failed_haplo_indices)
        exclusion_stats["failed_haplogroup_samples"] = failed_haplo_indices[:10]
        
        # Retain in df_full (burden-only analysis) - do nothing, it's already there
        # Exclude from df_haplo (haplogroup-specific analysis)
        df_haplo = df_haplo[~haplo_mask]
    else:
        logger.warning("Column 'haplogroup' not found in dataset. Skipping haplogroup exclusion.")
        failed_haplo_indices = []
    
    exclusion_stats["retained_for_burden_only"] = len(failed_haplo_indices)
    exclusion_stats["final_full_analysis_count"] = len(df_full)
    exclusion_stats["final_haplogroup_analysis_count"] = len(df_haplo)
    
    logger.info(f"Exclusion logic applied: {exclusion_stats['missing_age_count']} missing age, "
                f"{exclusion_stats['failed_haplogroup_count']} failed haplogroup")
    
    return df_full, df_haplo, exclusion_stats

def write_exclusion_report(stats: dict, output_path: Path):
    """
    Write the exclusion report to a text file.
    Format: Human-readable summary of exclusion counts and retention status.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=== Mitochondrial Aging Dataset Exclusion Report ===\n\n")
        f.write(f"Total samples processed: {stats['total_samples']}\n\n")
        
        f.write("--- Age Exclusion (All Analysis) ---\n")
        f.write(f"Samples excluded due to missing age: {stats['missing_age_count']}\n")
        if stats['missing_age_samples']:
            f.write(f"Sample IDs (first 10): {stats['missing_age_samples']}\n")
        f.write("\n")
        
        f.write("--- Haplogroup Exclusion (Haplogroup-Specific Analysis Only) ---\n")
        f.write(f"Samples excluded due to failed haplogroup assignment: {stats['failed_haplogroup_count']}\n")
        if stats['failed_haplogroup_samples']:
            f.write(f"Sample IDs (first 10): {stats['failed_haplogroup_samples']}\n")
        f.write(f"Samples retained for burden-only analysis: {stats['retained_for_burden_only']}\n")
        f.write("\n")
        
        f.write("--- Final Dataset Counts ---\n")
        f.write(f"Samples available for Full Analysis (Burden + Age): {stats['final_full_analysis_count']}\n")
        f.write(f"Samples available for Haplogroup-Specific Analysis: {stats['final_haplogroup_analysis_count']}\n")
    
    logger.info(f"Exclusion report written to {output_path}")

def main():
    """
    Main entry point for the exclusion logic task.
    Loads processed data, applies exclusion logic, and writes the report.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    paths = get_local_paths()
    exclusion_report_path = paths["logs"] / "exclusion_report.txt"
    
    try:
        df = load_processed_dataset()
        df_full, df_haplo, stats = apply_exclusion_logic(df)
        write_exclusion_report(stats, exclusion_report_path)
        
        # Optional: Save the filtered datasets for downstream tasks if needed
        # paths["processed_data"] / "mito_aging_dataset_full.csv"
        # paths["processed_data"] / "mito_aging_dataset_haplo.csv"
        
        logger.info("Exclusion logic task completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during exclusion logic: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()