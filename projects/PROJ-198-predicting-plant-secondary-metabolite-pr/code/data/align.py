"""
Data alignment utilities.
Provides functions to merge BGC feature tables with metabolite abundance tables,
write the aligned matrix to disk, compute alignment success statistics,
and enforce a minimum success rate threshold.
"""

from pathlib import Path
from typing import List, Optional, Union, Tuple

import json
import pandas as pd

from utils.logging import get_logger
from code.config import get_data_path
from utils.artifact import track_path  # <-- new import for artifact hygiene


def align_data(
    genomes_df: pd.DataFrame,
    metabolites_df: pd.DataFrame,
    species_list: Optional[List[dict]] = None,
) -> Tuple[pd.DataFrame, float]:
    """
    Merge genomic (BGC) and metabolomic data by species.

    Parameters
    ----------
    genomes_df : pd.DataFrame
        DataFrame containing BGC feature columns. Must include a ``species`` column.
    metabolites_df : pd.DataFrame
        DataFrame containing metabolite columns. Must include a ``species`` column.
    species_list : list of dict, optional
        Optional list of species dictionaries (as used throughout the project).
        If provided, the function will ensure that only those species are considered.

    Returns
    -------
    aligned_df : pd.DataFrame
        The merged DataFrame.
    success_rate : float
        Alignment success rate (see :func:`calculate_alignment_success_rate`).
    """
    logger = get_logger(__name__)

    # Verify required columns
    required_genome_cols = {"species", "total_bgc_count"}
    required_metabo_cols = {"species", "log_abundance"}

    missing_genome = required_genome_cols - set(genomes_df.columns)
    missing_metabo = required_metabo_cols - set(metabolites_df.columns)

    if missing_genome:
        logger.warning(f"Genomes data missing columns: {missing_genome}")
    if missing_metabo:
        logger.warning(f"Metabolites data missing columns: {required_metabo_cols}")

    # If a species list is supplied, restrict to those species
    if species_list is not None:
        allowed = {sp["name"] for sp in species_list}
        genomes_df = genomes_df[genomes_df["species"].isin(allowed)]
        metabolites_df = metabolites_df[metabolites_df["species"].isin(allowed)]

    # Inner join on species
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

    # Compute success rate
    success_rate = calculate_alignment_success_rate(aligned)

    return aligned, success_rate


def save_aligned_matrix(
    df: pd.DataFrame, output_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Write the aligned matrix to CSV and generate alignment statistics.

    If *output_path* is ``None`` the matrix is written to
    ``data/processed/aligned_matrix.csv``.
    """
    logger = get_logger(__name__)
    if output_path is None:
        output_path = get_data_path(Path("processed") / "aligned_matrix.csv")
    else:
        output_path = Path(output_path)

    # Ensure parent directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the aligned matrix
    df.to_csv(output_path, index=False)
    logger.info(f"Aligned matrix saved to {output_path}")

    # Register the matrix artifact
    track_path(output_path)

    # ------------------------------------------------------------------
    # Alignment statistics generation
    # ------------------------------------------------------------------
    success_rate = calculate_alignment_success_rate(df)

    stats = {
        "success_rate": success_rate,
        "total_species": int(df["species"].nunique()),
        "valid_species": int(
            df.dropna(
                subset=[
                    c for c in df.columns if c != "species"
                ]
            )["species"].nunique()
        ),
    }

    stats_path = get_data_path(Path("processed") / "alignment_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    logger.info(f"Alignment statistics saved to {stats_path}")

    # Register the statistics artifact
    track_path(stats_path)

    # Enforce the success‑rate threshold (≥ 80 %)
    if success_rate < 0.8:
        raise AssertionError(
            f"Alignment success rate {success_rate:.2%} is below the required 80 % threshold."
        )


def calculate_alignment_success_rate(
    aligned_df: pd.DataFrame,
    min_species_count: int = 5,
    required_columns: Optional[List[str]] = None,
) -> float:
    """
    Calculate the percentage of species with complete data.

    Parameters
    ----------
    aligned_df : pd.DataFrame
        The aligned DataFrame.
    min_species_count : int, default 5
        Minimum number of species required for a valid alignment.
    required_columns : list of str, optional
        Columns that must be non‑null for a species to be counted as valid.
        If ``None`` all columns except ``species`` are required.

    Returns
    -------
    float
        Success rate as a fraction (0‑1).
    """
    logger = get_logger(__name__)
    if required_columns is None:
        required_columns = [c for c in aligned_df.columns if c != "species"]

    valid_rows = aligned_df.dropna(subset=required_columns)
    total_species = aligned_df["species"].nunique()
    valid_species = valid_rows["species"].nunique()

    success_rate = valid_species / total_species if total_species > 0 else 0.0
    logger.info(
        f"Alignment success rate: {valid_species}/{total_species} species ({success_rate:.2%})"
    )
    return success_rate


def main() -> None:
    """
    Demonstration entry point – loads mock data, aligns, saves, and reports success.
    """
    logger = get_logger(__name__)
    # Load mock data files (used when CI_MODE=1)
    genomes_path = get_data_path(Path("raw") / "mock_bgc_counts.csv")
    metabolites_path = get_data_path(Path("raw") / "mock_metabolite_abundance.csv")

    try:
        genomes_df = pd.read_csv(genomes_path)
        metabolites_df = pd.read_csv(metabolites_path)
    except FileNotFoundError as e:
        logger.error(f"Mock data not found: {e}")
        return

    aligned_df, success = align_data(genomes_df, metabolites_df)
    save_aligned_matrix(aligned_df)
    logger.info(f"Alignment completed with success rate {success:.2%}")

if __name__ == "__main__":
    main()
