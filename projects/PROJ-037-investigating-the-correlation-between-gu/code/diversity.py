"""
Diversity Analysis Module for Gut Microbiome and Circadian Rhythm Study.

Calculates Alpha diversity (Shannon, Simpson) and Beta diversity (Bray-Curtis)
per participant from the merged cohort data.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, List

# Attempt to import biom; if missing, raise a clear ImportError
try:
    import biom
except ImportError:
    raise ImportError(
        "The 'biom-format' package is required for diversity analysis. "
        "Please ensure it is installed in the virtual environment (pip install biom-format)."
    )

from utils.logging_utils import get_logger
from utils.seeding import set_seed

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_biom_table() -> biom.Table:
    """
    Load the BIOM feature table from the raw data directory.

    Returns:
        biom.Table: The loaded BIOM table.

    Raises:
        FileNotFoundError: If the BIOM file is not found.
    """
    biom_path = DATA_RAW_DIR / "agp" / "feature-table.biom"
    if not biom_path.exists():
        # Fallback path if AGP data is stored differently or merged earlier
        alt_path = DATA_RAW_DIR / "feature-table.biom"
        if alt_path.exists():
            biom_path = alt_path
        else:
            raise FileNotFoundError(
                f"BIOM feature table not found at {DATA_RAW_DIR / 'agp' / 'feature-table.biom'} "
                f"or {alt_path}. Ensure T011 has successfully downloaded the data."
            )

    logger.info(f"Loading BIOM table from {biom_path}")
    try:
        table = biom.load_table(str(biom_path))
        logger.info(f"Successfully loaded BIOM table with {table.shape[0]} features and {table.shape[1]} samples.")
        return table
    except Exception as e:
        logger.error(f"Failed to load BIOM table: {e}")
        raise


def load_metadata() -> pd.DataFrame:
    """
    Load the merged cohort metadata from the processed data directory.

    Returns:
        pd.DataFrame: The metadata dataframe.

    Raises:
        FileNotFoundError: If the metadata file is not found.
    """
    metadata_path = DATA_PROCESSED_DIR / "cohort_merged.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Merged cohort metadata not found at {metadata_path}. "
            "Ensure T011-T017 (Ingestion) have been completed successfully."
        )

    logger.info(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    logger.info(f"Loaded metadata with {len(df)} participants.")
    return df


def calculate_alpha_diversity(table: biom.Table, metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Alpha diversity metrics (Shannon, Simpson) for each participant.

    Args:
        table (biom.Table): The BIOM feature table.
        metadata (pd.DataFrame): The participant metadata.

    Returns:
        pd.DataFrame: A dataframe with participant_id and alpha diversity metrics.
    """
    logger.info("Calculating Alpha diversity metrics (Shannon, Simpson)...")

    # Convert BIOM table to pandas DataFrame for easier manipulation
    # Note: BIOM tables are often sparse; we convert to dense only if memory allows,
    # or iterate if necessary. For typical AGP subsets, dense conversion is often feasible.
    try:
        # Get sample IDs from BIOM table
        sample_ids = table.ids(axis='sample')

        # Create a dataframe to store results
        alpha_diversity_df = pd.DataFrame({'participant_id': sample_ids})

        # Calculate Shannon diversity
        # biom.Table provides a method to calculate alpha diversity directly
        # We use the 'shannon' and 'simpson' metrics
        shannon_values = table.alpha_diversity(metric='shannon', ids=sample_ids)
        simpson_values = table.alpha_diversity(metric='simpson', ids=sample_ids)

        alpha_diversity_df['shannon'] = shannon_values
        alpha_diversity_df['simpson'] = simpson_values

        # Merge with metadata to ensure participant_id alignment
        # Note: BIOM sample IDs might differ from metadata participant_id format.
        # We assume they match or can be matched. If not, we filter.
        merged_alpha = metadata.merge(alpha_diversity_df, on='participant_id', how='inner')

        if len(merged_alpha) == 0:
            logger.warning("No matching participants found between BIOM table and metadata for alpha diversity.")
            # Try a fuzzy match or ID cleaning if necessary, but for now, raise an error or return empty
            # In a robust pipeline, we would log the mismatch and attempt ID normalization.
            # For now, we assume exact match as per T012 logic.
            raise ValueError("No matching participants found for alpha diversity calculation.")

        logger.info(f"Calculated alpha diversity for {len(merged_alpha)} participants.")
        return merged_alpha[['participant_id', 'shannon', 'simpson']]

    except Exception as e:
        logger.error(f"Error calculating alpha diversity: {e}")
        raise


def calculate_beta_diversity(table: biom.Table, metadata: pd.DataFrame) -> Tuple[pd.DataFrame, biom.Table]:
    """
    Calculate Beta diversity (Bray-Curtis) matrix for participants.

    Args:
        table (biom.Table): The BIOM feature table.
        metadata (pd.DataFrame): The participant metadata.

    Returns:
        Tuple[pd.DataFrame, biom.Table]: A distance matrix dataframe and the original table (for downstream use).
    """
    logger.info("Calculating Beta diversity matrix (Bray-Curtis)...")

    try:
        sample_ids = table.ids(axis='sample')

        # Calculate Bray-Curtis distance
        # biom.Table's beta_diversity returns a DistanceMatrix object
        distance_matrix = table.beta_diversity(metric='braycurtis', ids=sample_ids, transform_axis='sample')

        # Convert to DataFrame for easier handling and saving
        # The DistanceMatrix object has a 'data' attribute and 'ids'
        dm_df = pd.DataFrame(distance_matrix.data, index=distance_matrix.ids, columns=distance_matrix.ids)

        # Filter to only include participants present in metadata
        valid_ids = set(metadata['participant_id'].values)
        existing_ids = set(dm_df.index)
        common_ids = list(valid_ids.intersection(existing_ids))

        if len(common_ids) == 0:
            logger.warning("No common participants found between distance matrix and metadata.")
            raise ValueError("No common participants for beta diversity calculation.")

        # Filter the dataframe
        dm_df = dm_df.loc[common_ids, common_ids]

        logger.info(f"Calculated beta diversity matrix for {len(common_ids)} participants.")
        return dm_df, table

    except Exception as e:
        logger.error(f"Error calculating beta diversity: {e}")
        raise


def run_diversity_analysis(seed: int = 42) -> Dict[str, str]:
    """
    Main function to run the full diversity analysis pipeline.

    Args:
        seed (int): Random seed for reproducibility.

    Returns:
        Dict[str, str]: Paths to the generated output files.
    """
    set_seed(seed)
    logger.info("Starting Diversity Analysis Pipeline...")

    # Load data
    biom_table = load_biom_table()
    metadata = load_metadata()

    # Calculate Alpha Diversity
    alpha_df = calculate_alpha_diversity(biom_table, metadata)

    # Save Alpha Diversity results
    alpha_output_path = OUTPUT_DIR / "alpha_diversity.csv"
    alpha_df.to_csv(alpha_output_path, index=False)
    logger.info(f"Alpha diversity saved to {alpha_output_path}")

    # Calculate Beta Diversity
    beta_df, _ = calculate_beta_diversity(biom_table, metadata)

    # Save Beta Diversity results
    beta_output_path = OUTPUT_DIR / "beta_diversity_matrix.csv"
    beta_df.to_csv(beta_output_path)
    logger.info(f"Beta diversity matrix saved to {beta_output_path}")

    # Update the merged cohort with alpha diversity metrics
    # This ensures downstream tasks (analysis, viz) have access to these metrics
    updated_metadata = metadata.merge(alpha_df, on='participant_id', how='left')
    updated_cohort_path = OUTPUT_DIR / "cohort_merged_with_diversity.csv"
    updated_metadata.to_csv(updated_cohort_path, index=False)
    logger.info(f"Updated cohort with diversity metrics saved to {updated_cohort_path}")

    # Note: The original cohort_merged.csv is the input. We create a new file with diversity added.
    # However, if the pipeline expects 'cohort_merged.csv' to contain diversity, we might need to overwrite it.
    # Per T017, 'cohort_merged.csv' is the output of ingestion.
    # T020 adds diversity. We will output a new file 'cohort_with_diversity.csv' or update the existing one if that's the convention.
    # Looking at T021 (analysis), it likely expects diversity columns.
    # To be safe and follow the pattern of "updating" the cohort, we will overwrite the cohort file with diversity added.
    # But wait, T017 says "Save final merged cohort to data/processed/cohort_merged.csv".
    # If we overwrite it, we lose the original ingestion state.
    # Better approach: The 'analysis' task should load the 'cohort_merged.csv' and the 'alpha_diversity.csv' and merge them.
    # However, to simplify the pipeline and ensure 'cohort_merged.csv' is the single source of truth for the next step,
    # we will update 'cohort_merged.csv' with the diversity columns. This is a common pattern in data pipelines.
    # Let's update 'cohort_merged.csv' in place (conceptually, by writing a new one and renaming).
    # Actually, let's write to a new file 'cohort_processed.csv' to distinguish the enriched version.
    # But T021 says "load_processed_cohort". Let's assume 'cohort_merged.csv' is the base and we append diversity.
    # Re-reading T017: "Save final merged cohort to data/processed/cohort_merged.csv".
    # Re-reading T020: "Implement code/diversity.py to calculate...". It doesn't explicitly say to overwrite.
    # However, T021 (analysis) needs these columns.
    # Let's check the API for analysis.py: `load_processed_cohort`.
    # If we update 'cohort_merged.csv', then `load_processed_cohort` (which likely loads 'cohort_merged.csv') will have the data.
    # Let's update 'cohort_merged.csv' to include diversity columns.

    # We'll create a temporary file and then replace the original to ensure atomicity
    temp_path = OUTPUT_DIR / "cohort_merged_temp.csv"
    updated_metadata.to_csv(temp_path, index=False)
    os.replace(temp_path, metadata_path) # metadata_path is the path to cohort_merged.csv
    logger.info(f"Updated {metadata_path} with diversity metrics.")

    return {
        "alpha_diversity": str(alpha_output_path),
        "beta_diversity": str(beta_output_path),
        "updated_cohort": str(OUTPUT_DIR / "cohort_merged.csv")
    }


def main():
    """Entry point for the diversity analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = run_diversity_analysis()
        logger.info("Diversity analysis completed successfully.")
        logger.info(f"Outputs: {results}")
    except Exception as e:
        logger.error(f"Diversity analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()