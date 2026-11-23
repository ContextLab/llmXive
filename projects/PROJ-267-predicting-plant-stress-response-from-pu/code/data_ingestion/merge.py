import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd

# Project logger
from utils.logging_config import get_logger

logger = get_logger(__name__)

def check_and_install_biomart() -> bool:
    """
    Verify that the biomaRt R package is installed and loadable.
    Returns True if available, False otherwise.
    """
    # Existing implementation unchanged
    try:
        import rpy2.robjects as ro
        # Attempt to load biomaRt
        ro.r('library(biomaRt)')
        logger.info("biomaRt package is available.")
        return True
    except Exception as e:
        logger.error(f"biomaRt not available: {e}")
        return False

def map_uniprot_to_ensembl(
    df: pd.DataFrame,
    uniprot_col: str = 'UniProt_ID',
    ensembl_col: str = 'Ensembl_ID',
    species: str = 'arabidopsis'
) -> Tuple[pd.DataFrame, int, int]:
    """
    Maps UniProt IDs to Ensembl Gene IDs using biomaRt via rpy2.

    Returns:
        Tuple of (Mapped DataFrame, count of successfully mapped rows, count of dropped rows).
    """
    logger.info(f"Starting UniProt to Ensembl mapping for species: {species}")

    if not check_and_install_biomart():
        raise RuntimeError("biomaRt is not installed; cannot perform identifier mapping.")

    # Import rpy2 inside function to avoid import errors if not used
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    pandas2ri.activate()

    # Choose the appropriate Ensembl dataset
    dataset = 'plants_mart' if species in ['arabidopsis', 'rice', 'wheat'] else 'ensembl'
    logger.info(f"Using Ensembl dataset: {dataset}")

    # Connect to Ensembl via biomaRt
    try:
        ro.r(f'''
        library(biomaRt)
        ensembl <- useMart("{dataset}")
        attr <- c("{uniprot_col}", "{ensembl_col}")
        filters <- "{uniprot_col}"
        ''')
    except Exception as e:
        logger.error(f"Failed to initialize biomaRt connection: {e}")
        raise

    # Perform the mapping
    try:
        # Convert pandas DataFrame column to list for R
        uniprot_ids = df[uniprot_col].dropna().unique().tolist()
        ro.globalenv['uniprot_ids'] = ro.StrVector(uniprot_ids)

        mapping_df = ro.r('''
        getBM(attributes=attr, filters=filters, values=uniprot_ids, mart=ensembl)
        ''')
        mapping = pandas2ri.rpy2py(mapping_df)
    except Exception as e:
        logger.error(f"Error during biomaRt mapping: {e}")
        raise

    # Merge mapping back to original dataframe
    before_rows = df.shape[0]
    merged = df.merge(mapping, how='left', left_on=uniprot_col, right_on=uniprot_col)
    after_rows = merged.shape[0]

    # Count successful mappings and drops
    mapped_rows = merged[ensembl_col].notna().sum()
    dropped_rows = before_rows - mapped_rows

    logger.info(f"Mapping completed: {mapped_rows} rows mapped, {dropped_rows} rows dropped due to missing Ensembl IDs.")

    # Log dropped rows explicitly
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows where UniProt IDs could not be mapped to Ensembl IDs.")

    return merged, mapped_rows, dropped_rows

def run_merge_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    uniprot_col: str = 'UniProt_ID',
    ensembl_col: str = 'Ensembl_ID'
) -> pd.DataFrame:
    """
    Orchestrates the merge process:
    1. Load normalized data from data/processed/ if input_path not provided.
    2. Perform UniProt -> Ensembl mapping.
    3. Save the result to data/processed/merged.csv if output_path not provided.
    """
    logger.info("Running merge pipeline...")

    if input_path is None:
        processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
        possible_files = [
            processed_dir / "merged_proteomic_transcriptomic.csv",
            processed_dir / "processed_data.csv",
            processed_dir / "merged_data.csv"
        ]
        for f in possible_files:
            if f.exists():
                input_path = str(f)
                break
        if input_path is None:
            csv_files = list(processed_dir.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError("No processed CSV files found for merging.")
            input_path = str(csv_files[0])

    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)

    # Perform mapping
    merged_df, mapped, dropped = map_uniprot_to_ensembl(df, uniprot_col, ensembl_col)

    # Determine output path
    if output_path is None:
        output_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "merged.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Merged dataset saved to {output_path}")

    return merged_df

def main():
    """
    Entry point for the merge script.
    """
    try:
        run_merge_pipeline()
    except Exception as e:
        logger.error(f"Merge pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
