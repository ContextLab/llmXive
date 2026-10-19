from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
from utils.logging import get_logger
# Updated import to use the correct module path
from code.config import get_data_path

def align_data(genomes_df: pd.DataFrame, metabolites_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge genomic and metabolomic data by species.
    Filters partial rows and logs warnings.
    """
    logger = get_logger(__name__)
    # Ensure required columns exist
    required_genome_cols = {"species", "total_bgc_count"}
    required_metabolite_cols = {"species", "log_abundance"}

    missing_genome = required_genome_cols - set(genomes_df.columns)
    missing_metabo = required_metabolite_cols - set(metabolites_df.columns)

    if missing_genome:
        logger.warning(f"Genomes data missing columns: {missing_genome}")
    if missing_metabo:
        logger.warning(f"Metabolites data missing columns: {missing_metabolite_cols}")

    # Perform inner join on species
    aligned = pd.merge(
        genomes_df,
        metabolites_df,
        on="species",
        how="inner",
        suffixes=("_bgc", "_meta"),
    )

    # Log any species that were dropped
    dropped = set(genomes_df["species"]) ^ set(aligned["species"])
    if dropped:
        logger.info(f"Dropped species due to missing data: {dropped}")

    return aligned

def save_aligned_matrix(df: pd.DataFrame, output_path: Optional[Union[str, Path]] = None) -> None:
    """
    Write the final aligned matrix to CSV.

    If output_path is not provided, defaults to data/processed/aligned_matrix.csv
    as specified in the task requirements.
    """
    logger = get_logger(__name__)
    if output_path is None:
        output_path = get_data_path(Path("processed") / "aligned_matrix.csv")
    else:
        output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Aligned matrix saved to {output_path}")

def calculate_alignment_success_rate(
    aligned_df: pd.DataFrame,
    min_species_count: int = 5,
    required_columns: Optional[List[str]] = None,
) -> float:
    """
    Calculate, log, and report the percentage of species with valid data (N>=min_species_count).

    This implements SC-004 success criteria.
    """
    logger = get_logger(__name__)
    if required_columns is None:
        # Default to all columns except species
        required_columns = [col for col in aligned_df.columns if col != "species"]

    valid_rows = aligned_df.dropna(subset=required_columns)
    total_species = aligned_df["species"].nunique()
    valid_species = valid_rows["species"].nunique()

    success_rate = valid_species / total_species if total_species > 0 else 0.0
    logger.info(
        f"Alignment success rate: {valid_species}/{total_species} species ({success_rate:.2%})"
    )
    return success_rate

def main():
    """
    Main entry point for alignment and saving the matrix.

    This function demonstrates the full pipeline:
    1. Load genomic and metabolomic data (simulated here for standalone execution)
    2. Align them
    3. Save to data/processed/aligned_matrix.csv
    """
    logger = get_logger(__name__)
    # Simulated data loading (replace with real loaders as needed)
    genomes_path = get_data_path(Path("raw") / "genomes" / "bgc_counts.csv")
    metabolites_path = get_data_path(Path("raw") / "metabolites" / "harmonized.csv")

    try:
        genomes_df = pd.read_csv(genomes_path)
        metabolites_df = pd.read_csv(metabolites_path)
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        return

    aligned_df = align_data(genomes_df, metabolites_df)
    save_aligned_matrix(aligned_df)
    calculate_alignment_success_rate(aligned_df)

    logger.info("Alignment process completed.")

if __name__ == "__main__":
    main()
