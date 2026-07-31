import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Ensure imports match the API surface provided in the prompt
# The API surface lists: ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets, main

logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: Path) -> None:
    """Ensure the output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

def load_burden_data(burden_file_path: Path) -> pd.DataFrame:
    """
    Load the heteroplasmy burden data calculated in T015/T016.
    Expected columns: sample_id, burden_1pct, depth_category (or similar).
    """
    if not burden_file_path.exists():
        raise FileNotFoundError(f"Burden data file not found: {burden_file_path}")
    
    df = pd.read_csv(burden_file_path)
    logger.info(f"Loaded burden data: {len(df)} samples from {burden_file_path}")
    
    # Standardize column name for sample ID if necessary
    if 'sample_id' not in df.columns:
        if 'SampleID' in df.columns:
            df = df.rename(columns={'SampleID': 'sample_id'})
        else:
            # Fallback to first column if unnamed
            df = df.rename(columns={df.columns[0]: 'sample_id'})
    
    return df

def load_haplogroup_data(haplogroup_file_path: Path) -> pd.DataFrame:
    """
    Load the haplogroup assignments calculated in T017.
    Expected columns: sample_id, haplogroup.
    """
    if not haplogroup_file_path.exists():
        raise FileNotFoundError(f"Haplogroup data file not found: {haplogroup_file_path}")
    
    df = pd.read_csv(haplogroup_file_path)
    logger.info(f"Loaded haplogroup data: {len(df)} samples from {haplogroup_file_path}")
    
    # Standardize column name for sample ID if necessary
    if 'sample_id' not in df.columns:
        if 'SampleID' in df.columns:
            df = df.rename(columns={'SampleID': 'sample_id'})
        else:
            df = df.rename(columns={df.columns[0]: 'sample_id'})
    
    return df

def load_metadata_panel(metadata_file_path: Path) -> pd.DataFrame:
    """
    Load the 1000 Genomes metadata panel containing age, sex, population, and PCs.
    Expected columns: sample_id, age, sex, population, PC1, PC2 (and potentially others).
    """
    if not metadata_file_path.exists():
        raise FileNotFoundError(f"Metadata panel file not found: {metadata_file_path}")
    
    df = pd.read_csv(metadata_file_path)
    logger.info(f"Loaded metadata panel: {len(df)} samples from {metadata_file_path}")
    
    # Standardize column name for sample ID if necessary
    if 'sample_id' not in df.columns:
        if 'SampleID' in df.columns:
            df = df.rename(columns={'SampleID': 'sample_id'})
        elif 'SAMPLE' in df.columns:
            df = df.rename(columns={'SAMPLE': 'sample_id'})
        else:
            # Fallback to first column if unnamed
            df = df.rename(columns={df.columns[0]: 'sample_id'})
    
    return df

def merge_datasets(
    burden_df: pd.DataFrame,
    haplogroup_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Merge burden, haplogroups, and metadata into a single analysis-ready dataset.
    
    Performs an inner join to ensure only samples with complete data in all sources
    are included. Excludes samples with missing age or failed haplogroup assignment.
    
    Args:
        burden_df: DataFrame with sample_id and burden metrics.
        haplogroup_df: DataFrame with sample_id and haplogroup.
        metadata_df: DataFrame with sample_id, age, sex, population, PCs.
        output_path: Path to write the merged CSV.
    
    Returns:
        The merged DataFrame.
    """
    logger.info("Starting metadata merge...")
    
    # Initial merge: Burden + Haplogroup
    merged = pd.merge(
        burden_df,
        haplogroup_df,
        on='sample_id',
        how='inner'
    )
    logger.info(f"After merging burden and haplogroup: {len(merged)} samples")
    
    # Merge with metadata
    merged = pd.merge(
        merged,
        metadata_df,
        on='sample_id',
        how='inner'
    )
    logger.info(f"After merging with metadata: {len(merged)} samples")
    
    # Validation: Check for critical missing values
    # 1. Check for missing age
    missing_age = merged['age'].isna().sum()
    if missing_age > 0:
        logger.warning(f"Found {missing_age} samples with missing age. Excluding them.")
        merged = merged.dropna(subset=['age'])
    
    # 2. Check for missing/failed haplogroup
    # Assuming 'haplogroup' column exists; check for NaN or specific failure markers like 'UNK'
    if 'haplogroup' in merged.columns:
        missing_hg = merged['haplogroup'].isna().sum()
        failed_hg = (merged['haplogroup'] == 'UNK').sum() if 'UNK' in merged['haplogroup'].values else 0
        total_failed = missing_hg + failed_hg
        
        if total_failed > 0:
            logger.warning(f"Found {total_failed} samples with missing or failed haplogroup. Excluding them.")
            merged = merged[merged['haplogroup'].notna() & (merged['haplogroup'] != 'UNK')]
    
    # 3. Check for missing sex or population if required for downstream analysis
    # (Optional but good practice)
    for col in ['sex', 'population']:
        if col in merged.columns:
            missing_val = merged[col].isna().sum()
            if missing_val > 0:
                logger.warning(f"Found {missing_val} samples with missing {col}. Excluding them.")
                merged = merged.dropna(subset=[col])
    
    logger.info(f"Final merged dataset size: {len(merged)} samples")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    merged.to_csv(output_path, index=False)
    logger.info(f"Merged dataset written to: {output_path}")
    
    return merged

def main():
    """
    Main entry point for the metadata merge task (T018).
    Expects file paths to be configured in the environment or passed as arguments.
    For this implementation, we assume standard paths derived from the project structure.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths based on project conventions
    # These paths should ideally be read from config/environment.py if available,
    # but for this standalone task, we define them explicitly relative to the project root.
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Input files (produced by previous tasks)
    burden_file = project_root / "code" / "data" / "processed" / "burden_data.csv"
    haplogroup_file = project_root / "code" / "data" / "processed" / "haplogroup_assignments.csv"
    metadata_file = project_root / "code" / "data" / "processed" / "metadata_panel.csv"
    
    # Output file (as per tasks.md T020, though T018 is the merge step)
    output_file = project_root / "code" / "data" / "processed" / "mito_aging_dataset.csv"
    
    # Check if input files exist (simulating the flow)
    # In a real pipeline, we might check existence and fail loudly if missing.
    # For this task, we assume the previous steps (T012-T017) have produced these files.
    # If they don't exist, the load functions will raise FileNotFoundError.
    
    try:
        logger.info(f"Loading burden data from: {burden_file}")
        burden_df = load_burden_data(burden_file)
        
        logger.info(f"Loading haplogroup data from: {haplogroup_file}")
        haplogroup_df = load_haplogroup_data(haplogroup_file)
        
        logger.info(f"Loading metadata panel from: {metadata_file}")
        metadata_df = load_metadata_panel(metadata_file)
        
        # Perform the merge
        merged_df = merge_datasets(burden_df, haplogroup_df, metadata_df, output_file)
        
        logger.info("Metadata merge completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        logger.error("Ensure T012 (load_data), T015 (burden), T016 (depth), T017 (haplogroup) have run.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()