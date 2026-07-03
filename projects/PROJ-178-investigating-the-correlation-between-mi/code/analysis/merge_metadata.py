"""
Implementation of T018: Metadata merge logic for US1.
Joins heteroplasmy burden, haplogroups, age, sex, population, and PCs.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Ensure imports align with existing API surface if needed,
# though this is a standalone module for the merge step.
# We rely on standard libraries and pandas.

logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: Path) -> None:
    """Ensure the output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)

def load_burden_data(burden_path: Path) -> pd.DataFrame:
    """Load heteroplasmy burden and depth-stratified burden data."""
    if not burden_path.exists():
        raise FileNotFoundError(f"Burden data file not found: {burden_path}")
    df = pd.read_csv(burden_path)
    logger.info(f"Loaded burden data with {len(df)} samples from {burden_path}")
    return df

def load_haplogroup_data(haplogroup_path: Path) -> pd.DataFrame:
    """Load haplogroup assignments."""
    if not haplogroup_path.exists():
        raise FileNotFoundError(f"Haplogroup data file not found: {haplogroup_path}")
    df = pd.read_csv(haplogroup_path)
    logger.info(f"Loaded haplogroup data with {len(df)} samples from {haplogroup_path}")
    return df

def load_metadata_panel(metadata_path: Path) -> pd.DataFrame:
    """Load age, sex, population, and PCs from the metadata panel."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata panel not found: {metadata_path}")
    df = pd.read_csv(metadata_path)
    logger.info(f"Loaded metadata panel with {len(df)} samples from {metadata_path}")
    return df

def merge_datasets(
    burden_df: pd.DataFrame,
    haplogroup_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    sample_id_col: str = "SAMPLE_ID"
) -> pd.DataFrame:
    """
    Join burden, haplogroups, and metadata on the sample ID column.
    Returns the merged DataFrame.
    """
    # Standardize column names if necessary (assuming consistent naming from previous steps)
    # Expected columns in burden_df: SAMPLE_ID, total_burden, low_depth_burden, med_depth_burden, high_depth_burden
    # Expected columns in haplogroup_df: SAMPLE_ID, haplogroup
    # Expected columns in metadata_df: SAMPLE_ID, AGE, SEX, POPULATION, PC1, PC2, ...

    # Merge burden and haplogroup
    merged = pd.merge(burden_df, haplogroup_df, on=sample_id_col, how="inner")
    logger.info(f"After merging burden and haplogroups: {len(merged)} samples")

    # Merge with metadata
    merged = pd.merge(merged, metadata_df, on=sample_id_col, how="inner")
    logger.info(f"After merging with metadata: {len(merged)} samples")

    return merged

def main():
    """
    Main entry point to execute the metadata merge.
    Expects data files in code/data/processed/ as per project structure.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Define paths based on project conventions
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    ensure_dirs(processed_dir)

    # Input files (produced by T015, T016, T017)
    burden_file = processed_dir / "heteroplasmy_burden.csv"
    haplogroup_file = processed_dir / "haplogroups.csv"
    metadata_file = processed_dir / "metadata_panel.csv"

    # Output file
    output_file = processed_dir / "mito_aging_dataset_merged.csv"

    try:
        logger.info("Starting metadata merge process...")

        # Load data
        burden_df = load_burden_data(burden_file)
        haplogroup_df = load_haplogroup_data(haplogroup_file)
        metadata_df = load_metadata_panel(metadata_file)

        # Perform merge
        final_df = merge_datasets(burden_df, haplogroup_df, metadata_df)

        # Save result
        final_df.to_csv(output_file, index=False)
        logger.info(f"Successfully merged and saved dataset to {output_file}")
        logger.info(f"Final dataset shape: {final_df.shape}")
        logger.info(f"Columns: {list(final_df.columns)}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during merge process: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())