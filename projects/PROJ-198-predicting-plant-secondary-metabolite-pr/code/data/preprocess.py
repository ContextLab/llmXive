"""
Data preprocessing utilities for the Plant Metabolite Prediction pipeline.

This module originally contained placeholder implementations for antiSMASH
execution and BGC‑to‑metabolite mapping.  The placeholders have been
replaced with real logic that delegates to :pymod:`code.data.antismash`,
while preserving the original public API required by downstream code.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import pandas as pd

from utils.logging import get_logger
from .antismash import (
    map_bgc_to_mibig,
    parse_antismash_json,
    run_antismash_wrapper,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# BGC → Metabolite class mapping (static, domain‑specific)
# ----------------------------------------------------------------------
_BGC_TO_METABOLITE_CLASS: Mapping[str, str] = {
    "polyketide": "polyketide",
    "nonribosomal_peptide": "NRP",
    "terpene": "terpene",
    "alkaloid": "alkaloid",
    "saccharide": "saccharide",
    # Additional mappings can be added as knowledge grows.
}

def map_bgc_to_metabolite(bgc_type: str) -> str:
    """
    Map a raw BGC type string to a metabolite class using a static lookup.
    Returns ``'unknown'`` when the type is not recognised.
    """
    if not isinstance(bgc_type, str):
        return "unknown"
    key = bgc_type.strip().lower()
    return _BGC_TO_METABOLITE_CLASS.get(key, "unknown")

def map_bgc_to_metabolite_dataframe(
    bgc_df: pd.DataFrame, metabolite_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge BGC features with metabolite records and add a ``mapped_class``
    column derived from the first BGC type column found in ``bgc_df``.
    """
    if bgc_df.empty or metabolite_df.empty:
        logger.warning("One of the input DataFrames is empty; returning empty result.")
        return pd.DataFrame()

    # Identify BGC type columns (all columns except species and total count)
    bgc_type_cols = [c for c in bgc_df.columns if c not in {"species", "total_bgc_count"}]

    # Determine the primary BGC type for each row (first non‑zero count)
    def primary_type(row: pd.Series) -> str:
        for col in bgc_type_cols:
            if row.get(col, 0) > 0:
                return col
        return "unknown"

    bgc_df["primary_bgc_type"] = bgc_df.apply(primary_type, axis=1)
    bgc_df["mapped_class"] = bgc_df["primary_bgc_type"].apply(map_bgc_to_metabolite)

    # Merge on species
    merged = pd.merge(
        bgc_df,
        metabolite_df,
        on="species",
        how="inner",
        suffixes=("_bgc", "_meta"),
    )
    return merged

# ----------------------------------------------------------------------
# antiSMASH wrapper – thin façade that forwards to the implementation in
# ``code.data.antismash``.  The original project used a placeholder named
# ``run_antiasmh_wrapper``; we keep that name for backward compatibility.
# ----------------------------------------------------------------------
def run_antiasmh_wrapper(
    genome_paths: Iterable[Path],
    species_mapping: Mapping[Path, str],
    confidence: float = 0.5,
) -> pd.DataFrame:
    """
    Backward‑compatible wrapper that forwards to :func:`run_antismash_wrapper`.

    Parameters
    ----------
    genome_paths: Iterable[Path]
        Paths to genome FASTA files.
    species_mapping: Mapping[Path, str]
        Mapping from each genome path to its species name.
    confidence: float, optional
        Minimum confidence score for BGC inclusion.

    Returns
    -------
    pd.DataFrame
        BGC count matrix as defined by ``run_antismash_wrapper``.
    """
    logger.debug(
        "run_antiasmh_wrapper called – delegating to run_antismash_wrapper"
    )
    return run_antismash_wrapper(genome_paths, species_mapping, confidence)

def run_antiSMASH_wrapper(
    genome_paths: Iterable[Path],
    species_mapping: Mapping[Path, str],
    confidence: float = 0.5,
) -> pd.DataFrame:
    """
    Public wrapper used by the pipeline (the name matches the original
    implementation).  It simply forwards to the corrected wrapper.
    """
    return run_antiasmh_wrapper(genome_paths, species_mapping, confidence)

# ----------------------------------------------------------------------
# Metabolite harmonisation – unchanged from the original implementation.
# ----------------------------------------------------------------------
def harmonize_metabolites(
    input_path: Path, output_path: Path
) -> pd.DataFrame:
    """
    Load a metabolite abundance table, add a pseudo‑count of 1,
    apply log‑transformation, and write the result.

    The input table must contain at least the columns:
    ``species``, ``abundance`` (numeric), and ``inchikey`` (or ``InChIKey``).

    Parameters
    ----------
    input_path: Path
        Path to the raw metabolite TSV/CSV file.
    output_path: Path
        Destination path for the harmonised CSV.

    Returns
    -------
    pd.DataFrame
        The processed DataFrame (also written to ``output_path``).
    """
    df = pd.read_csv(input_path, sep="\t")
    required_cols = {"species", "abundance"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Metabolite file missing required columns: {required_cols}")

    # Add pseudo‑count and log‑transform
    df["log_abundance"] = (df["abundance"] + 1).apply(lambda x: pd.np.log(x))
    # Preserve InChIKey column name (normalize to lower case)
    if "InChIKey" in df.columns:
        df.rename(columns={"InChIKey": "inchikey"}, inplace=True)

    # Write out
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Harmonised metabolite data written to {output_path}")
    return df

# ----------------------------------------------------------------------
# Module test harness – allows ``python -m code.data.preprocess`` to run a
# tiny demonstration using mock data (useful during development).
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Demonstrate preprocessing steps (antiSMASH wrapper & harmonisation)."
    )
    parser.add_argument(
        "--genome-dir",
        type=str,
        required=False,
        help="Directory containing genome FASTA files (one per species).",
    )
    parser.add_argument(
        "--species-list",
        type=str,
        nargs="+",
        required=False,
        help="List of species names matching the FASTA files (order matters).",
    )
    parser.add_argument(
        "--metabolite-file",
        type=str,
        required=False,
        help="Path to a metabolite TSV file to harmonise.",
    )
    args = parser.parse_args()

    if args.genome_dir and args.species_list:
        genome_dir = Path(args.genome_dir)
        fasta_paths = list(genome_dir.glob("*.fasta"))
        if len(fasta_paths) != len(args.species_list):
            logger.error("Number of FASTA files does not match number of species supplied.")
        else:
            mapping = {p: s for p, s in zip(fasta_paths, args.species_list)}
            bgc_df = run_antiSMASH_wrapper(fasta_paths, mapping)
            logger.info(f"BGC DataFrame shape: {bgc_df.shape}")

    if args.metabolite_file:
        out_path = Path("data/processed/harmonised_metabolites.csv")
        harmonize_metabolites(Path(args.metabolite_file), out_path)